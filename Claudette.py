#      ___/\/\/\/\/\__/\/\__________________________________/\/\________________/\/\________/\/\_________________
#     _/\/\__________/\/\____/\/\/\______/\/\__/\/\________/\/\____/\/\/\____/\/\/\/\/\__/\/\/\/\/\____/\/\/\___
#    _/\/\__________/\/\________/\/\____/\/\__/\/\____/\/\/\/\__/\/\/\/\/\____/\/\________/\/\______/\/\/\/\/\_
#   _/\/\__________/\/\____/\/\/\/\____/\/\__/\/\__/\/\__/\/\__/\/\__________/\/\________/\/\______/\/\_______
#  ___/\/\/\/\/\__/\/\/\__/\/\/\/\/\____/\/\/\/\____/\/\/\/\____/\/\/\/\____/\/\/\______/\/\/\______/\/\/\/\_
# __________________________________________________________________________________________________________

import sublime
import sublime_plugin

from .chat.ask_question import ClaudetteAskQuestionCommand, ClaudetteAskNewQuestionCommand
from .chat.chat_history import ClaudetteClearChatHistoryCommand, ClaudetteExportChatHistoryCommand, ClaudetteImportChatHistoryCommand
from .settings.select_model_panel import ClaudetteSelectModelPanelCommand
from .settings.select_system_message_panel import ClaudetteSelectSystemMessagePanelCommand
from .statusbar.spinner import Spinner

def plugin_loaded():
    spinner = Spinner()
    spinner.start("Claudette", 1000)

class ClaudetteFocusListener(sublime_plugin.EventListener):
    def on_activated(self, view):
        if view.settings().get('claudette_is_chat_view', False):
            print(f"Chat view activated: {view.id()}")
            print(f"Window id: {view.window().id() if view.window() else 'None'}")
            self._update_current_chat_status(view)

    def on_load(self, view):
        if view.settings().get('claudette_is_chat_view', False):
            print(f"Chat view loaded: {view.id()}")
            self._update_current_chat_status(view)

    def on_new(self, view):
        if view.settings().get('claudette_is_chat_view', False):
            print(f"New chat view: {view.id()}")
            self._update_current_chat_status(view)

    def on_clone(self, view):
        if view.settings().get('claudette_is_chat_view', False):
            print(f"Chat view cloned: {view.id()}")
            self._update_current_chat_status(view)

    def _update_current_chat_status(self, view):
        window = view.window()
        if not window:
            print(f"No window found for view: {view.id()}")
            return

        # Set this view as the current chat for this window
        view.settings().set('claudette_is_current_chat', True)
        print(f"Set view {view.id()} as current chat in window {window.id()}")

        # Update other chat views in THIS window only
        for other_view in window.views():
            if (other_view.id() != view.id() and
                other_view.settings().get('claudette_is_chat_view', False)):
                print(f"Setting view {other_view.id()} to not current in window {window.id()}")
                other_view.settings().set('claudette_is_current_chat', False)

        # Verify the update
        print(f"Final current status for view {view.id()}: "
              f"{view.settings().get('claudette_is_current_chat', False)}")
