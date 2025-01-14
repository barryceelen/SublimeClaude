import sublime
import sublime_plugin
import threading
from ..constants import PLUGIN_NAME, SETTINGS_FILE
from ..api.api import ClaudeAPI
from ..api.handler import StreamingResponseHandler
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

    def create_chat_panel(self, force_new=False):
        """
        Creates a chat panel, optionally forcing a new view creation.

        Args:
            force_new (bool): If True, always creates a new view instead of reusing existing one

        Returns:
            sublime.View: The created or existing view
        """
        window = self.get_window()
        if not window:
            print(f"{PLUGIN_NAME} Error: No active window found")
            sublime.error_message(f"{PLUGIN_NAME} Error: No active window found")
            return None

        try:
            if force_new:
                # Create a new view
                new_view = window.new_file()
                if not new_view:
                    raise Exception("Could not create new view")

                # Initialize it as a chat view
                new_view.set_scratch(True)
                new_view.set_name("Claude Chat")
                new_view.assign_syntax('Packages/Markdown/Markdown.sublime-syntax')
                new_view.settings().set('claudette_is_chat_view', True)
                new_view.settings().set('claudette_is_current_chat', True)

                # Mark other chat views as not current
                for view in window.views():
                    if view != new_view and view.settings().get('claudette_is_chat_view', False):
                        view.settings().set('claudette_is_current_chat', False)

                # Create a new chat view instance for this view
                self.chat_view = ClaudetteChatView(window, self.settings)
                self.chat_view.view = new_view

                # Register the new instance
                ClaudetteChatView._instances[window.id()] = self.chat_view

                return new_view
            else:
                # Use existing behavior
                self.chat_view = ClaudetteChatView.get_instance(window, self.settings)
                return self.chat_view.create_or_get_view()

        except Exception as e:
            print(f"{PLUGIN_NAME} Error: {str(e)}")
            sublime.error_message(f"{PLUGIN_NAME} Error: Could not create or get chat panel")
            return None

    def handle_input(self, code, question):
        if not question or question.strip() == '':
            return None

        if not self.create_chat_panel():
            return

        if not self.settings.get('api_key'):
            self.chat_view.append_text(
                "A Claude API key is required. Please add your API key via Package Settings > Claudette.\n"
            )
            return

        self.send_to_claude(code, question.strip())

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

            # Format the user message with code if present
            user_message = question
            if code.strip():
                user_message = f"{question}\n\nCode:\n{code}"

            # Add question to conversation history and get full context
            conversation = self.chat_view.handle_question(user_message)

            self.chat_view.append_text(message)

            if self.chat_view.get_size() > 0:
                self.chat_view.focus()

            api = ClaudeAPI()

            # Store the starting position of the message
            message_start = self.chat_view.view.size()

            def on_complete():
                # Add the response to conversation history after streaming is complete
                response_start = self.chat_view.view.size()
                response_region = sublime.Region(response_start - message_start)
                response_text = self.chat_view.view.substr(response_region)
                self.chat_view.handle_response(response_text)
                self.chat_view.on_streaming_complete()

            handler = StreamingResponseHandler(
                view=self.chat_view.view,  # Changed from self.view to self.chat_view.view
                chat_view=self.chat_view,  # Changed from self to self.chat_view
                on_complete=on_complete    # Changed to use the local on_complete function
            )

            thread = threading.Thread(
                target=api.stream_response,
                args=(handler.append_chunk, conversation)
            )
            thread.start()

        except Exception as e:
            print(f"{PLUGIN_NAME} Error sending to Claude: {str(e)}")
            sublime.error_message(f"{PLUGIN_NAME} Error: Could not send message")
