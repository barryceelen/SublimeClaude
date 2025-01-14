import sublime
import sublime_plugin
import json
import os
from ..constants import PLUGIN_NAME
from .ask_question import ClaudetteAskQuestionCommand
from .chat_view import ClaudetteChatView

def get_cache_path():
    """Get the path to the cache file"""
    cache_dir = os.path.join(sublime.cache_path(), PLUGIN_NAME)
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    return os.path.join(cache_dir, 'last_chat_history_path.txt')

def get_last_directory():
    """Get the last used directory from cache"""
    cache_path = get_cache_path()
    try:
        if os.path.exists(cache_path):
            with open(cache_path, 'r', encoding='utf-8') as f:
                last_path = f.read().strip()
                if last_path and os.path.exists(os.path.dirname(last_path)):
                    return os.path.dirname(last_path)
    except Exception as e:
        print(f"{PLUGIN_NAME} Error reading cache: {str(e)}")
    return os.path.expanduser("~")

def save_last_directory(path):
    """Save the last used directory to cache"""
    cache_path = get_cache_path()
    try:
        with open(cache_path, 'w', encoding='utf-8') as f:
            f.write(path)
    except Exception as e:
        print(f"{PLUGIN_NAME} Error saving to cache: {str(e)}")

def get_current_directory(window):
    """Helper function to get the directory of the current view or last used directory"""
    last_dir = get_last_directory()
    view = window.active_view()
    if view and view.file_name():
        return os.path.dirname(view.file_name())
    return last_dir

def validate_message(message):
    """Validate a single message object"""
    if not isinstance(message, dict):
        return False
    if 'role' not in message or 'content' not in message:
        return False
    if message['role'] not in {'system', 'user', 'assistant'}:
        return False
    if not isinstance(message['content'], str):
        return False
    return True

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
            print(f"{PLUGIN_NAME} Error importing chat history: {str(e)}")
            sublime.error_message("Could not import chat history")

    def load_history(self, path):
        if not path or not path.lower().endswith('.json'):
            return

        try:
            # Save the last used path
            save_last_directory(path)

            # Read and validate the JSON file
            with open(path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)

            if not isinstance(import_data, dict) or 'messages' not in import_data:
                raise ValueError("Invalid chat history file format")

            messages = import_data['messages']
            if not isinstance(messages, list):
                raise ValueError("Messages must be a list")

            # Validate messages
            valid_messages = [msg for msg in messages if validate_message(msg)]
            if not valid_messages:
                raise ValueError("No valid messages found in import file")

            # Create ask command with force_new=True
            ask_cmd = ClaudetteAskQuestionCommand(self.window.active_view())
            ask_cmd.load_settings()

            # Create a new chat view
            sublime_view = ask_cmd.create_chat_panel(force_new=True)
            if not sublime_view:
                return

            # Get the chat view instance
            chat_view = ClaudetteChatView.get_instance(self.window, ask_cmd.settings)
            if not chat_view:
                return

            # Clear any existing content
            sublime_view.set_read_only(False)
            sublime_view.run_command('select_all')
            sublime_view.run_command('right_delete')

            # Initialize chat view settings
            chat_settings = ask_cmd.settings.get('chat', {})
            show_line_numbers = chat_settings.get('line_numbers', False)
            sublime_view.settings().set("line_numbers", show_line_numbers)

            # Render messages in the view
            first_message = True
            for message in valid_messages:
                if message['role'] == 'user':
                    prefix = "" if first_message else "\n\n"
                    chat_view.append_text(
                        f"{prefix}## Question\n\n{message['content']}\n\n### Claude's Response\n\n",
                        scroll_to_end=False
                    )
                    first_message = False
                elif message['role'] == 'assistant':
                    chat_view.append_text(
                        f"{message['content']}\n",
                        scroll_to_end=False
                    )

            # Store the conversation history in the view's settings
            sublime_view.settings().set('claudette_conversation_json', json.dumps(valid_messages))

            # Move cursor to the end and scroll
            end_point = sublime_view.size()
            sublime_view.sel().clear()
            sublime_view.sel().add(sublime.Region(end_point))
            sublime_view.show(end_point)

            # Update buttons for code blocks
            chat_view.on_streaming_complete()

            sublime.status_message(f"{PLUGIN_NAME}: Chat history imported successfully")

        except Exception as e:
            print(f"{PLUGIN_NAME} Error loading chat history: {str(e)}")
            sublime.error_message(f"Could not load chat history - {str(e)}")

class ClaudetteExportChatHistoryCommand(sublime_plugin.WindowCommand):
    def run(self):
        try:
            view = self.window.active_view()
            if not view:
                return

            # Get the conversation history from view settings
            conversation_json = view.settings().get('claudette_conversation_json', '[]')
            try:
                messages = json.loads(conversation_json)
            except json.JSONDecodeError:
                messages = []

            if not messages:
                sublime.error_message("No chat history to export")
                return

            # Show save dialog
            file_types = [("JSON", ["json"])]
            directory = get_current_directory(self.window)

            sublime.save_dialog(
                self.save_history,
                file_types,
                directory,
                "chat_history.json",
                False  # allow_folders
            )
        except Exception as e:
            print(f"{PLUGIN_NAME} Error exporting chat history: {str(e)}")
            sublime.error_message("Could not export chat history")

    def save_history(self, path):
        if not path or not path.lower().endswith('.json'):
            return

        try:
            view = self.window.active_view()
            if not view:
                return

            # Save the last used path
            save_last_directory(path)

            # Get the conversation history from view settings
            conversation_json = view.settings().get('claudette_conversation_json', '[]')
            try:
                messages = json.loads(conversation_json)
            except json.JSONDecodeError:
                messages = []

            # Create the export data structure
            export_data = {
                'messages': messages
            }

            # Write to file
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            sublime.status_message(f"{PLUGIN_NAME}: Chat history exported successfully")

        except Exception as e:
            print(f"{PLUGIN_NAME} Error saving chat history: {str(e)}")
            sublime.error_message(f"Could not save chat history - {str(e)}")

class ClaudetteClearChatHistoryCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        # Get the current window
        window = sublime.active_window()
        if not window:
            return

        # Find the current chat view in this window
        current_chat_view = None
        for view in window.views():
            if (view.settings().get('claudette_is_chat_view', False) and
                view.settings().get('claudette_is_current_chat', False)):
                current_chat_view = view
                break

        if current_chat_view:
            # Clear the conversation history setting
            current_chat_view.settings().set('claudette_conversation_json', '[]')

            # Add clear history message at the bottom of the view
            current_chat_view.set_read_only(False)

            # Get the end position of the view
            end_point = current_chat_view.size()

            # Add two newlines before the message if the view isn't empty
            if end_point > 0:
                current_chat_view.insert(edit, end_point, "\n\n")
                end_point += 2

            # Add the message with an icon
            clear_message = "⚠️ Chat history cleared"
            current_chat_view.insert(edit, end_point, clear_message)

            current_chat_view.set_read_only(True)

            # Scroll to the end to show the message
            current_chat_view.show(current_chat_view.size())

            sublime.status_message("Chat history cleared")
        else:
            sublime.status_message("No active chat view found")
