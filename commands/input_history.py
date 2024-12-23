import sublime_plugin
from ..input.handler import ClaudeInputHandler

class InputHistoryCommand(sublime_plugin.TextCommand):
    def run(self, edit, forward=False):
        handler = ClaudeInputHandler.get_instance()
        handler.navigate_history(forward)
