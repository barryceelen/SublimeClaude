import sublime
import sublime_plugin
from ..constants import SETTINGS_FILE

class SublimeClaudeSelectSystemMessagePanelCommand(sublime_plugin.WindowCommand):
    """
    A command to switch between different system messages.

    This command shows a quick panel with available system messages
    and allows the user to select and switch to a different system message.
    """

    def is_visible(self):
        return True

    def run(self):
        settings = sublime.load_settings(SETTINGS_FILE)
        system_messages = settings.get('system_messages', [])
        current_index = settings.get('default_system_message_index', 0)

        if not system_messages:
            sublime.message_dialog("No system messages defined. Please add system messages in your settings.")
            return

        panel_items = []
        for msg in system_messages:
            display_msg = msg.split('\n')[0][:120].rstrip('. \t') + ('...' if len(msg) > 120 else '')
            panel_items.append(display_msg)

        def on_select(index):
            if index != -1:
                settings.set('default_system_message_index', index)
                sublime.save_settings(SETTINGS_FILE)
                sublime.status_message("System message switched")

        self.window.show_quick_panel(
            panel_items,
            on_select,
            0,
            current_index
        )
