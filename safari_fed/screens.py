"""Textual screens for Safari Feed."""

from __future__ import annotations

from datetime import datetime

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.events import Key
from textual.screen import Screen
from textual.widgets import Static

from safari_fed.feed_state import FeedRecord, SafariFeedState
from safari_fed.services import (
    fetch_article,
    fetch_feed,
    load_feed_preferences,
    parse_opml_document,
    render_entry_source,
    save_feed_preferences,
    scan_opml_documents,
)

__all__ = [
    "SafariFedMainScreen",
    "SafariFeedListScreen",
    "SafariFeedReaderScreen",
]

_STATUS_BAR_STYLE = "bold reverse"
_FOOTER_STYLE = "reverse"
_FEED_SCREEN_CSS = """
SafariFedMainScreen,
SafariFeedListScreen,
SafariFeedReaderScreen {
    align: center middle;
}

#feed-library-summary,
#feed-library-status,
#feed-list-status,
#feed-reader-status {
    height: 1;
}

#feed-opml-list,
#feed-list {
    height: 1fr;
}

#feed-reader-body {
    height: 1fr;
    layout: horizontal;
}

#feed-reader-index {
    width: 44;
    min-width: 32;
    height: 1fr;
    padding: 0 1;
}

#feed-reader-detail {
    width: 1fr;
    height: 1fr;
    padding: 0 1;
}
"""


class SafariFedMainScreen(Screen[None]):
    """OPML library screen for Safari Feed."""

    CSS = _FEED_SCREEN_CSS

    BINDINGS = [
        Binding("up", "cursor_up", "Up", show=False),
        Binding("down", "cursor_down", "Down", show=False),
        Binding("enter", "open_selected", "Open", show=False),
        Binding("r", "rescan", "Rescan", show=False),
        Binding("q", "go_back", "Back", show=False),
        Binding("escape", "go_back", "Back", show=False),
        Binding("h", "help_screen", "Help", show=False),
    ]

    def __init__(self, state: SafariFeedState) -> None:
        super().__init__()
        self.state = state
        self._selected_index = 0
        self._digit_buffer = ""
        self._digit_timer = None
        if not self.state.opml_documents:
            self.state.opml_documents = scan_opml_documents(self.state.config_dir)

    def compose(self) -> ComposeResult:
        config_dir = self.state.config_dir
        yield Static(
            f"[{_STATUS_BAR_STYLE}]  SAFARI FEED — OPML LIBRARY  [/{_STATUS_BAR_STYLE}]"
        )
        yield Static("", id="feed-library-summary")
        if not self.state.opml_documents:
            yield Static(
                f"  No OPML files found in {config_dir}\n"
                "  Drop one or more *.opml files there, then press R to rescan."
            )
        yield Static("", id="feed-opml-list")
        yield Static("", id="feed-library-status")
        yield Static(
            f"[{_FOOTER_STYLE}]  Up/Down=Move  Enter=Open  R=Rescan  Q=Back  H=Help  [/{_FOOTER_STYLE}]"
        )

    def on_mount(self) -> None:
        self._refresh_documents()

    def _refresh_documents(self) -> None:
        self.state.opml_documents = scan_opml_documents(self.state.config_dir)
        self.query_one("#feed-library-summary", Static).update(
            f"  Files: {len(self.state.opml_documents)}   Refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        self.query_one("#feed-library-status", Static).update(
            f"  {self.state.status_message}"
        )
        self._render_list()

    def _render_list(self) -> None:
        if not self.state.opml_documents:
            self.query_one("#feed-opml-list", Static).update("")
            return
        lines: list[str] = []
        for index, document in enumerate(self.state.opml_documents):
            line = (
                f"  {index + 1:>3}. {document.filename:<30}"
                f" {document.modified_label:<16} {document.feed_count:>4} feeds"
            )
            if index == self._selected_index:
                line = f"[reverse]{line}[/reverse]"
            lines.append(line)
        self.query_one("#feed-opml-list", Static).update("\n".join(lines))

    def _clamp_index(self) -> None:
        count = len(self.state.opml_documents)
        if count == 0:
            self._selected_index = 0
        else:
            self._selected_index = max(0, min(self._selected_index, count - 1))

    def _selected_document(self):
        if 0 <= self._selected_index < len(self.state.opml_documents):
            return self.state.opml_documents[self._selected_index]
        return None

    def action_cursor_up(self) -> None:
        if self._selected_index > 0:
            self._selected_index -= 1
            self._render_list()

    def action_cursor_down(self) -> None:
        if self._selected_index < len(self.state.opml_documents) - 1:
            self._selected_index += 1
            self._render_list()

    def _commit_digit_selection(self) -> None:
        """Apply accumulated digit buffer as a selection jump."""
        if not self._digit_buffer:
            return
        index = int(self._digit_buffer) - 1
        self._digit_buffer = ""
        self._digit_timer = None
        if 0 <= index < len(self.state.opml_documents):
            self._selected_index = index
            self._render_list()

    def on_key(self, event: Key) -> None:
        if not event.character or not event.character.isdigit():
            if self._digit_buffer:
                self._digit_buffer = ""
                if self._digit_timer is not None:
                    self._digit_timer.stop()
                    self._digit_timer = None
            return
        if event.character == "0" and not self._digit_buffer:
            return
        candidate = f"{self._digit_buffer}{event.character}"
        value = int(candidate)
        has_exact = 1 <= value <= len(self.state.opml_documents)
        has_longer_prefix = any(
            str(number).startswith(candidate)
            for number in range(1, len(self.state.opml_documents) + 1)
            if len(str(number)) > len(candidate)
        )
        if not has_exact and not has_longer_prefix:
            self._digit_buffer = ""
            return
        self._digit_buffer = candidate
        event.stop()
        event.prevent_default()
        if self._digit_timer is not None:
            self._digit_timer.stop()
        if has_exact:
            self._selected_index = value - 1
            self._render_list()
        if has_exact and not has_longer_prefix:
            self._digit_buffer = ""
            self._digit_timer = None
            return
        self._digit_timer = self.set_timer(0.8, self._commit_digit_selection)

    def action_open_selected(self) -> None:
        document = self._selected_document()
        if document is None:
            return
        self.state.current_opml = document
        text = document.path.read_text(encoding="utf-8", errors="replace")
        self.state.feeds = parse_opml_document(text)
        self.state.current_feed_index = 0
        self.state.current_item_index = 0
        self.app.push_screen(SafariFeedListScreen(self.state))

    def action_rescan(self) -> None:
        self.state.status_message = "OPML library rescanned"
        self._refresh_documents()
        self.app.pop_screen()
        self.app.push_screen(SafariFedMainScreen(self.state))

    def action_help_screen(self) -> None:
        self.notify("Safari Feed: browse OPML, fetch feeds, read calmly.")

    def action_go_back(self) -> None:
        if hasattr(self.app, "quit_fed"):
            self.app.quit_fed()
        else:
            self.app.pop_screen()


class SafariFeedListScreen(Screen[None]):
    """Feed list inside a selected OPML document."""

    CSS = _FEED_SCREEN_CSS

    BINDINGS = [
        Binding("up", "cursor_up", "Up", show=False),
        Binding("down", "cursor_down", "Down", show=False),
        Binding("enter", "open_feed", "Open Feed", show=False),
        Binding("f", "fetch_current", "Fetch", show=False),
        Binding("a", "fetch_all", "Fetch All", show=False),
        Binding("r", "refresh_list", "Refresh List", show=False),
        Binding("q", "go_back", "Back", show=False),
        Binding("escape", "go_back", "Back", show=False),
    ]

    def __init__(self, state: SafariFeedState) -> None:
        super().__init__()
        self.state = state
        self._selected_index = state.current_feed_index
        self._digit_buffer = ""
        self._digit_timer = None

    def compose(self) -> ComposeResult:
        title = self.state.current_opml.filename if self.state.current_opml else "OPML"
        yield Static(f"[{_STATUS_BAR_STYLE}]  FEEDS — {title}  [/{_STATUS_BAR_STYLE}]")
        if not self.state.feeds:
            yield Static("  No feeds in this OPML file.")
        yield Static("", id="feed-list")
        yield Static(f"  {self.state.status_message}", id="feed-list-status")
        yield Static(
            f"[{_FOOTER_STYLE}]  Up/Down=Move  Enter=Open Feed  F=Fetch  A=Fetch All  R=Refresh List  Q=Back  [/{_FOOTER_STYLE}]"
        )

    def on_mount(self) -> None:
        self._clamp_index()
        self._render_list()

    def _clamp_index(self) -> None:
        count = len(self.state.feeds)
        if count == 0:
            self._selected_index = 0
        else:
            self._selected_index = max(0, min(self._selected_index, count - 1))

    def _render_list(self) -> None:
        if not self.state.feeds:
            self.query_one("#feed-list", Static).update("")
            return
        lines: list[str] = []
        for index, feed in enumerate(self.state.feeds):
            line = (
                f"  {index + 1:>3}. {feed.group[:16]:<16} {feed.title[:28]:<28}"
                f" {feed.domain[:18]:<18} {feed.unread_count:>4} unread  {feed.last_fetched or 'never':<16}"
            )
            if index == self._selected_index:
                line = f"[reverse]{line}[/reverse]"
            lines.append(line)
        self.query_one("#feed-list", Static).update("\n".join(lines))

    def action_cursor_up(self) -> None:
        if self._selected_index > 0:
            self._selected_index -= 1
            self._render_list()

    def action_cursor_down(self) -> None:
        if self._selected_index < len(self.state.feeds) - 1:
            self._selected_index += 1
            self._render_list()

    def _commit_digit_selection(self) -> None:
        """Apply accumulated digit buffer as a selection jump."""
        if not self._digit_buffer:
            return
        index = int(self._digit_buffer) - 1
        self._digit_buffer = ""
        self._digit_timer = None
        if 0 <= index < len(self.state.feeds):
            self._selected_index = index
            self._render_list()

    def on_key(self, event: Key) -> None:
        if not event.character or not event.character.isdigit():
            if self._digit_buffer:
                self._digit_buffer = ""
                if self._digit_timer is not None:
                    self._digit_timer.stop()
                    self._digit_timer = None
            return
        if event.character == "0" and not self._digit_buffer:
            return
        candidate = f"{self._digit_buffer}{event.character}"
        value = int(candidate)
        has_exact = 1 <= value <= len(self.state.feeds)
        has_longer_prefix = any(
            str(number).startswith(candidate)
            for number in range(1, len(self.state.feeds) + 1)
            if len(str(number)) > len(candidate)
        )
        if not has_exact and not has_longer_prefix:
            self._digit_buffer = ""
            return
        self._digit_buffer = candidate
        event.stop()
        event.prevent_default()
        if self._digit_timer is not None:
            self._digit_timer.stop()
        if has_exact:
            self._selected_index = value - 1
            self._render_list()
        if has_exact and not has_longer_prefix:
            self._digit_buffer = ""
            self._digit_timer = None
            return
        self._digit_timer = self.set_timer(0.8, self._commit_digit_selection)

    def _selected_feed(self) -> FeedRecord | None:
        if 0 <= self._selected_index < len(self.state.feeds):
            self.state.current_feed_index = self._selected_index
            return self.state.feeds[self._selected_index]
        return None

    def action_open_feed(self) -> None:
        feed = self._selected_feed()
        if feed is None:
            return
        self.state.current_item_index = 0
        self.app.push_screen(SafariFeedReaderScreen(self.state))

    def action_fetch_current(self) -> None:
        feed = self._selected_feed()
        if feed is None:
            return
        try:
            fetch_feed(feed)
            _apply_read_state(self.state, feed)
            self.state.status_message = f"Fetched {feed.title}"
        except Exception:
            feed.fetch_status = "ERROR"
            self.state.status_message = "FEED FETCH FAILED"
        self.app.pop_screen()
        self.app.push_screen(SafariFeedListScreen(self.state))

    def action_fetch_all(self) -> None:
        fetched = 0
        for feed in self.state.feeds:
            try:
                fetch_feed(feed)
                _apply_read_state(self.state, feed)
                fetched += 1
            except Exception:
                feed.fetch_status = "ERROR"
        self.state.status_message = f"Fetched {fetched} feed(s)"
        self.app.pop_screen()
        self.app.push_screen(SafariFeedListScreen(self.state))

    def action_refresh_list(self) -> None:
        self.state.status_message = "Feed list refreshed"
        self.app.pop_screen()
        self.app.push_screen(SafariFeedListScreen(self.state))

    def action_go_back(self) -> None:
        self.app.pop_screen()


class SafariFeedReaderScreen(Screen[None]):
    """Split-pane reader for one fetched feed."""

    CSS = _FEED_SCREEN_CSS

    BINDINGS = [
        Binding("up", "move_up", "Up", show=False),
        Binding("down", "move_down", "Down", show=False),
        Binding("enter", "read_item", "Read", show=False),
        Binding("m", "toggle_read", "Mark", show=False),
        Binding("f", "fetch_feed_again", "Fetch Feed", show=False),
        Binding("o", "fetch_article", "Fetch Article", show=False),
        Binding("t", "toggle_source", "Toggle Source", show=False),
        Binding("v", "toggle_render", "Toggle Render", show=False),
        Binding("n", "next_unread", "Next Unread", show=False),
        Binding("p", "previous_unread", "Prev Unread", show=False),
        Binding("q", "go_back", "Back", show=False),
        Binding("escape", "go_back", "Back", show=False),
    ]

    def __init__(self, state: SafariFeedState) -> None:
        super().__init__()
        self.state = state

    def compose(self) -> ComposeResult:
        yield Static("", id="feed-reader-header")
        with Horizontal(id="feed-reader-body"):
            yield Static("", id="feed-reader-index")
            yield Static("", id="feed-reader-detail")
        yield Static("", id="feed-reader-status")
        yield Static(
            f"[{_FOOTER_STYLE}]  Up/Down=Move  Enter=Read  M=Mark  F=Fetch Feed  O=Fetch Article  T=Feed/Fetched  V=Markdown/ANSI  Q=Back  [/{_FOOTER_STYLE}]"
        )

    def on_mount(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        self.state.ensure_indexes()
        feed = self.state.current_feed()
        item = self.state.current_item()
        if feed is None:
            self.query_one("#feed-reader-header", Static).update(
                f"[{_STATUS_BAR_STYLE}]  SAFARI FEED — EMPTY  [/{_STATUS_BAR_STYLE}]"
            )
            self.query_one("#feed-reader-index", Static).update("No feed selected.")
            self.query_one("#feed-reader-detail", Static).update("")
            self.query_one("#feed-reader-status", Static).update("READY")
            return
        position = self.state.current_item_index + 1 if item is not None else 0
        total = len(feed.items)
        self.query_one("#feed-reader-header", Static).update(
            f"[{_STATUS_BAR_STYLE}]  {feed.title}  {position}/{total}  "
            f"{self.state.content_source}  {self.state.render_mode}  "
            f"{feed.fetch_status or 'NEVER'}  [/{_STATUS_BAR_STYLE}]"
        )
        self.query_one("#feed-reader-index", Static).update(self._render_index(feed))
        self.query_one("#feed-reader-detail", Static).update(self._render_detail(item))
        self.query_one("#feed-reader-status", Static).update(
            f"  {self.state.status_message}"
        )

    def _render_index(self, feed: FeedRecord) -> str:
        if not feed.items:
            return "No items. Press F to fetch this feed."
        lines = [" # U Published           Title", "-" * 60]
        for index, item in enumerate(feed.items, start=1):
            unread = "*" if item.unread else " "
            published = (item.published or "")[:18]
            title = item.title[:34]
            line = f" {index:>2} {unread} {published:<18} {title}"
            if index - 1 == self.state.current_item_index:
                line = f"[reverse]{line}[/reverse]"
            lines.append(line)
        return "\n".join(lines)

    def _render_detail(self, item) -> str:
        if item is None:
            return "No article selected."
        body = render_entry_source(
            item,
            self.state.content_source,
            self.state.render_mode,
        )
        return "\n".join(
            [
                f"Title: {item.title}",
                f"Author: {item.author or '(unknown)'}",
                f"Published: {item.published or '(unknown)'}",
                f"URL: {item.link or '(none)'}",
                "-" * 72,
                body,
            ]
        )

    def action_move_up(self) -> None:
        self.state.current_item_index = max(0, self.state.current_item_index - 1)
        self._refresh()

    def action_move_down(self) -> None:
        feed = self.state.current_feed()
        if feed is None:
            return
        self.state.current_item_index = min(
            len(feed.items) - 1,
            self.state.current_item_index + 1,
        )
        self._refresh()

    def action_read_item(self) -> None:
        item = self.state.current_item()
        if item is None:
            return
        item.unread = False
        self.state.status_message = f"Reading {item.title}"
        _save_item_state(self.state)
        self._refresh()

    def action_toggle_read(self) -> None:
        item = self.state.current_item()
        if item is None:
            return
        item.unread = not item.unread
        self.state.status_message = "Marked unread" if item.unread else "Marked read"
        _save_item_state(self.state)
        self._refresh()

    def action_fetch_feed_again(self) -> None:
        feed = self.state.current_feed()
        if feed is None:
            return
        try:
            fetch_feed(feed)
            _apply_read_state(self.state, feed)
            self.state.status_message = f"Fetched {feed.title}"
        except Exception:
            feed.fetch_status = "ERROR"
            self.state.status_message = "FEED FETCH FAILED"
        self._refresh()

    def action_fetch_article(self) -> None:
        item = self.state.current_item()
        if item is None:
            return
        try:
            article = fetch_article(item)
            self.state.status_message = (
                "Article fetched"
                if article.status == "ONLINE"
                else "Fetched article loaded from cache"
            )
        except Exception:
            self.state.status_message = "ARTICLE FETCH FAILED"
        self._refresh()

    def action_toggle_source(self) -> None:
        item = self.state.current_item()
        if item is None:
            return
        if self.state.content_source == "FEED":
            if item.article is None:
                try:
                    fetch_article(item)
                except Exception:
                    self.state.status_message = "ARTICLE FETCH FAILED"
                    self._refresh()
                    return
            self.state.content_source = "FETCHED"
        else:
            self.state.content_source = "FEED"
        self.state.status_message = f"Source: {self.state.content_source}"
        _save_item_state(self.state)
        self._refresh()

    def action_toggle_render(self) -> None:
        self.state.render_mode = "ANSI" if self.state.render_mode == "MD" else "MD"
        self.state.status_message = f"Render: {self.state.render_mode}"
        _save_item_state(self.state)
        self._refresh()

    def action_next_unread(self) -> None:
        feed = self.state.current_feed()
        if feed is None:
            return
        for index in range(self.state.current_item_index + 1, len(feed.items)):
            if feed.items[index].unread:
                self.state.current_item_index = index
                self.state.status_message = "Jumped to next unread item"
                self._refresh()
                return
        self.state.status_message = "No next unread item"
        self._refresh()

    def action_previous_unread(self) -> None:
        feed = self.state.current_feed()
        if feed is None:
            return
        for index in range(self.state.current_item_index - 1, -1, -1):
            if feed.items[index].unread:
                self.state.current_item_index = index
                self.state.status_message = "Jumped to previous unread item"
                self._refresh()
                return
        self.state.status_message = "No previous unread item"
        self._refresh()

    def action_go_back(self) -> None:
        self.app.pop_screen()


def _apply_read_state(state: SafariFeedState, feed: FeedRecord) -> None:
    saved = load_feed_preferences()
    read_items = saved.get("read_items", {})
    for item in feed.items:
        item.unread = not bool(read_items.get(item.item_id))
    feed.unread_count = sum(1 for item in feed.items if item.unread)
    state.render_mode = saved.get("render_mode", state.render_mode)
    state.content_source = saved.get("content_source", state.content_source)


def _save_item_state(state: SafariFeedState) -> None:
    payload = load_feed_preferences()
    read_items = payload.setdefault("read_items", {})
    for feed in state.feeds:
        for item in feed.items:
            if not item.unread:
                read_items[item.item_id] = True
            elif item.item_id in read_items:
                del read_items[item.item_id]
        feed.unread_count = sum(1 for item in feed.items if item.unread)
    payload["render_mode"] = state.render_mode
    payload["content_source"] = state.content_source
    save_feed_preferences(payload)
