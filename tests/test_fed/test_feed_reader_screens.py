"""Textual screen tests for the Safari Feed OPML browser."""

from __future__ import annotations

import asyncio

from textual.app import App
from textual.widgets import ListView

from safari_fed.feed_state import FeedRecord, SafariFeedState
from safari_fed.screens import (
    SafariFedMainScreen,
    SafariFeedListScreen,
    SafariFeedReaderScreen,
)


class FeedScreenApp(App[None]):
    """Minimal app harness for Safari Feed screen tests."""

    def __init__(self, state: SafariFeedState) -> None:
        super().__init__()
        self._state = state

    def on_mount(self) -> None:
        self.push_screen(SafariFedMainScreen(self._state))


def test_opml_screen_selects_first_item_and_opens_with_enter(tmp_path):
    opml_path = tmp_path / "feeds.opml"
    opml_path.write_text(
        """<?xml version="1.0"?>
        <opml version="2.0"><body>
          <outline text="Example" xmlUrl="https://example.com/feed.xml" />
        </body></opml>""",
        encoding="utf-8",
    )

    async def run() -> None:
        app = FeedScreenApp(SafariFeedState(config_dir=tmp_path))
        async with app.run_test() as pilot:
            await pilot.pause()
            assert isinstance(app.screen, SafariFedMainScreen)
            list_view = app.screen.query_one("#feed-opml-list", ListView)
            assert list_view.has_focus
            assert list_view.index == 0
            await pilot.press("enter")
            await pilot.pause()
            assert isinstance(app.screen, SafariFeedListScreen)

    asyncio.run(run())


def test_opml_screen_opens_first_item_with_number_key(tmp_path):
    opml_path = tmp_path / "feeds.opml"
    opml_path.write_text(
        """<?xml version="1.0"?>
        <opml version="2.0"><body>
          <outline text="Example" xmlUrl="https://example.com/feed.xml" />
        </body></opml>""",
        encoding="utf-8",
    )

    async def run() -> None:
        app = FeedScreenApp(SafariFeedState(config_dir=tmp_path))
        async with app.run_test() as pilot:
            await pilot.pause()
            assert isinstance(app.screen, SafariFedMainScreen)
            await pilot.press("1")
            await pilot.pause()
            assert isinstance(app.screen, SafariFeedListScreen)

    asyncio.run(run())


def test_feed_list_arrow_keys_move_selection(tmp_path):
    state = SafariFeedState(config_dir=tmp_path)
    state.feeds = [
        FeedRecord(title="First", xml_url="https://example.com/1.xml"),
        FeedRecord(title="Second", xml_url="https://example.com/2.xml"),
        FeedRecord(title="Third", xml_url="https://example.com/3.xml"),
    ]

    class FeedListApp(App[None]):
        def on_mount(self) -> None:
            self.push_screen(SafariFeedListScreen(state))

    async def run() -> None:
        app = FeedListApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, SafariFeedListScreen)
            list_view = screen.query_one("#feed-list", ListView)
            assert list_view.index == 0
            await pilot.press("down")
            await pilot.pause()
            assert list_view.index == 1
            await pilot.press("up")
            await pilot.pause()
            assert list_view.index == 0

    asyncio.run(run())


def test_feed_list_accepts_multi_digit_selection(tmp_path):
    state = SafariFeedState(config_dir=tmp_path)
    state.feeds = [
        FeedRecord(title=f"Feed {index}", xml_url=f"https://example.com/{index}.xml")
        for index in range(1, 26)
    ]

    class FeedListApp(App[None]):
        def on_mount(self) -> None:
            self.push_screen(SafariFeedListScreen(state))

    async def run() -> None:
        app = FeedListApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            assert isinstance(app.screen, SafariFeedListScreen)
            await pilot.press("2")
            await pilot.press("0")
            await asyncio.sleep(0.5)
            await pilot.pause()
            assert isinstance(app.screen, SafariFeedReaderScreen)
            assert state.current_feed_index == 19

    asyncio.run(run())
