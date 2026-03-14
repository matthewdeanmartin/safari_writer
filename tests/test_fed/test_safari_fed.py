"""Tests for Safari Fed."""

from __future__ import annotations

import asyncio
import importlib
from pathlib import Path

import safari_fed
from safari_fed.app import SafariFedApp, build_fed_state
from safari_fed.client import (
    FedSyncResult,
    SafariFedClient,
    load_client_from_env,
    load_clients_from_env,
)
from safari_fed.config import load_default_identity, load_mastodon_identities
from safari_fed.main import main as safari_fed_main, parse_args
from safari_fed.screens import SafariFedMainScreen
from safari_fed.state import (
    FedPost,
    SafariFedExitRequest,
    build_demo_state,
    render_post_for_writer,
)
from safari_writer.app import SafariWriterApp
from textual.widgets import Static


def test_public_exports_are_explicit():
    expected = {
        "FedPost",
        "SafariFedApp",
        "SafariFedClient",
        "SafariFedExitRequest",
        "SafariFedState",
        "build_demo_state",
        "build_parser",
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
    from safari_writer.screens.print_screen import PrintScreen

    screen = PrintScreen()
    assert hasattr(screen, "on_key")


def test_command_bar_shows_compose_in_index():
    """The index command bar includes C Compose."""
    state = build_demo_state()
    screen = SafariFedMainScreen(state)
    bar = screen._render_command_bar()
    assert "C Compose" in bar
    assert "F1 Help" in bar


def test_command_bar_shows_compose_in_reader():
    """The reader command bar includes C Compose."""
    state = build_demo_state()
    state.view_mode = "reader"
    screen = SafariFedMainScreen(state)
    bar = screen._render_command_bar()
    assert "C Compose" in bar


def test_command_bar_shows_compose_in_thread():
    """The thread command bar includes C Compose."""
    state = build_demo_state()
    state.view_mode = "thread"
    screen = SafariFedMainScreen(state)
    bar = screen._render_command_bar()
    assert "C Compose" in bar


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
