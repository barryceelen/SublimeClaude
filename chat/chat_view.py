import sublime
import re

from ..constants import PLUGIN_NAME

class ClaudetteChatView:
    def __init__(self, window, settings):
        self.window = window
        self.settings = settings
        self.view = None
        self.phantom_set = None
        self.existing_button_positions = set()

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

    def on_streaming_complete(self):
        """
        Handles completion of streaming by finding code blocks and adding copy buttons.
        Only adds buttons where they don't already exist.
        """
        if not self.view:
            return

        # Create phantom set if it doesn't exist
        if not self.phantom_set:
            self.phantom_set = sublime.PhantomSet(self.view, "code_block_buttons")

        # Get entire content
        content = self.view.substr(sublime.Region(0, self.view.size()))

        # Find all code blocks using regex
        code_blocks = []
        pattern = r"```[\w]*\n(.*?)```\n"
        for match in re.finditer(pattern, content, re.DOTALL):
            code_block = match.group(1).strip()
            end_pos = match.end() - 1
            code_blocks.append((code_block, end_pos))

        # Create phantoms for copy buttons
        phantoms = []
        new_positions = set()

        for code_block, end_pos in code_blocks:
            # Check if button already exists at this position
            if end_pos not in self.existing_button_positions:
                # Escape any HTML special characters in the code block
                escaped_code = code_block.replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')

                button_html = f'''
                    <body><a class="claudette-button" href="copy:{escaped_code}">Copy</a></body>
                '''

                phantom = sublime.Phantom(
                    sublime.Region(end_pos, end_pos),
                    button_html,
                    sublime.LAYOUT_BLOCK,
                    lambda href, code=code_block: self.handle_copy(code)
                )
                phantoms.append(phantom)
                new_positions.add(end_pos)

        # Update tracked positions
        self.existing_button_positions = new_positions

        # Update phantom set with all phantoms
        self.phantom_set.update(phantoms)

    def clear_buttons(self):
        """
        Clears all existing copy buttons.
        """
        if self.phantom_set:
            self.phantom_set.update([])
        self.existing_button_positions.clear()

    def handle_copy(self, code):
        """Copies code to clipboard when button is clicked."""
        sublime.set_clipboard(code)
        sublime.status_message("Code copied to clipboard!")
