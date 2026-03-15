"""Tests for Safari Fed."""

from __future__ import annotations

import asyncio
import importlib

from textual.widgets import Static

import safari_fed
from safari_fed.app import SafariFedApp, build_fed_state
from safari_fed.client import (FedSyncResult, SafariFedClient,
                               load_client_from_env, load_clients_from_env)
from safari_fed.config import load_default_identity, load_mastodon_identities
from safari_fed.main import main as safari_fed_main
from safari_fed.main import parse_args
from safari_fed.opml import (DEFAULT_MAX_ACCOUNTS, DEFAULT_MAX_FEEDS,
                             WebDocument, build_opml_document,
                             export_followed_feeds_to_opml)
from safari_fed.screens import SafariFedMainScreen
from safari_fed.state import (FedPost, SafariFedExitRequest, build_demo_state,
                              render_post_for_writer)
from safari_writer.app import SafariWriterApp


def test_public_exports_are_explicit():
    expected = {
        "FedPost",
        "FeedSubscription",
        "SafariFedApp",
        "SafariFedClient",
        "SafariFedExitRequest",
        "SafariFedState",
        "build_demo_state",
        "build_opml_document",
        "build_parser",
        "default_opml_export_path",
        "export_followed_feeds_to_opml",
        "load_default_identity",
        "load_clients_from_env",
        "main",
        "parse_args",
        "render_post_for_writer",
        "render_thread_for_writer",
    }

    assert expected.issubset(set(safari_fed.__all__))


def test_parse_args_supports_optional_folder():
    args = parse_args(["--folder", "Mentions"])

    assert args.folder == "Mentions"


def test_parse_args_supports_account_selection():
    args = parse_args(["--folder", "Mentions", "--account", "ART"])

    assert args.folder == "Mentions"
    assert args.account == "ART"


def test_parse_args_supports_export_opml_command():
    args = parse_args(["export-opml", "--account", "ART"])

    assert args.command == "export-opml"
    assert args.account == "ART"
    assert args.max_accounts == DEFAULT_MAX_ACCOUNTS
    assert args.max_feeds == DEFAULT_MAX_FEEDS


def test_load_mastodon_identities_supports_multi_identity_pattern():
    identities = load_mastodon_identities(
        {
            "MASTODON_ID_MAIN_BASE_URL": "https://mastodon.social",
            "MASTODON_ID_MAIN_ACCESS_TOKEN": "main-token",
            "MASTODON_ID_ART_BASE_URL": "https://mastodon.art",
            "MASTODON_ID_ART_ACCESS_TOKEN": "art-token",
        }
    )

    assert sorted(identities) == ["ART", "MAIN"]
    assert identities["MAIN"].base_url == "https://mastodon.social"


def test_load_default_identity_prefers_main():
    identity = load_default_identity(
        {
            "MASTODON_ID_MAIN_BASE_URL": "https://mastodon.social",
            "MASTODON_ID_MAIN_ACCESS_TOKEN": "main-token",
            "MASTODON_ID_ALT_BASE_URL": "https://example.social",
            "MASTODON_ID_ALT_ACCESS_TOKEN": "alt-token",
        }
    )

    assert identity is not None
    assert identity.name == "MAIN"


def test_load_client_from_env_returns_none_without_credentials(monkeypatch):
    monkeypatch.setattr("safari_fed.client.load_default_identity", lambda: None)

    assert load_client_from_env() is None


def test_load_clients_from_env_returns_clients_and_default(monkeypatch):
    main_identity = load_default_identity(
        {
            "MASTODON_ID_MAIN_BASE_URL": "https://mastodon.social",
            "MASTODON_ID_MAIN_ACCESS_TOKEN": "main-token",
        }
    )
    art_identity = load_default_identity(
        {
            "MASTODON_ID_ART_BASE_URL": "https://mastodon.art",
            "MASTODON_ID_ART_ACCESS_TOKEN": "art-token",
        }
    )
    assert main_identity is not None
    assert art_identity is not None
    identities = {"ART": art_identity, "MAIN": main_identity}

    class FakeClient:
        def __init__(self, identity) -> None:
            self.identity = identity

    monkeypatch.setattr(
        "safari_fed.client.load_mastodon_identities", lambda: identities
    )
    monkeypatch.setattr(
        "safari_fed.client.load_default_identity", lambda: identities["MAIN"]
    )
    monkeypatch.setattr("safari_fed.client.SafariFedClient", FakeClient)

    clients, default_name = load_clients_from_env()

    assert sorted(clients) == ["ART", "MAIN"]
    assert default_name == "MAIN"
    assert clients["ART"].identity.base_url == "https://mastodon.art"


def test_build_demo_state_can_start_in_requested_folder():
    state = build_demo_state(start_folder="Bookmarks")

    assert state.current_folder == "Bookmarks"
    assert state.visible_posts()


def test_build_fed_state_uses_demo_posts_only_without_accounts(monkeypatch):
    monkeypatch.setattr("safari_fed.app.load_clients_from_env", lambda: ({}, None))

    state = build_fed_state()

    assert state.active_account_id == "DEMO"
    assert state.visible_posts()
    assert state.account_label == "Demo packet"


def test_build_fed_state_starts_configured_account_empty_before_sync(monkeypatch):
    import safari_fed.app as fed_app

    monkeypatch.setattr(fed_app, "_load_fed_cache", lambda: {})

    class FakeClient:
        def __init__(self, label: str) -> None:
            self.identity = type("Identity", (), {"label": label})()

    state = build_fed_state(client=FakeClient("MAIN@mastodon.social"))

    assert state.active_account_id == "MAIN"
    assert state.posts == []
    assert state.visible_posts() == []
    assert state.account_label == "MAIN@mastodon.social"
    assert (
        state.status_message == "Mastodon ready: MAIN@mastodon.social (press U to sync)"
    )


def test_render_post_for_writer_contains_author_and_body():
    post = build_demo_state().posts[0]

    text = render_post_for_writer(post)

    assert post.handle in text
    assert post.content_lines[0] in text


def test_writer_menu_action_opens_safari_fed(monkeypatch):
    app = SafariWriterApp()
    pushed: list[tuple[object, object | None]] = []

    monkeypatch.setattr(
        app,
        "push_screen",
        lambda screen, callback=None, **_: pushed.append((screen, callback)),
    )

    app.handle_menu_action("safari_fed")

    assert isinstance(pushed[0][0], SafariFedMainScreen)


def test_writer_import_from_safari_fed_loads_editor_buffer(monkeypatch):
    app = SafariWriterApp()
    opened: list[object] = []

    monkeypatch.setattr(app, "_open_editor", lambda: opened.append("editor"))
    monkeypatch.setattr(app, "set_message", lambda message: None)

    app.open_in_writer_from_text("retro-thread", "line one\nline two")

    assert app.state.buffer == ["line one", "line two"]
    assert app.state.filename == ""
    assert opened == ["editor"]


def test_main_launches_writer_when_app_requests_handoff(monkeypatch, tmp_path):
    document = tmp_path / "fed-export.txt"
    document.write_text("Hello", encoding="utf-8")
    launched: list[list[str]] = []
    safari_fed_main_module = importlib.import_module("safari_fed.main")
    safari_writer_main_module = importlib.import_module("safari_writer.main")

    class FakeApp:
        def __init__(
            self,
            start_folder: str = "Home",
            start_account: str | None = None,
        ) -> None:
            self.start_folder = start_folder
            self.start_account = start_account

        def run(self):
            return SafariFedExitRequest(action="open-in-writer", document_path=document)

    monkeypatch.setattr(safari_fed_main_module, "SafariFedApp", FakeApp)
    monkeypatch.setattr(
        safari_writer_main_module, "main", lambda argv: launched.append(argv) or 0
    )

    exit_code = safari_fed_main(["--folder", "Mentions"])

    assert exit_code == 0
    assert launched == [["tui", "edit", "--file", str(document)]]


def test_export_followed_feeds_to_opml_scavenges_profile_links(tmp_path):
    identity = load_default_identity(
        {
            "MASTODON_ID_MAIN_BASE_URL": "https://mastodon.social",
            "MASTODON_ID_MAIN_ACCESS_TOKEN": "token",
        }
    )
    assert identity is not None

    class FakeMastodon:
        def __init__(self, **kwargs) -> None:
            self.kwargs = kwargs

        def account_verify_credentials(self):
            return {"id": "me"}

        def account_following(self, account_id: str, limit: int = 200):
            assert account_id == "me"
            return [
                {
                    "display_name": "Alice Example",
                    "acct": "alice@example.social",
                    "url": "https://alice.example/about",
                    "fields": [
                        {
                            "name": "blog",
                            "value": '<a href="https://alice.example/blog">Blog</a>',
                        }
                    ],
                    "note": "Writing at https://alice.example/blog",
                }
            ]

    pages = {
        "https://alice.example/about": WebDocument(
            url="https://alice.example/about",
            text="<html><head><title>Alice</title></head><body>about</body></html>",
            content_type="text/html",
        ),
        "https://alice.example/about/feed": WebDocument(
            url="https://alice.example/about/feed.xml",
            text='<?xml version="1.0"?><rss version="2.0"></rss>',
            content_type="application/rss+xml",
        ),
        "https://alice.example/blog": WebDocument(
            url="https://alice.example/blog",
            text=(
                '<html><head><title>Alice Blog</title>'
                '<link rel="alternate" type="application/rss+xml" '
                'href="/feed.xml"></head></html>'
            ),
            content_type="text/html",
        ),
    }

    client = SafariFedClient(identity=identity, mastodon_factory=FakeMastodon)
    output_path = tmp_path / "feeds.opml"
    subscriptions = export_followed_feeds_to_opml(
        client,
        output_path,
        fetcher=lambda url: pages.get(url),
    )

    assert len(subscriptions) == 2
    written = output_path.read_text(encoding="utf-8")
    assert "https://alice.example/about/feed.xml" in written
    assert "https://alice.example/blog" in written
    assert written.count("<outline ") == 2


def test_export_followed_feeds_to_opml_stops_at_feed_limit(tmp_path):
    identity = load_default_identity(
        {
            "MASTODON_ID_MAIN_BASE_URL": "https://mastodon.social",
            "MASTODON_ID_MAIN_ACCESS_TOKEN": "token",
        }
    )
    assert identity is not None

    class FakeMastodon:
        def __init__(self, **kwargs) -> None:
            self.kwargs = kwargs

        def account_verify_credentials(self):
            return {"id": "me"}

        def account_following(self, account_id: str, limit: int = 200):
            assert account_id == "me"
            assert limit == 100
            return [
                {"display_name": "One", "acct": "one@example", "url": "https://one.example"},
                {"display_name": "Two", "acct": "two@example", "url": "https://two.example"},
            ]

    pages = {
        "https://one.example": WebDocument(
            url="https://one.example/feed.xml",
            text='<?xml version="1.0"?><rss version="2.0"></rss>',
            content_type="application/rss+xml",
        ),
        "https://two.example": WebDocument(
            url="https://two.example/feed.xml",
            text='<?xml version="1.0"?><rss version="2.0"></rss>',
            content_type="application/rss+xml",
        ),
    }

    client = SafariFedClient(identity=identity, mastodon_factory=FakeMastodon)
    subscriptions = export_followed_feeds_to_opml(
        client,
        tmp_path / "feeds.opml",
        fetcher=lambda url: pages.get(url),
        max_accounts=100,
        max_feeds=1,
    )

    assert len(subscriptions) == 1
    assert subscriptions[0].xml_url == "https://one.example/feed.xml"


def test_export_opml_skips_mastodon_profile_feeds(tmp_path):
    """OPML export should not include Mastodon instance feeds as blog feeds."""
    identity = load_default_identity(
        {
            "MASTODON_ID_MAIN_BASE_URL": "https://mastodon.social",
            "MASTODON_ID_MAIN_ACCESS_TOKEN": "token",
        }
    )
    assert identity is not None

    class FakeMastodon:
        def __init__(self, **kwargs) -> None:
            self.kwargs = kwargs

        def account_verify_credentials(self):
            return {"id": "me"}

        def account_following(self, account_id: str, limit: int = 200):
            return [
                {
                    "display_name": "Bob Blogger",
                    "acct": "bob@mastodon.social",
                    "url": "https://mastodon.social/@bob",
                    "fields": [
                        {
                            "name": "Blog",
                            "value": '<a href="https://bob.example/blog">blog</a>',
                        }
                    ],
                },
            ]

    pages = {
        # Bob's blog has a feed link
        "https://bob.example/blog": WebDocument(
            url="https://bob.example/blog",
            text=(
                '<html><head><title>Bob Blog</title>'
                '<link rel="alternate" type="application/rss+xml" '
                'href="/feed.xml"></head></html>'
            ),
            content_type="text/html",
        ),
        # Bob's mastodon profile also has a feed (should be skipped)
        "https://mastodon.social/@bob": WebDocument(
            url="https://mastodon.social/@bob",
            text=(
                '<html><head><title>Bob on Mastodon</title>'
                '<link rel="alternate" type="application/rss+xml" '
                'href="https://mastodon.social/@bob.rss"></head></html>'
            ),
            content_type="text/html",
        ),
    }

    client = SafariFedClient(identity=identity, mastodon_factory=FakeMastodon)
    output_path = tmp_path / "feeds.opml"
    subscriptions = export_followed_feeds_to_opml(
        client,
        output_path,
        fetcher=lambda url: pages.get(url),
    )

    # Should find the blog feed, NOT the mastodon feed
    assert len(subscriptions) == 1
    assert subscriptions[0].xml_url == "https://bob.example/feed.xml"
    written = output_path.read_text(encoding="utf-8")
    assert "mastodon.social/@bob" not in written
    assert "@bob.rss" not in written


def test_export_opml_skips_unknown_mastodon_instances_dynamically(tmp_path):
    """OPML export detects unknown fediverse instances by HTML markers."""
    identity = load_default_identity(
        {
            "MASTODON_ID_MAIN_BASE_URL": "https://mastodon.social",
            "MASTODON_ID_MAIN_ACCESS_TOKEN": "token",
        }
    )
    assert identity is not None

    class FakeMastodon:
        def __init__(self, **kwargs) -> None:
            self.kwargs = kwargs

        def account_verify_credentials(self):
            return {"id": "me"}

        def account_following(self, account_id: str, limit: int = 200):
            return [
                {
                    "display_name": "Carol",
                    "acct": "carol@obscure.toot.zone",
                    # obscure.toot.zone is NOT in the known domain list
                    "url": "https://obscure.toot.zone/@carol",
                    "fields": [
                        {
                            "name": "Blog",
                            "value": '<a href="https://carol.example/blog">blog</a>',
                        }
                    ],
                },
                {
                    "display_name": "Dave",
                    "acct": "dave@my-masto.club",
                    # Custom domain that is actually a Mastodon instance
                    "fields": [
                        {
                            "name": "Site",
                            "value": '<a href="https://my-masto.club/about">site</a>',
                        }
                    ],
                },
            ]

    # The obscure.toot.zone/@carol page has Mastodon markers — should be
    # caught by the /@user path pattern (already in static check).
    # my-masto.club/about is a Mastodon "about" page with fediverse markers.
    pages = {
        "https://carol.example/blog": WebDocument(
            url="https://carol.example/blog",
            text=(
                '<html><head><title>Carol Blog</title>'
                '<link rel="alternate" type="application/rss+xml" '
                'href="/feed.xml"></head></html>'
            ),
            content_type="text/html",
        ),
        "https://my-masto.club/about": WebDocument(
            url="https://my-masto.club/about",
            text=(
                '<html><head><title>my-masto.club - Mastodon</title>'
                '<link rel="alternate" type="application/activity+json" '
                'href="/about.json">'
                '<div id="mastodon-data" data-props="{}"></div>'
                '<script id="initial-state">{"nodeinfo":"2.0"}</script>'
                '</head></html>'
            ),
            content_type="text/html",
        ),
    }

    client = SafariFedClient(identity=identity, mastodon_factory=FakeMastodon)
    output_path = tmp_path / "feeds.opml"
    subscriptions = export_followed_feeds_to_opml(
        client,
        output_path,
        fetcher=lambda url: pages.get(url),
    )

    # Carol's blog should be found; Dave's Mastodon instance page should be skipped
    assert len(subscriptions) == 1
    assert subscriptions[0].xml_url == "https://carol.example/feed.xml"
    written = output_path.read_text(encoding="utf-8")
    assert "my-masto.club" not in written


def test_export_opml_runs_fetches_concurrently(tmp_path):
    """Feed discovery fetches URLs concurrently, not sequentially."""
    import threading
    import time

    identity = load_default_identity(
        {
            "MASTODON_ID_MAIN_BASE_URL": "https://mastodon.social",
            "MASTODON_ID_MAIN_ACCESS_TOKEN": "token",
        }
    )
    assert identity is not None

    class FakeMastodon:
        def __init__(self, **kwargs) -> None:
            pass

        def account_verify_credentials(self):
            return {"id": "me"}

        def account_following(self, account_id: str, limit: int = 200):
            return [
                {
                    "display_name": f"User{i}",
                    "acct": f"user{i}@example",
                    "fields": [
                        {
                            "name": "blog",
                            "value": f'<a href="https://user{i}.example">blog</a>',
                        }
                    ],
                }
                for i in range(10)
            ]

    peak_concurrent = [0]
    current_concurrent = [0]
    lock = threading.Lock()

    def slow_fetcher(url):
        with lock:
            current_concurrent[0] += 1
            if current_concurrent[0] > peak_concurrent[0]:
                peak_concurrent[0] = current_concurrent[0]
        time.sleep(0.05)  # simulate network latency
        with lock:
            current_concurrent[0] -= 1
        # Return a feed for each user
        return WebDocument(
            url=url + "/feed.xml",
            text='<?xml version="1.0"?><rss version="2.0"></rss>',
            content_type="application/rss+xml",
        )

    client = SafariFedClient(identity=identity, mastodon_factory=FakeMastodon)
    start = time.monotonic()
    subscriptions = export_followed_feeds_to_opml(
        client,
        tmp_path / "feeds.opml",
        fetcher=slow_fetcher,
        max_feeds=10,
    )
    elapsed = time.monotonic() - start

    assert len(subscriptions) == 10
    # With 10 URLs at 50ms each, sequential would take ~500ms.
    # Concurrent should finish much faster. Allow generous margin.
    assert elapsed < 0.4, f"took {elapsed:.2f}s — looks sequential"
    # At least some fetches should have been concurrent
    assert peak_concurrent[0] >= 3, (
        f"peak concurrency was {peak_concurrent[0]} — expected parallel execution"
    )


def test_build_opml_document_renders_outline_rows():
    opml = build_opml_document([])

    assert "<opml version=\"2.0\">" in opml
    assert "<body>" in opml


def test_main_export_opml_command_writes_default_path(monkeypatch, tmp_path, capsys):
    safari_fed_main_module = importlib.import_module("safari_fed.main")

    class FakeClient:
        def __init__(self) -> None:
            self.identity = type("Identity", (), {"name": "MAIN"})()

    output_path = tmp_path / "fed-feeds-main.opml"

    monkeypatch.setattr(
        safari_fed_main_module,
        "load_clients_from_env",
        lambda: ({"MAIN": FakeClient()}, "MAIN"),
    )
    monkeypatch.setattr(
        safari_fed_main_module,
        "default_opml_export_path",
        lambda account_name: output_path,
    )
    monkeypatch.setattr(
        safari_fed_main_module,
        "export_followed_feeds_to_opml",
        lambda client, path, max_accounts, max_feeds: (
            path.write_text("<opml />", encoding="utf-8"),
            [],
            max_accounts,
            max_feeds,
        )[1],
    )

    exit_code = safari_fed_main(["export-opml"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Exported 0 feeds to" in captured.out
    assert output_path.read_text(encoding="utf-8") == "<opml />"


def test_main_export_opml_command_rejects_invalid_limits(capsys):
    exit_code = safari_fed_main(["export-opml", "--max-accounts", "0"])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "--max-accounts must be at least 1" in captured.err


def test_sync_from_api_replaces_remote_posts_and_updates_status():
    class FakeMastodon:
        def __init__(self, **kwargs) -> None:
            self.kwargs = kwargs

        def account_verify_credentials(self):
            return {"acct": "you@example.social"}

        def timeline_home(self, limit: int):
            return [
                {
                    "id": "101",
                    "content": "<p>Hello <b>world</b></p>",
                    "created_at": "2026-03-08T22:00:00+00:00",
                    "account": {
                        "display_name": "Alice",
                        "username": "alice",
                        "acct": "alice@example.social",
                    },
                    "tags": [{"name": "python"}],
                    "reblogs_count": 2,
                    "favourites_count": 3,
                    "replies_count": 1,
                    "visibility": "public",
                    "media_attachments": [],
                    "spoiler_text": "",
                }
            ]

        def bookmarks(self, limit: int):
            return []

        def notifications(self, limit: int):
            return []

    identity = load_default_identity(
        {
            "MASTODON_ID_MAIN_BASE_URL": "https://mastodon.social",
            "MASTODON_ID_MAIN_ACCESS_TOKEN": "token",
        }
    )
    assert identity is not None
    client = SafariFedClient(identity=identity, mastodon_factory=FakeMastodon)
    state = build_demo_state()
    state.client = client

    message = state.sync_from_api()

    assert "Synced 1 home" in message
    assert state.account_label == "@you@example.social"
    assert state.posts[0].handle == "@alice@example.social"
    assert state.posts[0].content_lines[0] == "Hello world"


def test_state_switches_between_account_sessions():
    class FakeClient:
        def __init__(self, label: str) -> None:
            self.identity = type("Identity", (), {"label": label})()

    state = build_demo_state()
    state.configure_accounts(
        {
            "MAIN": FakeClient("MAIN@mastodon.social"),
            "ART": FakeClient("ART@mastodon.art"),
        },
        active_account_id="MAIN",
    )
    state.create_local_post("main draft", draft=True)
    state.set_folder("Drafts")

    message = state.select_account("ART")

    assert message == "Active account: ART@mastodon.art"
    assert state.active_account_id == "ART"
    assert state.current_folder == "Home"
    assert state.visible_posts()
    assert all(post.preview_text != "main draft" for post in state.posts)

    state.select_account("MAIN")
    assert state.current_folder == "Drafts"
    assert any(post.draft for post in state.visible_posts())


def test_screen_css_uses_roomier_layout():
    assert "min-width: 140;" in SafariFedMainScreen.CSS
    assert "width: 100;" in SafariFedMainScreen.CSS


def test_default_mount_renders_safari_fed_shell():
    async def run() -> None:
        app = SafariFedApp(clients={})
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, SafariFedMainScreen)
            assert "SAFARI-FED" in screen.query_one("#fed-title", Static).content
            assert "Folders:" in screen.query_one("#fed-folders", Static).content
            assert "acct=" in screen.query_one("#fed-title", Static).content

    asyncio.run(run())


def test_shell_supports_reader_thread_and_compose_flow():
    async def run() -> None:
        app = SafariFedApp(clients={})
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("enter")
            assert "READER" in app.screen.query_one("#fed-detail-title", Static).content
            await pilot.press("t")
            assert (
                "THREAD VIEW"
                in app.screen.query_one("#fed-detail-title", Static).content
            )
            await pilot.press("c", "H", "i", "enter", "t", "h", "e", "r", "e")
            assert (
                "COMPOSE POST"
                in app.screen.query_one("#fed-detail-title", Static).content
            )
            await pilot.press("ctrl+s")
            assert app.state.current_folder == "Drafts"
            assert (
                "Draft saved locally"
                in app.screen.query_one("#fed-status", Static).content
            )

    asyncio.run(run())


def test_shell_sync_key_uses_api_client():
    class FakeClient:
        def __init__(self) -> None:
            self.identity = type("Identity", (), {"label": "MAIN@mastodon.social"})()

        def fetch_sync_result(self, limit: int = 20):
            return FedSyncResult(
                posts=[
                    FedPost(
                        post_id="900",
                        author="API User",
                        handle="@api@example.social",
                        posted_at="2026-03-08 22:00 UTC",
                        age="1m",
                        content_lines=["Fetched from API"],
                        preview_text="Fetched from API",
                        thread_title="Fetched from API",
                        thread_lines=("> @api@example.social", "  Fetched from API"),
                    )
                ],
                account_label="@api@example.social",
                last_sync_label="Last sync: @api@example.social",
                status_message="Synced 1 home, 0 mentions, 0 bookmarks, 0 notices",
            )

    async def run() -> None:
        app = SafariFedApp(client=FakeClient())
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("u")
            title = app.screen.query_one("#fed-title", Static).content
            status = app.screen.query_one("#fed-status", Static).content
            assert "@api@example.social" in title
            assert "Synced 1 home" in status

    asyncio.run(run())


def test_shell_cycles_between_accounts():
    class FakeClient:
        def __init__(self, label: str) -> None:
            self.identity = type("Identity", (), {"label": label})()

        def fetch_sync_result(self, limit: int = 20):
            raise AssertionError("sync should not run in this test")

    async def run() -> None:
        app = SafariFedApp(
            clients={
                "MAIN": FakeClient("MAIN@mastodon.social"),
                "ART": FakeClient("ART@mastodon.art"),
            },
            start_account="MAIN",
        )
        async with app.run_test() as pilot:
            await pilot.pause()
            accounts = app.screen.query_one("#fed-accounts", Static).content
            assert "[1:MAIN]" in accounts
            await pilot.press("a")
            title = app.screen.query_one("#fed-title", Static).content
            status = app.screen.query_one("#fed-status", Static).content
            assert "acct=ART@mastodon.art" in title
            assert "Active account: ART@mastodon.art" in status
            await pilot.press("1")
            title = app.screen.query_one("#fed-title", Static).content
            assert "acct=MAIN@mastodon.social" in title

    asyncio.run(run())


def test_persist_state_failure_updates_status(monkeypatch):
    screen = SafariFedMainScreen(build_demo_state())
    notifications: list[str] = []
    screen._refresh_status = lambda: None
    screen.notify = lambda message, severity="information", **_: notifications.append(
        f"{severity}:{message}"
    )

    def fail(state):
        raise OSError("disk full")

    monkeypatch.setattr("safari_fed.app.persist_fed_state", fail)

    screen._persist_state()

    assert screen.state.status_message == "Could not save Safari Fed state: disk full"
    assert notifications == ["error:Could not save Safari Fed state: disk full"]


def test_writer_open_fed_compose_loads_editor_buffer(monkeypatch):
    """Pressing 'c' in Safari Fed within the Writer app opens the editor."""
    app = SafariWriterApp()
    app.fed_state = build_demo_state()
    opened: list[object] = []

    monkeypatch.setattr(app, "_open_editor", lambda: opened.append("editor"))
    monkeypatch.setattr(app, "set_message", lambda message: None)

    app.open_fed_compose()

    assert app._fed_compose_active is True
    assert app.state.buffer == [""]
    assert opened == ["editor"]


def test_writer_open_fed_compose_reply_includes_context(monkeypatch):
    """Reply compose pre-loads quoted context from the original post."""
    app = SafariWriterApp()
    app.fed_state = build_demo_state()
    post = app.fed_state.posts[0]
    opened: list[object] = []

    monkeypatch.setattr(app, "_open_editor", lambda: opened.append("editor"))
    monkeypatch.setattr(app, "set_message", lambda message: None)

    app.open_fed_compose(reply_to_post=post, reply=True)

    assert app._fed_compose_active is True
    assert app.state.buffer[0] == f"> {post.handle}:"
    assert app.state.buffer[-1].startswith(f"@{post.author}")
    assert opened == ["editor"]


def test_writer_post_to_mastodon_sends_buffer(monkeypatch):
    """Confirming the toot preview sends the buffer content."""
    app = SafariWriterApp()
    app.fed_state = build_demo_state()
    app._fed_compose_active = True
    app.state.buffer = ["Hello Mastodon!", "Second line"]
    popped: list[bool] = []
    messages: list[str] = []

    monkeypatch.setattr(app, "pop_screen", lambda: popped.append(True))
    monkeypatch.setattr(app, "set_message", lambda msg: messages.append(msg))

    # post_to_mastodon now opens a preview screen; simulate confirming it
    app._on_toot_confirm(True)

    # pop_screen is no longer called from _on_toot_confirm (screen dismissed via callback)
    assert popped == []
    assert app._fed_compose_active is False
    assert any("queued locally" in m.lower() or "posted" in m.lower() for m in messages)


def test_writer_post_to_mastodon_cancel(monkeypatch):
    """Cancelling the toot preview does not send."""
    app = SafariWriterApp()
    app.fed_state = build_demo_state()
    app._fed_compose_active = True
    app.state.buffer = ["Hello Mastodon!"]
    popped: list[bool] = []
    messages: list[str] = []

    monkeypatch.setattr(app, "pop_screen", lambda: popped.append(True))
    monkeypatch.setattr(app, "set_message", lambda msg: messages.append(msg))

    app._on_toot_confirm(False)

    assert popped == []
    assert app._fed_compose_active is True  # unchanged
    assert any("cancel" in m.lower() for m in messages)


def test_writer_finish_fed_compose_returns_to_fed(monkeypatch):
    """Escape from editor in fed compose mode pops back to Fed screen."""
    app = SafariWriterApp()
    app._fed_compose_active = True
    popped: list[bool] = []

    monkeypatch.setattr(app, "pop_screen", lambda: popped.append(True))

    app.finish_fed_compose()

    assert app._fed_compose_active is False
    assert popped == [True]


def test_print_menu_includes_mastodon_option():
    """The Print/Export dialog includes a Mastodon posting option."""
    from safari_writer.file_types import HighlightProfile
    from safari_writer.screens.print_screen import PrintScreen

    screen = PrintScreen(HighlightProfile.SAFARI_WRITER)
    assert hasattr(screen, "on_key")


def test_command_bar_shows_compose_in_index():
    """The index command bar includes C Compose."""
    state = build_demo_state()
    screen = SafariFedMainScreen(state)
    bar = screen._render_command_bar()
    assert "C Compose" in bar
    assert "O OPML" in bar
    assert "F1 Help" in bar


def test_command_bar_shows_compose_in_reader():
    """The reader command bar includes C Compose."""
    state = build_demo_state()
    state.view_mode = "reader"
    screen = SafariFedMainScreen(state)
    bar = screen._render_command_bar()
    assert "C Compose" in bar
    assert "O OPML" in bar


def test_command_bar_shows_compose_in_thread():
    """The thread command bar includes C Compose."""
    state = build_demo_state()
    state.view_mode = "thread"
    screen = SafariFedMainScreen(state)
    bar = screen._render_command_bar()
    assert "C Compose" in bar
    assert "O OPML" in bar


def test_help_content_mentions_opml_export():
    assert "O                 Export OPML feeds" in (
        importlib.import_module("safari_fed.screens").FED_HELP_CONTENT
    )


def test_o_key_starts_opml_export(monkeypatch):
    calls: list[str] = []

    async def run() -> None:
        app = SafariFedApp(clients={})
        async with app.run_test() as pilot:
            await pilot.pause()
            monkeypatch.setattr(
                app.screen,
                "_prompt_for_opml_export",
                lambda: calls.append("opml"),
            )
            await pilot.press("o")

    asyncio.run(run())

    assert calls == ["opml"]


def test_help_screen_opens_on_f1():
    """F1 opens the help modal in Safari Fed."""
    from safari_fed.screens import FedHelpScreen

    async def run() -> None:
        app = SafariFedApp(clients={})
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("f1")
            assert isinstance(app.screen, FedHelpScreen)
            await pilot.press("escape")
            assert isinstance(app.screen, SafariFedMainScreen)

    asyncio.run(run())


def test_editor_help_bar_plain_mode_omits_formatting_codes():
    """Plain text / markdown files show ^Z Undo instead of ^B Bold etc."""
    from safari_writer.screens.editor import HELP_TEXT_PLAIN

    assert "^Z Undo" in HELP_TEXT_PLAIN
    assert "Bold" not in HELP_TEXT_PLAIN
    assert "Underline" not in HELP_TEXT_PLAIN
    assert "Elongate" not in HELP_TEXT_PLAIN


def test_editor_help_content_plain_omits_inline_formatting():
    """The plain F1 help content omits SFW-only sections."""
    from safari_writer.screens.editor import HELP_CONTENT, HELP_CONTENT_PLAIN

    assert "INLINE FORMATTING" in HELP_CONTENT
    assert "INLINE FORMATTING" not in HELP_CONTENT_PLAIN
    assert "DOCUMENT STRUCTURE" in HELP_CONTENT
    assert "DOCUMENT STRUCTURE" not in HELP_CONTENT_PLAIN
    assert "TEXTUAL FRAMEWORK" in HELP_CONTENT
    assert "TEXTUAL FRAMEWORK" in HELP_CONTENT_PLAIN


def test_editor_help_screen_accepts_custom_content():
    """HelpScreen can show custom content and title."""
    from safari_writer.screens.editor import HelpScreen

    screen = HelpScreen(title="Custom Title", content="Custom body")
    assert screen._title == "Custom Title"
    assert screen._content == "Custom body"
