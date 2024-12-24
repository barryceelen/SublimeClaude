import sublime_plugin

class SublimeClaudeInputHistoryListener(sublime_plugin.EventListener):
    def on_query_context(self, view, key, operator, operand, match_all):
        if key == "input_history":
            return view.settings().get("is_claude_input", False)
        return None
