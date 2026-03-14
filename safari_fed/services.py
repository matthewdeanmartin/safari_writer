"""Services for Safari Feed OPML, feed parsing, caching, and rendering."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict
from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Callable
from urllib.parse import urljoin, urlparse
from xml.etree import ElementTree as ET

import httpx

from safari_fed.feed_state import FeedArticle, FeedItem, FeedRecord, OpmlDocument

__all__ = [
    "article_cache_dir",
    "config_dir",
    "feed_state_path",
    "fetch_article",
    "fetch_feed",
    "format_modified_time",
    "load_feed_preferences",
    "parse_feed_document",
    "parse_opml_document",
    "render_entry_source",
    "save_feed_preferences",
    "scan_opml_documents",
    "stable_item_key",
]

_SCRIPT_STYLE_RE = re.compile(
    r"<(script|style|noscript)\b[^>]*>.*?</\1>",
    flags=re.IGNORECASE | re.DOTALL,
)
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"[ \t]+")
_MULTI_NL_RE = re.compile(r"\n{3,}")


class _HtmlToText(HTMLParser):
    """Small HTML-to-text renderer tuned for terminal reading."""

    def __init__(self, *, rich: bool) -> None:
        super().__init__(convert_charrefs=True)
        self.rich = rich
        self.parts: list[str] = []
        self.href_stack: list[str] = []
        self.list_depth = 0
        self.in_pre = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {key: value or "" for key, value in attrs}
        if tag in {"p", "div", "section", "article", "header"}:
            self.parts.append("\n\n")
        elif tag == "br":
            self.parts.append("\n")
        elif tag == "li":
            indent = "  " * max(0, self.list_depth - 1)
            self.parts.append(f"\n{indent}- ")
        elif tag in {"ul", "ol"}:
            self.list_depth += 1
            self.parts.append("\n")
        elif tag == "blockquote":
            self.parts.append("\n> ")
        elif tag == "pre":
            self.in_pre = True
            self.parts.append("\n\n")
        elif tag == "code" and self.rich:
            self.parts.append("[italic]")
        elif tag in {"strong", "b"} and self.rich:
            self.parts.append("[bold]")
        elif tag in {"em", "i"} and self.rich:
            self.parts.append("[italic]")
        elif tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self.parts.append("\n\n")
            if self.rich:
                self.parts.append("[bold]")
        elif tag == "a":
            self.href_stack.append(attr_map.get("href", ""))

    def handle_endtag(self, tag: str) -> None:
        if tag in {"ul", "ol"} and self.list_depth > 0:
            self.list_depth -= 1
            self.parts.append("\n")
        elif tag == "pre":
            self.in_pre = False
            self.parts.append("\n\n")
        elif tag in {"code", "em", "i"} and self.rich:
            self.parts.append("[/italic]")
        elif tag in {"strong", "b"} and self.rich:
            self.parts.append("[/bold]")
        elif tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            if self.rich:
                self.parts.append("[/bold]")
            self.parts.append("\n")
        elif tag == "a":
            href = self.href_stack.pop() if self.href_stack else ""
            if href:
                self.parts.append(f" <{href}>")

    def handle_data(self, data: str) -> None:
        if self.in_pre:
            self.parts.append(data)
            return
        normalized = _WS_RE.sub(" ", data)
        self.parts.append(normalized)

    def get_text(self) -> str:
        text = "".join(self.parts)
        text = unescape(text)
        lines = [line.rstrip() for line in text.splitlines()]
        text = "\n".join(lines)
        text = _MULTI_NL_RE.sub("\n\n", text).strip()
        return text


def config_dir() -> Path:
    """Return the Safari Feed config directory."""

    path = Path.home() / ".config" / "safari_writer"
    path.mkdir(parents=True, exist_ok=True)
    return path


def feed_state_path() -> Path:
    """Return the feed-reader JSON state path."""

    return config_dir() / "safari_feed_state.json"


def article_cache_dir() -> Path:
    """Return the cache folder used for fetched article payloads."""

    path = config_dir() / "safari_feed_cache"
    path.mkdir(parents=True, exist_ok=True)
    return path


def scan_opml_documents(base_dir: Path | None = None) -> list[OpmlDocument]:
    """Discover `*.opml` files and summarize them."""

    root = base_dir or config_dir()
    documents: list[OpmlDocument] = []
    for path in sorted(root.glob("*.opml")):
        feed_count = 0
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
            feed_count = len(parse_opml_document(text))
        except OSError:
            feed_count = 0
        modified = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        documents.append(
            OpmlDocument(
                path=path,
                filename=path.name,
                modified_label=format_modified_time(modified),
                feed_count=feed_count,
            )
        )
    return documents


def format_modified_time(value: datetime) -> str:
    """Format a timestamp in a compact, stable way."""

    return value.astimezone().strftime("%Y-%m-%d %H:%M")


def parse_opml_document(text: str) -> list[FeedRecord]:
    """Parse feed outlines from an OPML document."""

    root = ET.fromstring(text)
    body = root.find("body")
    if body is None:
        return []
    records: list[FeedRecord] = []

    def _walk(element: ET.Element, groups: list[str]) -> None:
        title = element.attrib.get("title") or element.attrib.get("text", "")
        xml_url = element.attrib.get("xmlUrl", "")
        html_url = element.attrib.get("htmlUrl", "")
        if xml_url:
            parsed = urlparse(html_url or xml_url)
            records.append(
                FeedRecord(
                    title=title or xml_url,
                    xml_url=xml_url,
                    html_url=html_url,
                    group=" / ".join(groups),
                    domain=parsed.netloc,
                )
            )
        child_groups = groups
        if not xml_url and title:
            child_groups = [*groups, title]
        for child in list(element):
            _walk(child, child_groups)

    for outline in list(body):
        _walk(outline, [])
    return records


def parse_feed_document(xml_text: str, source_url: str) -> tuple[str, list[FeedItem]]:
    """Parse RSS 2.0 or Atom feed XML."""

    root = ET.fromstring(xml_text)
    tag = _local_name(root.tag)
    if tag == "rss":
        channel = root.find("channel")
        if channel is None:
            return ("Untitled Feed", [])
        title = _child_text(channel, "title") or source_url
        items = [_parse_rss_item(node) for node in channel.findall("item")]
        return (title, items)
    if tag == "feed":
        title = _child_text(root, "title") or source_url
        items = [_parse_atom_entry(node) for node in _children_named(root, "entry")]
        return (title, items)
    return (source_url, [])


def _parse_rss_item(node: ET.Element) -> FeedItem:
    guid = _child_text(node, "guid")
    link = _child_text(node, "link")
    title = _child_text(node, "title") or "(untitled)"
    published = _child_text(node, "pubDate")
    author = _child_text(node, "author") or _child_text(node, "creator")
    summary = _child_text(node, "description")
    content = _child_text(node, "encoded") or summary
    return FeedItem(
        item_id=guid or stable_item_key(link, title, published),
        title=title,
        link=link,
        published=published,
        author=author,
        summary_html=summary,
        content_html=content,
    )


def _parse_atom_entry(node: ET.Element) -> FeedItem:
    item_id = _child_text(node, "id")
    title = _child_text(node, "title") or "(untitled)"
    published = _child_text(node, "published") or _child_text(node, "updated")
    author = ""
    author_node = _child_named(node, "author")
    if author_node is not None:
        author = _child_text(author_node, "name")
    link = ""
    for link_node in _children_named(node, "link"):
        rel = link_node.attrib.get("rel", "alternate")
        href = link_node.attrib.get("href", "")
        if rel == "alternate" and href:
            link = href
            break
        if not link and href:
            link = href
    summary = _child_text(node, "summary")
    content = _child_text(node, "content") or summary
    return FeedItem(
        item_id=item_id or stable_item_key(link, title, published),
        title=title,
        link=link,
        published=published,
        author=author,
        summary_html=summary,
        content_html=content,
    )


def stable_item_key(link: str, title: str, published: str) -> str:
    """Build a stable item identifier fallback."""

    if link:
        return link
    digest = hashlib.sha1(f"{title}|{published}".encode("utf-8")).hexdigest()
    return digest


def fetch_feed(
    feed: FeedRecord,
    *,
    fetcher: Callable[[str], httpx.Response] | None = None,
) -> FeedRecord:
    """Fetch and parse a feed on demand."""

    getter = fetcher or _default_get
    response = getter(feed.xml_url)
    response.raise_for_status()
    title, items = parse_feed_document(response.text, feed.xml_url)
    feed.title = title or feed.title
    feed.items = items
    feed.last_fetched = _now_label()
    feed.fetch_status = "ONLINE"
    feed.error = ""
    return feed


def fetch_article(
    item: FeedItem,
    *,
    fetcher: Callable[[str], httpx.Response] | None = None,
) -> FeedArticle:
    """Fetch an article body for one feed item and cache it."""

    cached = load_cached_article(item.link)
    if cached is not None:
        item.article = cached
        return cached
    if not item.link:
        article = FeedArticle(url="", status="ERROR", error="NO ARTICLE URL")
        item.article = article
        return article
    getter = fetcher or _default_get
    response = getter(item.link)
    response.raise_for_status()
    html = response.text
    title = _extract_title(html) or item.title
    markdown_text = html_to_terminal_text(html, base_url=item.link, rich=False)
    ansi_text = html_to_terminal_text(html, base_url=item.link, rich=True)
    article = FeedArticle(
        url=item.link,
        fetched_at=_now_label(),
        title=title,
        html=html,
        markdown_text=markdown_text,
        ansi_text=ansi_text,
        status="ONLINE",
    )
    save_cached_article(article)
    item.article = article
    return article


def render_entry_source(item: FeedItem, source: str, render_mode: str) -> str:
    """Render the chosen item source into terminal text."""

    rich = render_mode.upper() == "ANSI"
    if source.upper() == "FETCHED":
        if item.article is None:
            return "NO FETCHED ARTICLE CACHED"
        if rich:
            return item.article.ansi_text or "NO FETCHED ARTICLE CACHED"
        return item.article.markdown_text or "NO FETCHED ARTICLE CACHED"
    html = item.content_html or item.summary_html
    if not html:
        return "NO FEED BODY AVAILABLE"
    return html_to_terminal_text(html, base_url=item.link, rich=rich)


def html_to_terminal_text(html: str, *, base_url: str, rich: bool) -> str:
    """Convert sanitized HTML to readable terminal text."""

    cleaned = _sanitize_html(html, base_url=base_url)
    parser = _HtmlToText(rich=rich)
    parser.feed(cleaned)
    text = parser.get_text()
    return text or "NO BODY AVAILABLE"


def _sanitize_html(html: str, *, base_url: str) -> str:
    html = _SCRIPT_STYLE_RE.sub("", html)
    html = re.sub(
        r'href=["\']([^"\':#?][^"\']*)["\']',
        lambda match: f'href="{urljoin(base_url, match.group(1))}"',
        html,
        flags=re.IGNORECASE,
    )
    html = re.sub(
        r'src=["\']([^"\':#?][^"\']*)["\']',
        lambda match: f'src="{urljoin(base_url, match.group(1))}"',
        html,
        flags=re.IGNORECASE,
    )
    return html


def load_feed_preferences() -> dict:
    """Load persisted read-state and reader preferences."""

    path = feed_state_path()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def save_feed_preferences(data: dict) -> None:
    """Persist read-state and reader preferences."""

    feed_state_path().write_text(json.dumps(data, indent=2), encoding="utf-8")


def save_cached_article(article: FeedArticle) -> None:
    """Persist one fetched article to disk."""

    if not article.url:
        return
    cache_path = article_cache_dir() / f"{_hash_url(article.url)}.json"
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(asdict(article), indent=2), encoding="utf-8")


def load_cached_article(url: str) -> FeedArticle | None:
    """Load one cached article if present."""

    if not url:
        return None
    cache_path = article_cache_dir() / f"{_hash_url(url)}.json"
    if not cache_path.exists():
        return None
    try:
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    article = FeedArticle(**payload)
    if article.status == "ONLINE":
        article.status = "CACHED"
    return article


def _hash_url(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()


def _default_get(url: str) -> httpx.Response:
    return httpx.get(
        url,
        timeout=20,
        follow_redirects=True,
        headers={"User-Agent": "Safari Feed/0.1"},
    )


def _extract_title(html: str) -> str:
    match = re.search(
        r"<title[^>]*>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL
    )
    if not match:
        return ""
    return _TAG_RE.sub("", match.group(1)).strip()


def _now_label() -> str:
    return datetime.now(tz=timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M")


def _child_text(node: ET.Element, name: str) -> str:
    child = _child_named(node, name)
    if child is None:
        return ""
    return "".join(child.itertext()).strip()


def _child_named(node: ET.Element, name: str) -> ET.Element | None:
    for child in list(node):
        if _local_name(child.tag) == name:
            return child
    return None


def _children_named(node: ET.Element, name: str) -> list[ET.Element]:
    return [child for child in list(node) if _local_name(child.tag) == name]


def _local_name(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", maxsplit=1)[-1]
    if ":" in tag:
        return tag.rsplit(":", maxsplit=1)[-1]
    return tag
