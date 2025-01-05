import sublime_plugin

class ClaudetteInputHistoryListener(sublime_plugin.EventListener):
    def on_query_context(self, view, key, operator, operand, match_all):
        if key == "input_history":
            return view.settings().get("is_claudette_input", False)
        return None
