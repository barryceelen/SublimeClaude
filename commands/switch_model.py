import sublime
import sublime_plugin
from ..api.api import ClaudeAPI

class SublimeClaudeSettings:
    settings_file = 'SublimeClaude.sublime-settings'
    settings = None

    @classmethod
    def load(cls):
        cls.settings = sublime.load_settings(cls.settings_file)

    @classmethod
    def save(cls):
        sublime.save_settings(cls.settings_file)

class SublimeClaudeSwitchModelCommand(sublime_plugin.WindowCommand):
    def run(self):
        SublimeClaudeSettings.load()

        api = ClaudeAPI()
        models = api.fetch_models()
        current_model = SublimeClaudeSettings.settings.get('model');
        if current_model in models:
            selected_index = models.index(current_model)
        else:
            models.insert(0, current_model)
            selected_index = 0

        def on_select(index):
            if index != -1:
                selected_model = models[index]
                SublimeClaudeSettings.settings.set('model', selected_model)
                SublimeClaudeSettings.save()
                sublime.status_message("Claude model switched to {0}".format(str(selected_model)))

        self.window.show_quick_panel(models, on_select, 0, selected_index)

    def is_visible(self):
        return True
