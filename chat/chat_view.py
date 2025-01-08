import sublime
from ..constants import PLUGIN_NAME

class ClaudetteChatView:
    def __init__(self, window, settings):
        self.window = window
        self.settings = settings
        self.view = None

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
