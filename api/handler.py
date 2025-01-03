from ..chat.chat_history import SublimeClaudeChatHistory

class StreamingResponseHandler:
    def __init__(self, view):
        self.view = view
        self.chat_history = SublimeClaudeChatHistory()
        self.current_response = ""  # Initialize this to prevent the AttributeError

    def append_chunk(self, chunk):
        self.current_response += chunk
        self.view.set_read_only(False)
        self.view.run_command('append', {
            'characters': chunk,
            'force': True,
            'scroll_to_end': True
        })
        self.view.set_read_only(True)

    def __del__(self):
        try:
            if hasattr(self, 'current_response') and self.current_response:
                self.chat_history.add_message("assistant", self.current_response)
        except:
            pass  # Safely handle any cleanup errors
