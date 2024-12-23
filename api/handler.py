class StreamingResponseHandler:
    def __init__(self, chat_view):
        self.chat_view = chat_view
        self.accumulated_text = ''

    def append_chunk(self, chunk):
        self.accumulated_text += chunk

        self.chat_view.set_read_only(False)
        self.chat_view.run_command('append', {
            'characters': chunk,
            'force': True,
            'scroll_to_end': True
        })
        self.chat_view.set_read_only(True)
