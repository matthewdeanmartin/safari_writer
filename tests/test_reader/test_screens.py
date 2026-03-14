"""Textual screen tests for Safari Reader."""

from __future__ import annotations

import asyncio

from textual.widgets import ListView, Static

from safari_reader.app import SafariReaderApp
from safari_reader.screens import SafariReaderCatalogScreen, SafariReaderMainMenuScreen
from safari_reader.state import BookMeta


def test_main_menu_renders_three_columns_and_current_book(tmp_path):
    async def run() -> None:
        app = SafariReaderApp(library_dir=tmp_path / "library")
        app.state.current_book = BookMeta(title="Treasure Island", progress_percent=42)

        async with app.run_test() as pilot:
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, SafariReaderMainMenuScreen)
            screen.query_one("#reader-menu-col-1")
            screen.query_one("#reader-menu-col-2")
            screen.query_one("#reader-menu-col-3")
            context = screen.query_one("#reader-context-bar", Static).content
            assert "Current Book: Treasure Island" in context

    asyncio.run(run())


def test_catalog_list_accepts_arrow_navigation(tmp_path):
    async def run() -> None:
        app = SafariReaderApp(library_dir=tmp_path / "library")
        app.state.catalog_results = [
            {"id": "1", "title": "First Book", "author": "Alpha", "download_count": "10"},
            {"id": "2", "title": "Second Book", "author": "Beta", "download_count": "20"},
            {"id": "3", "title": "Third Book", "author": "Gamma", "download_count": "30"},
        ]

        async with app.run_test() as pilot:
            await pilot.pause()
            app.push_screen(SafariReaderCatalogScreen(app.state))
            await pilot.pause()
            screen = app.screen
            list_view = screen.query_one("#catalog-list", ListView)
            assert list_view.has_focus
            start_index = list_view.index
            await pilot.press("down")
            await pilot.press("down")
            assert list_view.index is not None
            assert start_index is not None
            assert list_view.index > start_index

    asyncio.run(run())
