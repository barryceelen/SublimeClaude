import sublime
import sublime_plugin
import json
import os
import time
from .chat_history import SublimeClaudeChatHistory

class SublimeClaudeExportChatHistoryCommand(sublime_plugin.WindowCommand):
    def run(self):
        try:
            chat_history = SublimeClaudeChatHistory()
            messages = chat_history.get_messages()

            # Create an export object with metadata
            export_data = {
                "version": "1.0",
                "timestamp": time.time(),
                "messages": messages
            }

            # Show save dialog
            self.window.show_input_panel(
                "Save chat history as:",
                os.path.expanduser("~/claude_chat_history.json"),
                lambda path: self.save_history(path, export_data),
                None,
                None
            )

        except Exception as e:
            print("{0} Error exporting chat history: {1}".format(PLUGIN_NAME, str(e)))
            sublime.error_message("{0} Error: Could not export chat history".format(PLUGIN_NAME))

    def save_history(self, path, data):
        try:
            # Ensure directory exists
            directory = os.path.dirname(os.path.abspath(path))
            if not os.path.exists(directory):
                os.makedirs(directory)

            # Save JSON file
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)

            sublime.status_message("Claude: Chat history exported successfully")

        except Exception as e:
            print("{0} Error saving chat history: {1}".format(PLUGIN_NAME, str(e)))
            sublime.error_message("{0} Error: Could not save chat history".format(PLUGIN_NAME))

class SublimeClaudeImportChatHistoryCommand(sublime_plugin.WindowCommand):
    def run(self):
        try:
            # Show open dialog
            self.window.show_input_panel(
                "Import chat history from:",
                os.path.expanduser("~/claude_chat_history.json"),
                self.load_history,
                None,
                None
            )

        except Exception as e:
            print("{0} Error importing chat history: {1}".format(PLUGIN_NAME, str(e)))
            sublime.error_message("{0} Error: Could not import chat history".format(PLUGIN_NAME))

    def load_history(self, path):
        try:
            # Check if file exists
            if not os.path.exists(path):
                sublime.error_message("{0} Error: File not found".format(PLUGIN_NAME))
                return

            # Load and validate JSON file
            with open(path, 'r') as f:
                data = json.load(f)

            # Basic validation
            if not isinstance(data, dict) or 'messages' not in data:
                sublime.error_message("{0} Error: Invalid chat history file format".format(PLUGIN_NAME))
                return

            # Clear current history and import new messages
            chat_history = SublimeClaudeChatHistory()
            chat_history.clear()

            for message in data['messages']:
                # Basic message validation
                if not isinstance(message, dict) or 'role' not in message or 'content' not in message:
                    continue

                chat_history.add_message(
                    message['role'],
                    message['content']
                )

            sublime.status_message("Claude: Chat history imported successfully")

        except ValueError as e:
            print("{0} Error parsing chat history file: {1}".format(PLUGIN_NAME, str(e)))
            sublime.error_message("{0} Error: Invalid JSON file".format(PLUGIN_NAME))
        except Exception as e:
            print("{0} Error loading chat history: {1}".format(PLUGIN_NAME, str(e)))
            sublime.error_message("{0} Error: Could not load chat history".format(PLUGIN_NAME))
