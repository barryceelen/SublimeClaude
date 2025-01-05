import sublime
import sublime_plugin
import threading
from ..constants import PLUGIN_NAME, SETTINGS_FILE
from ..api.api import ClaudeAPI
from ..api.handler import StreamingResponseHandler
from ..input.handler import ClaudeInputHandler
from .chat_history import SublimeClaudeChatHistory

class SublimeClaudeAskQuestionCommand(sublime_plugin.TextCommand):
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
        try:
            window = self.get_window()
            if not window:
                print(f"{PLUGIN_NAME} Error: No active window found")
                sublime.error_message(f"{PLUGIN_NAME} Error: No active window found")
                return None

            chat_view = None

            for view in window.views():
                if view.name() == "Claude Chat":
                    chat_view = view
                    break

            if not chat_view:
                chat_view = window.new_file()
                if not chat_view:
                    print(f"{PLUGIN_NAME} Error: Could not create new file")
                    sublime.error_message(f"{PLUGIN_NAME} Error: Could not create new file")
                    return None

                chat_view.set_name("Claude Chat")
                chat_view.set_scratch(True)
                chat_view.assign_syntax('Packages/Markdown/Markdown.sublime-syntax')
                chat_view.set_read_only(True)

            self.chat_view = chat_view
            return self.chat_view

        except Exception as e:
            print(f"{PLUGIN_NAME} Error creating chat panel: {str(e)}")
            sublime.error_message(f"{PLUGIN_NAME} Error: Could not create chat panel")
            return None

    def handle_input(self, code, question):
        handler = ClaudeInputHandler.get_instance()
        handler.store_text(question)
        handler.history_pos = -1

        # Create chat panel only when question is submitted
        if not self.create_chat_panel():
            return

        # Check API key after creating chat panel
        if not self.settings.get('api_key'):
            self.chat_view.set_read_only(False)
            self.chat_view.run_command('append', {
                'characters': "⚠️ Claude API key not configured. Please set your API key in SublimeClaude.sublime-settings\n",
                'force': True,
                'scroll_to_end': True
            })
            self.chat_view.set_read_only(True)
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

            view.settings().set("is_claude_input", True)

            handler = ClaudeInputHandler.get_instance()
            handler.input_view = view

        except Exception as e:
            print(f"{PLUGIN_NAME} Error in run command: {str(e)}")
            sublime.error_message(f"{PLUGIN_NAME} Error: Could not process request")

    def send_to_claude(self, code, question):
        try:
            if not self.chat_view:
                return

            message = "\n\n" if self.chat_view.size() > 0 else ""
            message += f"## Question\n\n{question}\n\n"

            if code.strip():
                message += f"### Selected Code\n\n```\n{code}\n```\n\n"

            message += "### Claude's Response\n\n"

            chat_history = SublimeClaudeChatHistory()

            user_message = question
            if code.strip():
                user_message = f"{question}\n\nCode:\n{code}"
            chat_history.add_message("user", user_message)

            self.chat_view.set_read_only(False)
            self.chat_view.run_command('append', {
                'characters': message,
                'force': True,
                'scroll_to_end': True
            })

            if self.chat_view.size() > 0:
                self.chat_view.window().focus_view(self.chat_view)

            api = ClaudeAPI()
            handler = StreamingResponseHandler(self.chat_view)

            thread = threading.Thread(
                target=api.stream_response,
                args=(handler.append_chunk, chat_history.get_messages(api_format=True))
            )
            thread.start()

        except Exception as e:
            print(f"{PLUGIN_NAME} Error sending to Claude: {str(e)}")
            sublime.error_message(f"{PLUGIN_NAME} Error: Could not send message")
