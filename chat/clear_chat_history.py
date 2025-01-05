import sublime
import sublime_plugin
from .chat_history import ClaudetteChatHistory

class ClaudetteClearChatHistoryCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        chat_history = ClaudetteChatHistory()
        chat_history.clear()
        sublime.status_message("Claude: Chat history cleared")
