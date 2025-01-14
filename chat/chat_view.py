import sublime
import re
from typing import List, Tuple, Set
from dataclasses import dataclass

from ..constants import PLUGIN_NAME

@dataclass
class CodeBlock:
    content: str
    start_pos: int
    end_pos: int
    language: str

class ClaudetteChatView:
    _instances = {}  # Store one instance per window

    @classmethod
    def get_instance(cls, window=None, settings=None):
        if window is None:
            raise ValueError("Window is required")

        window_id = window.id()

        if window_id not in cls._instances:
            if settings is None:
                raise ValueError("Settings are required for initial creation")
            cls._instances[window_id] = cls(window, settings)

        return cls._instances[window_id]

    def __init__(self, window, settings):
        self.window = window
        self.settings = settings
        self.view = None
        self.phantom_set = None
        self.existing_button_positions = set()

    def create_or_get_view(self):
        """
        Creates a new chat view or returns existing one.
        """
        try:
            # First check for current chat view in this window
            for view in self.window.views():
                if (view.settings().get('claudette_is_chat_view', False) and
                    view.settings().get('claudette_is_current_chat', False)):
                    self.view = view
                    return self.view

            # If no current chat view found, use the first chat view
            for view in self.window.views():
                if view.settings().get('claudette_is_chat_view', False):
                    self.view = view
                    # Set this view as current since none was marked as current
                    view.settings().set('claudette_is_current_chat', True)
                    return self.view

            # Create new chat view if none exists in this window
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
            self.view.settings().set("claudette_is_chat_view", True)
            self.view.settings().set("claudette_is_current_chat", True)

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

    def on_streaming_complete(self) -> None:
        """
        Improved handling of code blocks and phantom buttons.
        """
        if not self.view:
            return

        self.validate_and_fix_code_blocks()

        if not self.phantom_set:
            self.phantom_set = sublime.PhantomSet(self.view, "code_block_buttons")

        content = self.view.substr(sublime.Region(0, self.view.size()))
        code_blocks = self.find_code_blocks(content)

        phantoms = []
        new_positions: Set[int] = set()

        # Handle existing phantoms
        if self.phantom_set:
            for phantom in self.phantom_set.phantoms:
                if phantom.region.end() in self.existing_button_positions:
                    phantoms.append(phantom)
                    new_positions.add(phantom.region.end())

        # Add new phantoms
        for block in code_blocks:
            if block.end_pos not in new_positions:
                region = sublime.Region(block.end_pos, block.end_pos)
                escaped_code = self.escape_html(block.content)

                button_html = self.create_button_html(
                    escaped_code,
                    block.language
                )

                phantom = sublime.Phantom(
                    region,
                    button_html,
                    sublime.LAYOUT_BLOCK,
                    lambda href, code=block.content: self.handle_copy(code)
                )
                phantoms.append(phantom)
                new_positions.add(block.end_pos)

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
        if self.window:
            window_id = self.window.id()
            if window_id in self._instances:
                del self._instances[window_id]
        self.view = None

    def find_code_blocks(self, content: str) -> List[CodeBlock]:
        """
        Finds all code blocks in the content using improved regex pattern.
        Returns list of CodeBlock objects with positions and language info.
        """
        blocks = []
        # Updated regex to better handle language specification and edge cases
        pattern = r"```([\w+]*)\n(.*?)\n```"

        for match in re.finditer(pattern, content, re.DOTALL):
            language = match.group(1).strip()
            content = match.group(2).strip()
            blocks.append(CodeBlock(
                content=content,
                start_pos=match.start(),
                end_pos=match.end(),
                language=language
            ))
        return blocks

    def validate_and_fix_code_blocks(self) -> None:
        """
        Improved validation and fixing of code blocks with better edge case handling.
        """
        if not self.view:
            return

        content = self.view.substr(sublime.Region(0, self.view.size()))
        lines = content.split('\n')
        stack = []
        fixes_needed = []

        for i, line in enumerate(lines):
            stripped = line.strip()

            if stripped.startswith('```'):
                if len(stripped) > 3:  # Opening block with language
                    stack.append((i, stripped[3:].strip()))
                elif stripped == '```':
                    if stack:  # Proper closing
                        stack.pop()
                    else:  # Orphaned closing marker
                        fixes_needed.append((i, 'remove'))

        # Handle unclosed blocks
        if stack:
            self.view.set_read_only(False)
            for _, language in stack:
                self.view.run_command('append', {
                    'characters': '\n```',
                    'force': True,
                    'scroll_to_end': True
                })
            self.view.set_read_only(True)

    @staticmethod
    def escape_html(text: str) -> str:
        """
        Safely escape HTML special characters.
        """
        return (text
                .replace('&', '&amp;')
                .replace('"', '&quot;')
                .replace('<', '&lt;')
                .replace('>', '&gt;'))

    def create_button_html(self, code: str, language: str = '') -> str:
        """
        Creates HTML for the copy button with optional language indicator.
        """
        lang_indicator = f' ({language})' if language else ''
        return f'''
            <div class="code-block-button">
                <a class="copy-button" href="copy:{code}">
                    Copy{lang_indicator}
                </a>
            </div>
        '''
