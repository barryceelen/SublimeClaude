def claudette_chat_status_message(window, message: str, prefix: str = "ℹ️") -> None:
    """
    Display a status message in the active chat view.

    Args:
        window: The Sublime Text window
        message (str): The status message to display
        prefix (str, optional): Icon or text prefix for the message. Defaults to "ℹ️"
    """
    if not window:
        return

    # Find the active chat view
    current_chat_view = None
    for view in window.views():
        if (view.settings().get('claudette_is_chat_view', False) and
            view.settings().get('claudette_is_current_chat', False)):
            current_chat_view = view
            break

    if not current_chat_view:
        return

    if current_chat_view.size() > 0:
        message = f"\n\n{prefix} {message}\n"
    else:
        message = f"{prefix} {message}\n"

    current_chat_view.set_read_only(False)
    current_chat_view.run_command('append', {
        'characters': message,
        'force': True,
        'scroll_to_end': True
    })
    current_chat_view.set_read_only(True)
