import sublime
import sublime_plugin
from .chat_history import SublimeClaudeChatHistory

class SublimeClaudeClearChatHistoryCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        chat_history = SublimeClaudeChatHistory()
        chat_history.clear()
        sublime.status_message("Claude: Chat history cleared")
