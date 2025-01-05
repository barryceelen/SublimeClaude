import sublime_plugin
from ..input.handler import ClaudetteInputHandler

class ClaudetteInputHistoryCommand(sublime_plugin.TextCommand):
    def run(self, edit, forward=False):
        handler = ClaudetteInputHandler.get_instance()
        handler.navigate_history(forward)
