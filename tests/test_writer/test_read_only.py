"""Read-only behavior tests for Safari Writer."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from safari_writer.app import SafariWriterApp
from safari_writer.screens.editor import EditorArea
from safari_writer.state import AppState
from tests.test_writer.test_editor import make_editor


def make_read_only_editor(text: str = "") -> EditorArea:
    editor = make_editor(text)
    editor.state.read_only = True
    editor.refresh = MagicMock()
    editor._update_status = MagicMock()
    return editor


def make_key(key: str, character: str | None = None) -> MagicMock:
    event = MagicMock()
    event.key = key
    event.character = character
    event.stop = MagicMock()
    return event


def test_editor_on_key_blocks_typing_in_read_only_mode():
    editor = make_read_only_editor("")
    mock_screen = MagicMock()

    with patch.object(
        type(editor), "screen", new_callable=lambda: property(lambda self: mock_screen)
    ):
        editor.on_key(make_key("a", "a"))

    assert editor.state.buffer == [""]
    mock_screen.set_message.assert_called_once()


def test_editor_on_key_blocks_delete_in_read_only_mode():
    editor = make_read_only_editor("abc")
    editor.state.cursor_col = 1
    mock_screen = MagicMock()

    with patch.object(
        type(editor), "screen", new_callable=lambda: property(lambda self: mock_screen)
    ):
        editor.on_key(make_key("delete"))

    assert editor.state.buffer == ["abc"]
    mock_screen.set_message.assert_called_once()


def test_app_save_action_is_blocked_in_read_only_mode():
    messages: list[str] = []
    app = SafariWriterApp(state=AppState(read_only=True))
    app.set_message = messages.append
    app.push_screen = MagicMock()

    app._action_save_via_safari_dos()

    assert messages == ["Save is unavailable in read-only mode"]
    app.push_screen.assert_not_called()
