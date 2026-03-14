"""Tests for Safari Feed OPML and feed reader services."""

from __future__ import annotations

import json
from pathlib import Path

import httpx

from safari_fed.feed_state import FeedItem, FeedRecord
from safari_fed.services import (
    config_dir,
    fetch_article,
    fetch_feed,
    load_cached_article,
    parse_feed_document,
    parse_opml_document,
    render_entry_source,
    save_feed_preferences,
    scan_opml_documents,
)


def test_parse_opml_document_preserves_groups():
    feeds = parse_opml_document(
        """<?xml version="1.0"?>
        <opml version="2.0">
          <body>
            <outline text="Tech">
              <outline text="Example" title="Example Feed"
                xmlUrl="https://example.com/feed.xml"
                htmlUrl="https://example.com/" />
            </outline>
          </body>
        </opml>"""
    )

    assert len(feeds) == 1
    assert feeds[0].group == "Tech"
    assert feeds[0].title == "Example Feed"
    assert feeds[0].xml_url == "https://example.com/feed.xml"


def test_parse_feed_document_reads_rss_items():
    title, items = parse_feed_document(
        """<?xml version="1.0"?>
        <rss version="2.0">
          <channel>
            <title>Example Feed</title>
            <item>
              <guid>item-1</guid>
              <title>Hello</title>
              <link>https://example.com/post</link>
              <pubDate>Sat, 14 Mar 2026 10:00:00 GMT</pubDate>
              <description><![CDATA[<p>Body text</p>]]></description>
            </item>
          </channel>
        </rss>""",
        "https://example.com/feed.xml",
    )

    assert title == "Example Feed"
    assert len(items) == 1
    assert items[0].item_id == "item-1"
    assert items[0].title == "Hello"


def test_fetch_feed_populates_items():
    def fake_get(url: str) -> httpx.Response:
        return httpx.Response(
            200,
            text=(
                """<?xml version="1.0"?>
                <rss version="2.0"><channel><title>Example</title>
                <item><guid>a</guid><title>One</title><link>https://example.com/1</link>
                <description><![CDATA[<p>Alpha</p>]]></description></item>
                </channel></rss>"""
            ),
            request=httpx.Request("GET", url),
        )

    feed = FeedRecord(title="Stub", xml_url="https://example.com/feed.xml")
    fetch_feed(feed, fetcher=fake_get)

    assert feed.title == "Example"
    assert feed.fetch_status == "ONLINE"
    assert feed.items[0].title == "One"


def test_fetch_article_caches_result(monkeypatch, tmp_path):
    monkeypatch.setattr("safari_fed.services.config_dir", lambda: tmp_path)
    monkeypatch.setattr(
        "safari_fed.services.article_cache_dir",
        lambda: tmp_path / "cache",
    )

    def fake_get(url: str) -> httpx.Response:
        return httpx.Response(
            200,
            text="<html><head><title>Fetched</title></head><body><h1>Fetched</h1><p>Hello</p></body></html>",
            request=httpx.Request("GET", url),
        )

    item = FeedItem(item_id="x", title="Hello", link="https://example.com/post")
    article = fetch_article(item, fetcher=fake_get)

    cached = load_cached_article("https://example.com/post")
    assert article.title == "Fetched"
    assert "Hello" in article.markdown_text
    assert cached is not None
    assert cached.status == "CACHED"


def test_render_entry_source_supports_feed_and_fetched():
    item = FeedItem(
        item_id="x",
        title="Hello",
        link="https://example.com/post",
        summary_html="<p>Feed body</p>",
    )

    assert "Feed body" in render_entry_source(item, "FEED", "MD")
    assert render_entry_source(item, "FETCHED", "MD") == "NO FETCHED ARTICLE CACHED"


def test_scan_opml_documents_counts_feeds(tmp_path):
    opml = tmp_path / "feeds.opml"
    opml.write_text(
        """<?xml version="1.0"?>
        <opml version="2.0"><body>
          <outline text="Example" xmlUrl="https://example.com/feed.xml" />
        </body></opml>""",
        encoding="utf-8",
    )

    documents = scan_opml_documents(tmp_path)

    assert len(documents) == 1
    assert documents[0].feed_count == 1


def test_feed_preferences_round_trip(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "safari_fed.services.feed_state_path",
        lambda: tmp_path / "state.json",
    )

    payload = {"render_mode": "ANSI", "read_items": {"abc": True}}
    save_feed_preferences(payload)

    assert json.loads((tmp_path / "state.json").read_text(encoding="utf-8")) == payload


def test_config_dir_uses_expanded_override(monkeypatch, tmp_path):
    monkeypatch.setenv("SAFARI_WRITER_CONFIG_DIR", str(Path("~") / "custom-fed"))
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.delenv("APPDATA", raising=False)

    resolved = config_dir()

    assert resolved == tmp_path / "custom-fed"
    assert resolved.is_dir()


def test_config_dir_prefers_xdg_config_home(monkeypatch, tmp_path):
    monkeypatch.delenv("SAFARI_WRITER_CONFIG_DIR", raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    monkeypatch.delenv("APPDATA", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))

    resolved = config_dir()

    assert resolved == tmp_path / ".config" / "safari_writer"
    assert resolved.is_dir()
