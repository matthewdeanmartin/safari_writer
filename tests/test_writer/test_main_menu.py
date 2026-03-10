"""Tests for the Main Menu screen layout and behaviour."""

from __future__ import annotations

import asyncio

from safari_writer.app import SafariWriterApp
from safari_writer.screens.main_menu import (
    COL1_ITEMS,
    COL2_ITEMS,
    COL3_ITEMS,
    MENU_ITEMS,
    MainMenuScreen,
    MenuItem,
)
from safari_writer.state import AppState


class TestMenuColumns:
    def test_col1_has_document_ops(self) -> None:
        actions = [action for _, _, action in COL1_ITEMS]
        assert "create" in actions
        assert "edit" in actions
        assert "print" in actions
        assert "global_format" in actions
        assert "mail_merge" in actions
        assert "verify" in actions

    def test_col2_has_file_ops(self) -> None:
        actions = [action for _, _, action in COL2_ITEMS]
        assert "load" in actions
        assert "save" in actions
        assert "save_as" in actions
        assert "delete" in actions
        assert "new_folder" in actions
        assert "index1" in actions
        assert "index2" in actions
        assert "quit" in actions

    def test_col3_has_tools(self) -> None:
        actions = [action for _, _, action in COL3_ITEMS]
        assert "safari_dos" in actions
        assert "safari_chat" in actions
        assert "safari_fed" in actions
        assert "safari_repl" in actions
        assert "style_switcher" in actions
        assert "demo" in actions

    def test_no_duplicate_keys(self) -> None:
        keys = [key.lower() for key, _, _ in MENU_ITEMS]
        assert len(keys) == len(set(keys)), f"Duplicate keys: {keys}"

    def test_all_items_combined(self) -> None:
        assert MENU_ITEMS == COL1_ITEMS + COL2_ITEMS + COL3_ITEMS

    def test_col3_is_separate_from_file_ops(self) -> None:
        # Demo moved from col1 to col3
        col1_actions = {a for _, _, a in COL1_ITEMS}
        col2_actions = {a for _, _, a in COL2_ITEMS}
        col3_actions = {a for _, _, a in COL3_ITEMS}
        assert "demo" not in col1_actions
        assert "demo" not in col2_actions
        assert "demo" in col3_actions


class TestMenuItemWidget:
    def test_menu_item_markup(self) -> None:
        item = MenuItem("C", "reate File")
        # Should contain the key in the content markup
        assert "C" in item.content


class TestMainMenuMount:
    def test_three_columns_rendered(self) -> None:
        async def run():
            app = SafariWriterApp(state=AppState())
            async with app.run_test() as pilot:
                await pilot.pause()
                screen = app.screen
                assert isinstance(screen, MainMenuScreen)
                # Verify all three columns exist
                screen.query_one("#menu-col-1")
                screen.query_one("#menu-col-2")
                screen.query_one("#menu-col-3")

        asyncio.run(run())

    def test_clock_widget_present(self) -> None:
        async def run():
            app = SafariWriterApp(state=AppState())
            async with app.run_test() as pilot:
                await pilot.pause()
                screen = app.screen
                assert isinstance(screen, MainMenuScreen)
                from textual.widgets import Static

                clock = screen.query_one("#status-clock", Static)
                # Clock text should contain a date-like string
                text = clock.content
                assert len(text) >= 10  # YYYY-MM-DD at minimum

        asyncio.run(run())

    def test_status_text_shows_bytes_free(self) -> None:
        async def run():
            app = SafariWriterApp(state=AppState())
            async with app.run_test() as pilot:
                await pilot.pause()
                screen = app.screen
                assert isinstance(screen, MainMenuScreen)
                from textual.widgets import Static

                status = screen.query_one("#status-text", Static)
                assert "Bytes Free" in status.content

        asyncio.run(run())


class TestActionQuitOverride:
    def test_app_has_action_quit(self) -> None:
        app = SafariWriterApp()
        assert hasattr(app, "action_quit")

    def test_app_has_quit_chat(self) -> None:
        app = SafariWriterApp()
        assert hasattr(app, "quit_chat")

    def test_app_has_quit_dos(self) -> None:
        app = SafariWriterApp()
        assert hasattr(app, "quit_dos")

    def test_app_has_quit_fed(self) -> None:
        app = SafariWriterApp()
        assert hasattr(app, "quit_fed")

    def test_app_has_quit_repl(self) -> None:
        app = SafariWriterApp()
        assert hasattr(app, "quit_repl")
