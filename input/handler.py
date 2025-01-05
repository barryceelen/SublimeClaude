import sublime

class ClaudetteInputHandler:
    _instance = None

    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = ClaudetteInputHandler()
        return cls._instance

    def __init__(self):
        self.history = []
        self.history_pos = -1
        self.current_text = ''
        self.input_view = None

    def store_text(self, text):
        if text.strip():
            self.history.insert(0, text)
            self.history = self.history[:100]

    def navigate_history(self, forward=False):
        if not self.history or not self.input_view:
            return

        if self.history_pos == -1:
            self.current_text = self.input_view.substr(sublime.Region(0, self.input_view.size()))

        if forward:
            self.history_pos = max(-1, self.history_pos - 1)
        else:
            self.history_pos = min(len(self.history) - 1, self.history_pos + 1)

        if self.history_pos == -1:
            text = self.current_text
        else:
            text = self.history[self.history_pos]

        self.input_view.run_command("select_all")
        self.input_view.run_command("insert", {"characters": text})
