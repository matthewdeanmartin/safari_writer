"""State models for Safari Feed."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

__all__ = [
    "FeedArticle",
    "FeedItem",
    "FeedRecord",
    "FeedSource",
    "OpmlDocument",
    "RenderMode",
    "SafariFeedState",
]

FeedSource = str
RenderMode = str


@dataclass
class OpmlDocument:
    """One OPML file discovered in the Safari Feed config folder."""

    path: Path
    filename: str
    modified_label: str
    feed_count: int


@dataclass
class FeedArticle:
    """Fetched article content cached for later rereading."""

    url: str
    fetched_at: str = ""
    title: str = ""
    html: str = ""
    markdown_text: str = ""
    ansi_text: str = ""
    status: str = "NEVER"
    error: str = ""


@dataclass
class FeedItem:
    """A single RSS/Atom entry."""

    item_id: str
    title: str
    link: str
    published: str = ""
    author: str = ""
    summary_html: str = ""
    content_html: str = ""
    unread: bool = True
    article: FeedArticle | None = None


@dataclass
class FeedRecord:
    """A feed discovered inside an OPML document."""

    title: str
    xml_url: str
    html_url: str = ""
    group: str = ""
    domain: str = ""
    unread_count: int = 0
    last_fetched: str = ""
    fetch_status: str = "NEVER"
    error: str = ""
    items: list[FeedItem] = field(default_factory=list)


@dataclass
class SafariFeedState:
    """Mutable shared state for the Safari Feed reader."""

    config_dir: Path
    opml_documents: list[OpmlDocument] = field(default_factory=list)
    current_opml: OpmlDocument | None = None
    feeds: list[FeedRecord] = field(default_factory=list)
    current_feed_index: int = 0
    current_item_index: int = 0
    content_source: FeedSource = "FEED"
    render_mode: RenderMode = "MD"
    status_message: str = "READY"
    last_refresh_label: str = ""

    def current_feed(self) -> FeedRecord | None:
        if 0 <= self.current_feed_index < len(self.feeds):
            return self.feeds[self.current_feed_index]
        return None

    def current_item(self) -> FeedItem | None:
        feed = self.current_feed()
        if feed is None:
            return None
        if 0 <= self.current_item_index < len(feed.items):
            return feed.items[self.current_item_index]
        return None

    def ensure_indexes(self) -> None:
        if not self.feeds:
            self.current_feed_index = 0
            self.current_item_index = 0
            return
        self.current_feed_index = max(0, min(self.current_feed_index, len(self.feeds) - 1))
        feed = self.current_feed()
        items = feed.items if feed is not None else []
        if not items:
            self.current_item_index = 0
            return
        self.current_item_index = max(0, min(self.current_item_index, len(items) - 1))
