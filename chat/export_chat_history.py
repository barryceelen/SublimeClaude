import sublime
import sublime_plugin
import json
import os
import time
from .chat_history import ClaudetteChatHistory
from ..constants import PLUGIN_NAME

# Valid message roles for Claude
VALID_ROLES = set(['system', 'user', 'assistant'])

def get_current_directory(window):
    """Helper function to get the directory of the current view"""
    view = window.active_view()
    if view and view.file_name():
        return os.path.dirname(view.file_name())
    return os.path.expanduser("~")

def validate_message(message):
    """Validate a single message object"""
    if not isinstance(message, dict):
        return False
    if 'role' not in message or 'content' not in message:
        return False
    if message['role'] not in VALID_ROLES:
        return False
    if not isinstance(message['content'], str):
        return False
    return True

class ClaudetteExportChatHistoryCommand(sublime_plugin.WindowCommand):
    def run(self):
        try:
            chat_history = ClaudetteChatHistory()
            messages = chat_history.get_messages()

            # Create an export object with metadata
            self.export_data = {
                "version": "1.0",
                "timestamp": time.time(),
                "messages": messages
            }

            # Show save dialog
            file_types = [("JSON", ["json"])]
            directory = get_current_directory(self.window)
            name = "sublimeclaude-chat-history.json"

            sublime.save_dialog(
                self.save_history,
                file_types,
                directory,
                name,
                "json"
            )

        except Exception as e:
            print("{0} Error exporting chat history: {1}".format(PLUGIN_NAME, str(e)))
            sublime.error_message("Could not export chat history")

    def save_history(self, path):
        if not path:
            return

        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.export_data, f, indent=2)
            sublime.status_message("{0}: Chat history exported successfully".format(PLUGIN_NAME))
        except Exception as e:
            print("{0} Error saving chat history: {1}".format(PLUGIN_NAME, str(e)))
            sublime.error_message("Could not save chat history")

class ClaudetteImportChatHistoryCommand(sublime_plugin.WindowCommand):
    def run(self):
        try:
            # Show open dialog
            file_types = [("JSON", ["json"])]
            directory = get_current_directory(self.window)

            sublime.open_dialog(
                self.load_history,
                file_types,
                directory,
                multi_select=False,
                allow_folders=False
            )
        except Exception as e:
            print("{0} Error importing chat history: {1}".format(PLUGIN_NAME, str(e)))
            sublime.error_message("Could not import chat history")

    def load_history(self, path):
        if not path:
            return

        # Check if the selected file is a JSON file
        if not path.lower().endswith('.json'):
            sublime.error_message("Please select a JSON file")
            return

        try:
            # Check if file exists and is readable
            if not os.path.isfile(path):
                sublime.error_message("File does not exist")
                return

            if not os.access(path, os.R_OK):
                sublime.error_message("File is not readable")
                return

            with open(path, 'r', encoding='utf-8') as f:
                try:
                    import_data = json.load(f)
                except ValueError as e:  # Python 3.3 uses ValueError for JSON decode errors
                    sublime.error_message("Invalid JSON format - {0}".format(str(e)))
                    return

            # Validate import data structure
            if not isinstance(import_data, dict) or 'messages' not in import_data:
                raise ValueError("Invalid chat history file format")

            if not isinstance(import_data['messages'], list):
                raise ValueError("Messages must be a list")

            # Filter and validate messages
            valid_messages = []
            invalid_count = 0

            for message in import_data['messages']:
                if validate_message(message):
                    valid_messages.append(message)
                else:
                    invalid_count += 1

            if not valid_messages:
                raise ValueError("No valid messages found in import file")

            # Import valid messages into chat history
            chat_history = ClaudetteChatHistory()

            for message in valid_messages:
                chat_history.add_message(message['role'], message['content'])

            status_message = "{0}: Chat history imported successfully".format(PLUGIN_NAME)
            if invalid_count > 0:
                status_message += " ({0} invalid messages skipped)".format(invalid_count)

            sublime.status_message(status_message)

        except Exception as e:
            print("{0} Error loading chat history: {1}".format(PLUGIN_NAME, str(e)))
            sublime.error_message("Could not load chat history - {0}".format(str(e)))
