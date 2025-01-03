import time

class SublimeClaudeChatHistory:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SublimeClaudeChatHistory, cls).__new__(cls)
            cls._instance.messages = []
        return cls._instance

    def __init__(self):
        # Initialize only if it hasn't been initialized
        if not hasattr(self, 'messages'):
            self.messages = []

    def add_message(self, role, content):
        self.messages.append({"role": role, "content": content, "timestamp": time.time()})

    def get_messages(self, api_format=False):
       """Return messages list. If api_format=True, only return role/content keys."""
       if not api_format:
           return self.messages

       return [{
           "role": m["role"],
           "content": m["content"]
       } for m in self.messages]

    def clear(self):
        self.messages = []
