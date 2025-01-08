import sublime
import sublime_plugin
import threading
from ..constants import PLUGIN_NAME, SETTINGS_FILE
from ..api.api import ClaudeAPI
from ..api.handler import StreamingResponseHandler
from .chat_history import ClaudetteChatHistory
from .chat_view import ClaudetteChatView

class ClaudetteAskQuestionCommand(sublime_plugin.TextCommand):
    def __init__(self, view):
        super().__init__(view)
        self.chat_view = None
        self.settings = None
        self._view = view

    def load_settings(self):
        if not self.settings:
            self.settings = sublime.load_settings(SETTINGS_FILE)

    def get_window(self):
        return self._view.window() or sublime.active_window()

    def is_visible(self):
        return True

    def is_enabled(self):
        return True

    def create_chat_panel(self):
        window = self.get_window()
        if not window:
            print(f"{PLUGIN_NAME} Error: No active window found")
            sublime.error_message(f"{PLUGIN_NAME} Error: No active window found")
            return None

        chat_view_manager = ClaudetteChatView(window, self.settings)
        view = chat_view_manager.create_or_get_view()
        if view:
            self.chat_view = chat_view_manager
        return view

    def handle_input(self, code, question):
        if not self.create_chat_panel():
            return

        if not self.settings.get('api_key'):
            self.chat_view.append_text(
                "⚠️ Claude API key not configured. Please set your API key in Claudette.sublime-settings\n"
            )
            return

        self.send_to_claude(code, question)

    def run(self, edit, code=None, question=None):
        try:
            self.load_settings()

            window = self.get_window()
            if not window:
                print(f"{PLUGIN_NAME} Error: No active window found")
                sublime.error_message(f"{PLUGIN_NAME} Error: No active window found")
                return

            if code is not None and question is not None:
                # Create chat panel for direct calls with code and question
                if not self.create_chat_panel():
                    return
                self.send_to_claude(code, question)
                return

            sel = self.view.sel()
            selected_text = self.view.substr(sel[0]) if sel else ''

            view = window.show_input_panel(
                "Ask Claude:",
                "",
                lambda q: self.handle_input(selected_text, q),
                None,
                None
            )

            if not view:
                print(f"{PLUGIN_NAME} Error: Could not create input panel")
                sublime.error_message(f"{PLUGIN_NAME} Error: Could not create input panel")
                return

        except Exception as e:
            print(f"{PLUGIN_NAME} Error in run command: {str(e)}")
            sublime.error_message(f"{PLUGIN_NAME} Error: Could not process request")

    def send_to_claude(self, code, question):
        try:
            if not self.chat_view:
                return

            message = "\n\n" if self.chat_view.get_size() > 0 else ""
            message += f"## Question\n\n{question}\n\n"

            if code.strip():
                message += f"### Selected Code\n\n```\n{code}\n```\n\n"

            message += "### Claude's Response\n\n"

            chat_history = ClaudetteChatHistory()

            user_message = question
            if code.strip():
                user_message = f"{question}\n\nCode:\n{code}"
            chat_history.add_message("user", user_message)

            self.chat_view.append_text(message)

            if self.chat_view.get_size() > 0:
                self.chat_view.focus()

            api = ClaudeAPI()
            handler = StreamingResponseHandler(self.chat_view.view)

            thread = threading.Thread(
                target=api.stream_response,
                args=(handler.append_chunk, chat_history.get_messages(api_format=True))
            )
            thread.start()

        except Exception as e:
            print(f"{PLUGIN_NAME} Error sending to Claude: {str(e)}")
            sublime.error_message(f"{PLUGIN_NAME} Error: Could not send message")
