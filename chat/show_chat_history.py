import sublime
import sublime_plugin
import time
from ..constants import PLUGIN_NAME
from .chat_history import SublimeClaudeChatHistory

class SublimeClaudeShowChatHistoryCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        try:
            window = self.view.window()
            if not window:
                print("{0} Error: No active window found".format(PLUGIN_NAME))
                sublime.error_message("{0} Error: No active window found".format(PLUGIN_NAME))
                return

            # Get the chat history
            chat_history = SublimeClaudeChatHistory()
            messages = chat_history.get_messages()

            # Create new view for history
            history_view = window.new_file()
            if not history_view:
                print("{0} Error: Could not create new file".format(PLUGIN_NAME))
                sublime.error_message("{0} Error: Could not create new file".format(PLUGIN_NAME))
                return

            history_view.set_name("Claude Chat History")
            history_view.set_scratch(True)
            history_view.assign_syntax('Packages/Markdown/Markdown.sublime-syntax')

            # Format the history
            formatted_history = "# Claude Chat History\n\n"
            for message in messages:
                if message['role'] == 'user':
                    # Format timestamp for user messages
                    timestamp = time.strftime("%d-%m-%Y %H:%M", time.localtime(message.get('timestamp', 0)))
                    formatted_history += "## Question ({0})\n\n".format(timestamp)
                else:
                    formatted_history += "### Claude's Response\n\n"

                formatted_history += "{0}\n\n".format(message['content'])

            # Insert the formatted history
            history_view.run_command('append', {
                'characters': formatted_history,
                'force': True,
                'scroll_to_end': True
            })

            history_view.set_read_only(True)

        except Exception as e:
            print("{0} Error showing chat history: {1}".format(PLUGIN_NAME, str(e)))
            sublime.error_message("{0} Error: Could not show chat history".format(PLUGIN_NAME))

    def is_visible(self):
        return True

    def is_enabled(self):
        return True
