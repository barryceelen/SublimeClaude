from ..chat.chat_history import ClaudetteChatHistory

class StreamingResponseHandler:
    def __init__(self, view, on_complete=None):
        self.view = view
        self.chat_history = ClaudetteChatHistory()
        self.current_response = ""
        self.on_complete = on_complete

    def append_chunk(self, chunk, is_done=False):
        self.current_response += chunk
        self.view.set_read_only(False)
        self.view.run_command('append', {
            'characters': chunk,
            'force': True,
            'scroll_to_end': True
        })
        self.view.set_read_only(True)

        if is_done and self.on_complete:
            self.on_complete()

    def __del__(self):
        try:
            if hasattr(self, 'current_response') and self.current_response:
                self.chat_history.add_message("assistant", self.current_response)
                if self.on_complete:
                    self.on_complete()
        except:
            pass
