import sublime
import re

from ..constants import PLUGIN_NAME

class ClaudetteChatView:
    _instance = None

    @classmethod
    def get_instance(cls, window=None, settings=None):
        if cls._instance is None:
            if window is None or settings is None:
                raise ValueError("Window and settings are required for initial creation")
            cls._instance = cls(window, settings)
        return cls._instance

    def __init__(self, window, settings):
        if ClaudetteChatView._instance is not None:
            raise Exception("This class is a singleton!")
        self.window = window
        self.settings = settings
        self.view = None
        self.phantom_set = None
        self.existing_button_positions = set()
        ClaudetteChatView._instance = self

    def create_or_get_view(self):
        """
        Creates a new chat view or returns existing one.

        Returns:
            sublime.View or None: The chat view object or None if creation fails.
        """
        try:
            # Check for existing chat view
            for view in self.window.views():
                if view.name() == "Claude Chat":
                    self.view = view
                    return self.view

            # Create new chat view if none exists
            self.view = self.window.new_file()
            if not self.view:
                print(f"{PLUGIN_NAME} Error: Could not create new file")
                sublime.error_message(f"{PLUGIN_NAME} Error: Could not create new file")
                return None

            # Configure chat view settings
            chat_settings = self.settings.get('chat', {})
            show_line_numbers = chat_settings.get('line_numbers', False)

            self.view.set_name("Claude Chat")
            self.view.set_scratch(True)
            self.view.assign_syntax('Packages/Markdown/Markdown.sublime-syntax')
            self.view.set_read_only(True)
            self.view.settings().set("line_numbers", show_line_numbers)

            return self.view

        except Exception as e:
            print(f"{PLUGIN_NAME} Error creating chat panel: {str(e)}")
            sublime.error_message(f"{PLUGIN_NAME} Error: Could not create chat panel")
            return None

    def append_text(self, text, scroll_to_end=True):
        """
        Appends text to the chat view.

        Args:
            text (str): Text to append
            scroll_to_end (bool): Whether to scroll to end after appending
        """
        if not self.view:
            return

        self.view.set_read_only(False)
        self.view.run_command('append', {
            'characters': text,
            'force': True,
            'scroll_to_end': scroll_to_end
        })
        self.view.set_read_only(True)

    def focus(self):
        """Focuses the chat view."""
        if self.view and self.view.window():
            self.view.window().focus_view(self.view)

    def get_size(self):
        """Returns the size of the chat view content."""
        return self.view.size() if self.view else 0

    def clear(self):
        """Clears the chat view content and buttons."""
        if self.view:
            self.view.set_read_only(False)
            self.view.run_command('select_all')
            self.view.run_command('right_delete')
            self.view.set_read_only(True)
            self.clear_buttons()

    def clear_buttons(self):
        """Clears all existing copy buttons."""
        if self.phantom_set:
            self.phantom_set.update([])
        self.existing_button_positions.clear()

    def on_streaming_complete(self):
        if not self.view:
            return

        # First validate and fix any unclosed code blocks
        self.validate_and_fix_code_blocks()

        if not self.phantom_set:
            self.phantom_set = sublime.PhantomSet(self.view, "code_block_buttons")

        content = self.view.substr(sublime.Region(0, self.view.size()))

        # Updated regex pattern to better handle code blocks
        pattern = r"```[\w+]*\n(.*?)\n```"
        code_blocks = []
        for match in re.finditer(pattern, content, re.DOTALL):
            code_block = match.group(1).strip()
            end_pos = match.end()
            code_blocks.append((code_block, end_pos))

        phantoms = []
        new_positions = set()

        # First, collect all existing phantoms that are still valid
        if self.phantom_set:
            existing_phantoms = self.phantom_set.phantoms
            for phantom in existing_phantoms:
                phantoms.append(phantom)
                new_positions.add(phantom.region.end())

        # Then add new phantoms for new code blocks
        for code_block, end_pos in code_blocks:
            if end_pos not in new_positions:  # Only add if not already exists
                region = sublime.Region(end_pos, end_pos)
                escaped_code = (code_block
                              .replace('&', '&amp;')
                              .replace('"', '&quot;')
                              .replace('<', '&lt;')
                              .replace('>', '&gt;'))

                button_html = f'''
                    <a class="copy-button" href="copy:{escaped_code}">Copy</a>
                '''

                phantom = sublime.Phantom(
                    region,
                    button_html,
                    sublime.LAYOUT_BLOCK,
                    lambda href, code=code_block: self.handle_copy(code)
                )
                phantoms.append(phantom)
                new_positions.add(end_pos)

        self.existing_button_positions = new_positions
        if phantoms:
            self.phantom_set.update(phantoms)

    def handle_copy(self, code):
        """
        Copies code to clipboard when button is clicked.
        Shows a status message to confirm the copy action.
        """
        try:
            sublime.set_clipboard(code)
            sublime.status_message("Code copied to clipboard")
        except Exception as e:
            print(f"{PLUGIN_NAME} Error copying to clipboard: {str(e)}")
            sublime.status_message("Error copying code to clipboard")

    def destroy(self):
        """Cleanup method to be called when the view is being destroyed."""
        if self.phantom_set:
            self.phantom_set.update([])  # Clear all phantoms
        self.existing_button_positions.clear()
        self.view = None
        ClaudetteChatView._instance = None

    def validate_and_fix_code_blocks(self):
        """
        Validates and fixes unclosed code blocks in the view content.
        """
        if not self.view:
            return

        # Get full content
        content = self.view.substr(sublime.Region(0, self.view.size()))
        lines = content.split('\n')
        open_blocks = 0

        # Count opening and closing code blocks
        for line in lines:
            if line.strip().startswith('```'):
                if line.strip() == '```':
                    open_blocks -= 1
                else:
                    open_blocks += 1

        # Add closing blocks if needed
        if open_blocks > 0:
            self.view.set_read_only(False)
            self.view.run_command('append', {
                'characters': '\n' + '```' * open_blocks,
                'force': True,
                'scroll_to_end': True
            })
            self.view.set_read_only(True)
