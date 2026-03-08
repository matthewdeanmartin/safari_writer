"""Tests for the bundled demo mode."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, PropertyMock, patch

from safari_writer.app import SafariWriterApp
from safari_writer.document_io import load_demo_document_buffer
from safari_writer.mail_merge_db import MailMergeDB
from safari_writer.screens.editor import (
    CTRL_BOLD,
    CTRL_CENTER,
    CTRL_CHAIN,
    CTRL_EJECT,
    CTRL_ELONGATE,
    CTRL_FOOTER,
    CTRL_FORM,
    CTRL_HEADER,
    CTRL_HEADING,
    CTRL_MERGE,
    CTRL_PARA,
    CTRL_RIGHT,
    CTRL_SUB,
    CTRL_SUPER,
    CTRL_UNDERLINE,
)
from safari_writer.screens.main_menu import MENU_ITEMS, MainMenuScreen
from safari_writer.state import AppState
from textual.widgets import Static


def test_main_menu_exposes_demo_mode():
    assert ("T", "ry Demo Mode", "demo") in MENU_ITEMS
    assert ("O", "pen Safari DOS", "safari_dos") in MENU_ITEMS
    assert any(
        binding.key == "t" and binding.action == "menu_action('demo')"
        for binding in MainMenuScreen.BINDINGS
    )
    assert any(
        binding.key == "o" and binding.action == "menu_action('safari_dos')"
        for binding in MainMenuScreen.BINDINGS
    )


def test_main_menu_context_text_includes_edit_and_merge_files():
    screen = MainMenuScreen()
    state = AppState(filename=r"C:\docs\draft.sfw")
    state.mail_merge_db = MailMergeDB(filename=r"C:\data\contacts.mm")
    app = MagicMock()
    app.state = state

    with patch.object(MainMenuScreen, "app", new_callable=PropertyMock) as app_prop:
        app_prop.return_value = app
        assert screen._context_text() == " Edit: draft.sfw   Merge: contacts.mm"


def test_main_menu_mount_shows_context_and_status_bars():
    async def run():
        state = AppState(filename=r"C:\docs\draft.sfw")
        state.mail_merge_db = MailMergeDB(filename=r"C:\data\contacts.mm")
        app = SafariWriterApp(state=state)
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, MainMenuScreen)
            assert "Edit: draft.sfw" in screen.query_one("#context-bar", Static).content
            assert (
                "Merge: contacts.mm" in screen.query_one("#context-bar", Static).content
            )
            assert "Bytes Free:" in screen.query_one("#status-text", Static).content

    asyncio.run(run())


def test_default_save_name_uses_windows_basename_on_linux():
    app = SafariWriterApp(state=AppState(filename=r"C:\docs\draft.sfw"))

    assert app._default_save_name() == "draft.sfw"


def test_handle_menu_action_routes_to_demo(monkeypatch):
    app = SafariWriterApp()
    called: list[str] = []
    monkeypatch.setattr(app, "_action_demo", lambda: called.append("demo"))
    monkeypatch.setattr(app, "_action_safari_dos", lambda: called.append("safari_dos"))

    app.handle_menu_action("demo")
    app.handle_menu_action("safari_dos")

    assert called == ["demo", "safari_dos"]


def test_do_demo_loads_bundled_document(monkeypatch):
    app = SafariWriterApp(state=AppState())
    app.state.buffer = ["old"]
    app.state.cursor_row = 4
    app.state.cursor_col = 9
    app.state.filename = "draft.sfw"
    app.state.modified = True
    messages: list[str] = []
    opened: list[AppState] = []

    monkeypatch.setattr(
        "safari_writer.app.load_demo_document_buffer", lambda: ["demo", "text"]
    )
    monkeypatch.setattr(app, "set_message", lambda msg: messages.append(msg))
    monkeypatch.setattr(app, "_open_editor", lambda: opened.append(app.state))

    app._do_demo()

    assert app.state.buffer == ["demo", "text"]
    assert app.state.cursor_row == 0
    assert app.state.cursor_col == 0
    assert app.state.filename == ""
    assert app.state.modified is False
    assert messages == ["Loaded demo document"]
    assert opened == [app.state]


def test_do_demo_reports_resource_errors(monkeypatch):
    app = SafariWriterApp(state=AppState())
    messages: list[str] = []

    monkeypatch.setattr(
        "safari_writer.app.load_demo_document_buffer",
        MagicMock(side_effect=FileNotFoundError("missing demo")),
    )
    monkeypatch.setattr(app, "set_message", lambda msg: messages.append(msg))
    monkeypatch.setattr(
        app,
        "_open_editor",
        lambda: (_ for _ in ()).throw(AssertionError("should not open")),
    )

    app._do_demo()

    assert messages == ["Demo load error: missing demo"]


def test_demo_document_includes_all_supported_markers():
    demo_text = "\n".join(load_demo_document_buffer())

    for marker in [
        CTRL_BOLD,
        CTRL_UNDERLINE,
        CTRL_CENTER,
        CTRL_RIGHT,
        CTRL_ELONGATE,
        CTRL_SUPER,
        CTRL_SUB,
        CTRL_PARA,
        CTRL_MERGE,
        CTRL_HEADER,
        CTRL_FOOTER,
        CTRL_HEADING,
        CTRL_EJECT,
        CTRL_CHAIN,
        CTRL_FORM,
    ]:
        assert marker in demo_text


def test_demo_document_reads_like_getting_started_copy():
    demo_text = "\n".join(load_demo_document_buffer())

    assert "quick tour" in demo_text
    assert "Press F1 or ?" in demo_text
    assert "Print / Export" in demo_text
    assert "Type here:" in demo_text
