import sublime
import json
import urllib.request
import urllib.parse
import urllib.error
from ..constants import SETTINGS_FILE

class ClaudeAPI:
    BASE_URL = 'https://api.anthropic.com/v1/'

    def __init__(self):
        self.settings = sublime.load_settings(SETTINGS_FILE)
        self.api_key = self.settings.get('api_key')
        self.model = self.settings.get('model', 'claude-3-opus-20240229')

    def stream_response(self, code, question, chunk_callback):
        def handle_error(error_msg):
            sublime.set_timeout(
                lambda msg=error_msg: chunk_callback(msg),
                0
            )

        try:
            headers = {
                'x-api-key': self.api_key,
                'anthropic-version': '2023-06-01',
                'content-type': 'application/json',
            }

            data = {
                'model': self.model,
                'messages': [
                    {
                        'role': 'user',
                        'content': 'Code:\n```\n{0}\n```\n\nQuestion: {1}'.format(code, question) if code else 'Question: {0}'.format(question)
                    }
                ],
                'stream': True,
                'max_tokens': 4000
            }

            req = urllib.request.Request(
                urllib.parse.urljoin(self.BASE_URL, 'messages'),
                data=json.dumps(data).encode('utf-8'),
                headers=headers,
                method='POST'
            )

            try:
                with urllib.request.urlopen(req) as response:
                    for line in response:
                        if not line or line.isspace():
                            continue

                        try:
                            chunk = line.decode('utf-8')
                            if not chunk.startswith('data: '):
                                continue

                            chunk = chunk[6:]  # Remove 'data: ' prefix
                            if chunk.strip() == '[DONE]':
                                break

                            data = json.loads(chunk)
                            if 'delta' in data and 'text' in data['delta']:
                                sublime.set_timeout(
                                    lambda text=data['delta']['text']: chunk_callback(text),
                                    0
                                )
                        except Exception:
                            continue  # Skip invalid chunks without error messages

            except urllib.error.HTTPError as e:
                if e.code == 401:
                    handle_error("⚠️ Authentication failed. Please check your API key in Claude.sublime-settings.\n\nExample configuration:\n```json\n{\n    \"api_key\": \"YOUR_API_KEY\",\n    \"model\": \"claude-3-opus-20240229\",\n    \"chat_panel_width\": 0.3\n}\n```\n")
                else:
                    handle_error("⚠️ API Error: {0}".format(str(e)))
            except urllib.error.URLError as e:
                handle_error("⚠️ Connection Error: {0}".format(str(e)))

        except Exception as e:
            handle_error("⚠️ Error: {0}".format(str(e)))
