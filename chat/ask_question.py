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

    def load_settings(self):
        if not self.settings:
            self.settings = sublime.load_settings(SETTINGS_FILE)

    def is_visible(self):
        return True

    def is_enabled(self):
        return True

    def create_chat_panel(self):
        try:
            window = self.view.window()
            if not window:
                print("{0} Error: No active window found".format(PLUGIN_NAME))
                sublime.error_message("{0} Error: No active window found".format(PLUGIN_NAME))
                return None

            chat_view = None

            # Find existing chat view
            for view in window.views():
                if view.name() == "Claude Chat":
                    chat_view = view
                    break

            # Create new if not found
            if not chat_view:
                chat_view = window.new_file()
                if not chat_view:
                    print("{0} Error: Could not create new file".format(PLUGIN_NAME))
                    sublime.error_message("{0} Error: Could not create new file".format(PLUGIN_NAME))
                    return None

                chat_view.set_name("Claude Chat")
                chat_view.set_scratch(True)
                chat_view.assign_syntax('Packages/Markdown/Markdown.sublime-syntax')
                chat_view.set_read_only(True)

            self.chat_view = chat_view
            self.load_settings()

            return self.chat_view

        except Exception as e:
            print("{0} Error creating chat panel: {1}".format(PLUGIN_NAME, str(e)))
            sublime.error_message("{0} Error: Could not create chat panel".format(PLUGIN_NAME))
            return None

    def handle_input(self, code, question):
        handler = ClaudeInputHandler.get_instance()
        handler.store_text(question)
        handler.history_pos = -1
        self.send_to_claude(code, question)

    def run(self, edit, code=None, question=None):
        try:
            self.load_settings()

            # Verify we have a valid window before proceeding
            if not self.view.window():
                print("{0} Error: No active window found".format(PLUGIN_NAME))
                sublime.error_message("{0} Error: No active window found".format(PLUGIN_NAME))
                return

            chat_panel = self.create_chat_panel()
            if not chat_panel:
                return

            if not self.settings.get('api_key'):
                self.chat_view.set_read_only(False)
                self.chat_view.run_command('append', {
                    'characters': "⚠️ Claude API key not configured. Please set your API key in `${packages}/User/SublimeClaude.sublime-settings`\n\nExample configuration:\n```json\n{\n    \"api_key\": \"YOUR_API_KEY\",\n    \"model\": \"claude-3-opus-20240229\"\n}\n```\n",
                    'force': True,
                    'scroll_to_end': True
                })
                self.chat_view.set_read_only(True)
                return

            if code is not None and question is not None:
                self.send_to_claude(code, question)
                return

            sel = self.view.sel()
            selected_text = self.view.substr(sel[0]) if sel else ''

            # Verify window again before showing input panel
            window = self.view.window()
            if not window:
                print("{0} Error: No active window found".format(PLUGIN_NAME))
                sublime.error_message("{0} Error: No active window found".format(PLUGIN_NAME))
                return

            view = window.show_input_panel(
                "Ask Claude:",
                "",
                lambda q: self.handle_input(selected_text, q),
                None,
                None
            )

            if not view:
                print("{0} Error: Could not create input panel".format(PLUGIN_NAME))
                sublime.error_message("{0} Error: Could not create input panel".format(PLUGIN_NAME))
                return

            model = self.settings.get('model')
            sublime.status_message('Model: {}'.format(model or "Not set"))

            view.settings().set("is_claude_input", True)

            handler = ClaudeInputHandler.get_instance()
            handler.input_view = view

        except Exception as e:
            print("{0} Error in run command: {1}".format(PLUGIN_NAME, str(e)))
            sublime.error_message("{0} Error: Could not process request".format(PLUGIN_NAME))

    def send_to_claude(self, code, question):
        try:
            if not self.chat_view:
                return

            message = '';

            if self.chat_view.size() > 0:
                message += "\n\n";

            message += "## Question\n\n{0}\n\n".format(question)

            if code.strip():
                message += "### Selected Code\n\n```\n{0}\n```\n\n".format(code)

            message += "### Claude's Response\n\n"

            # Get the singleton instance
            chat_history = SublimeClaudeChatHistory()

            messages = chat_history.get_messages(api_format=True)

            # Add user message to history
            user_message = question
            if code.strip():
                user_message = "{0}\n\nCode:\n{1}".format(question, code)
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
            print("{0} Error sending to Claude: {1}".format(PLUGIN_NAME, str(e)))
            sublime.error_message("{0} Error: Could not send message".format(PLUGIN_NAME))
