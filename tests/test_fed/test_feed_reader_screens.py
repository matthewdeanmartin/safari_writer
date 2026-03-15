"""Textual screen tests for the Safari Feed OPML browser."""

from __future__ import annotations

import asyncio

from textual.app import App

from safari_fed.feed_state import FeedRecord, SafariFeedState
from safari_fed.screens import (
    SafariFeedMainScreen,
    SafariFeedListScreen,
    SafariFeedReaderScreen,
)


class FeedScreenApp(App[None]):
    """Minimal app harness for Safari Feed screen tests."""

    def __init__(self, state: SafariFeedState) -> None:
        super().__init__()
        self._state = state

    def on_mount(self) -> None:
        self.push_screen(SafariFeedMainScreen(self._state))


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
            assert isinstance(app.screen, SafariFeedMainScreen)
            assert app.screen._selected_index == 0
            await pilot.press("enter")
            await pilot.pause()
            assert isinstance(app.screen, SafariFeedListScreen)

    asyncio.run(run())


def test_opml_screen_jumps_selection_with_number_key(tmp_path):
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
            assert isinstance(app.screen, SafariFeedMainScreen)
            # Number key jumps selection but does NOT auto-open
            await pilot.press("1")
            await pilot.pause()
            assert app.screen._selected_index == 0
            # Still on OPML screen — need Enter to open
            assert isinstance(app.screen, SafariFeedMainScreen)
            await pilot.press("enter")
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
            assert screen._selected_index == 0
            await pilot.press("down")
            await pilot.pause()
            assert screen._selected_index == 1
            await pilot.press("up")
            await pilot.pause()
            assert screen._selected_index == 0

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
            # Type "20" — should jump selection to item 20 (index 19)
            await pilot.press("2")
            await pilot.press("0")
            await asyncio.sleep(1.0)
            await pilot.pause()
            # Still on feed list — numbers only jump, don't open
            assert isinstance(app.screen, SafariFeedListScreen)
            assert app.screen._selected_index == 19
            # Enter opens the feed
            await pilot.press("enter")
            await pilot.pause()
            assert isinstance(app.screen, SafariFeedReaderScreen)
            assert state.current_feed_index == 19

    asyncio.run(run())


def test_opml_screen_arrow_keys_move_selection(tmp_path):
    """Arrow keys move the highlight on the OPML library screen."""
    for name in ("alpha.opml", "beta.opml", "gamma.opml"):
        (tmp_path / name).write_text(
            '<?xml version="1.0"?>'
            '<opml version="2.0"><body>'
            f'<outline text="{name}" xmlUrl="https://example.com/{name}" />'
            "</body></opml>",
            encoding="utf-8",
        )

    async def run() -> None:
        app = FeedScreenApp(SafariFeedState(config_dir=tmp_path))
        async with app.run_test() as pilot:
            await pilot.pause()
            assert isinstance(app.screen, SafariFeedMainScreen)
            assert app.screen._selected_index == 0
            await pilot.press("down")
            await pilot.pause()
            assert app.screen._selected_index == 1
            await pilot.press("down")
            await pilot.pause()
            assert app.screen._selected_index == 2
            await pilot.press("up")
            await pilot.pause()
            assert app.screen._selected_index == 1

    asyncio.run(run())


def test_reader_screen_uses_reverse_highlight(tmp_path):
    """Reader screen highlights the selected item with [reverse] markup."""
    state = SafariFeedState(config_dir=tmp_path)
    from safari_fed.feed_state import FeedItem

    state.feeds = [
        FeedRecord(
            title="Test Feed",
            xml_url="https://example.com/feed.xml",
            items=[
                FeedItem(item_id="1", title="First Post", link="https://example.com/1"),
                FeedItem(item_id="2", title="Second Post", link="https://example.com/2"),
            ],
        ),
    ]
    state.current_feed_index = 0
    state.current_item_index = 0

    class ReaderApp(App[None]):
        def on_mount(self) -> None:
            self.push_screen(SafariFeedReaderScreen(state))

    async def run() -> None:
        app = ReaderApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            assert isinstance(app.screen, SafariFeedReaderScreen)
            # The index pane should contain [reverse] markup for highlighting
            from textual.widgets import Static

            index_widget = app.screen.query_one("#feed-reader-index", Static)
            # The render uses Rich markup — the underlying _content should have reverse
            rendered = app.screen._render_index(state.current_feed())
            assert "[reverse]" in rendered
            assert "First Post" in rendered

    asyncio.run(run())
