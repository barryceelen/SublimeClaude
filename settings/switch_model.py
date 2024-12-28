import sublime
import sublime_plugin
from ..api.api import ClaudeAPI
from ..constants import SETTINGS_FILE

class SublimeClaudeSwitchModelCommand(sublime_plugin.WindowCommand):
    """
    A command to switch between different Claude AI models.

    This command shows a quick panel with available Claude models
    and allows the user to select and switch to a different model.
    """

    def is_visible(self):
        return True

    def run(self):
        api = ClaudeAPI()
        settings = sublime.load_settings(SETTINGS_FILE)
        current_model = settings.get('model')
        models = api.fetch_models()

        if current_model in models:
            selected_index = models.index(current_model)
        else:
            models.insert(0, current_model)
            selected_index = 0

        def on_select(index):
            if index != -1:
                selected_model = models[index]
                settings.set('model', selected_model)
                settings.save()
                sublime.status_message("Claude model switched to {0}".format(str(selected_model)))

        self.window.show_quick_panel(models, on_select, 0, selected_index)
