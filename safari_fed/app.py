"""Standalone Textual app for Safari Fed."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from textual.app import App

from safari_fed.client import SafariFedClient, load_clients_from_env
from safari_fed.screens import SafariFedMainScreen
from safari_fed.state import (
    FedPost,
    SafariFedExitRequest,
    SafariFedState,
    build_demo_state,
)

__all__ = ["SafariFedApp"]


def _fed_cache_path() -> Path:
    cfg = Path.home() / ".config" / "safari_writer"
    cfg.mkdir(parents=True, exist_ok=True)
    return cfg / "fed_cache.json"


def _load_fed_cache() -> dict:
    path = _fed_cache_path()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _save_fed_cache(data: dict) -> None:
    _fed_cache_path().write_text(json.dumps(data, indent=2), encoding="utf-8")


def _posts_to_cache(posts: list[FedPost]) -> list[dict]:
    """Serialize a list of FedPost objects to JSON-safe dicts."""
    result = []
    for post in posts:
        result.append(
            {
                "post_id": post.post_id,
                "author": post.author,
                "handle": post.handle,
                "posted_at": post.posted_at,
                "age": post.age,
                "content_lines": post.content_lines,
                "preview_text": post.preview_text,
                "thread_title": post.thread_title,
                "thread_lines": list(post.thread_lines),
                "boosts": post.boosts,
                "favourites": post.favourites,
                "replies": post.replies,
                "tags": list(post.tags),
                "flags": list(post.flags),
                "attachments": list(post.attachments),
                "visibility": post.visibility,
                "cw": post.cw,
                "unread": post.unread,
                "bookmarked": post.bookmarked,
                "mention": post.mention,
                "direct": post.direct,
                "draft": post.draft,
                "sent": post.sent,
                "deferred": post.deferred,
            }
        )
    return result


def _posts_from_cache(data: list) -> list[FedPost]:
    """Deserialize cached post dicts back to FedPost objects."""
    posts = []
    for item in data:
        if not isinstance(item, dict):
            continue
        try:
            posts.append(
                FedPost(
                    post_id=item.get("post_id", ""),
                    author=item.get("author", ""),
                    handle=item.get("handle", ""),
                    posted_at=item.get("posted_at", ""),
                    age=item.get("age", ""),
                    content_lines=item.get("content_lines", []),
                    preview_text=item.get("preview_text", ""),
                    thread_title=item.get("thread_title", ""),
                    thread_lines=tuple(item.get("thread_lines", [])),
                    boosts=item.get("boosts", 0),
                    favourites=item.get("favourites", 0),
                    replies=item.get("replies", 0),
                    tags=tuple(item.get("tags", [])),
                    flags=tuple(item.get("flags", [])),
                    attachments=tuple(item.get("attachments", [])),
                    visibility=item.get("visibility", "Public"),
                    cw=item.get("cw", "none"),
                    unread=item.get("unread", True),
                    bookmarked=item.get("bookmarked", False),
                    mention=item.get("mention", False),
                    direct=item.get("direct", False),
                    draft=item.get("draft", False),
                    sent=item.get("sent", False),
                    deferred=item.get("deferred", False),
                )
            )
        except Exception:
            continue
    return posts


class SafariFedApp(App[SafariFedExitRequest | None]):
    """Retro-fediverse shell with calm queue-oriented reading."""

    TITLE = "Safari Fed"
    CSS = ""

    def __init__(
        self,
        start_folder: str = "Home",
        client: SafariFedClient | None = None,
        clients: dict[str, SafariFedClient] | None = None,
        start_account: str | None = None,
    ) -> None:
        super().__init__()
        self.state = build_fed_state(
            start_folder=start_folder,
            client=client,
            clients=clients,
            start_account=start_account,
        )

    def on_mount(self) -> None:
        if os.environ.get("SAFARI_HEADLESS") == "1":
            self.exit()

        from safari_writer.themes import DEFAULT_THEME, THEMES, load_settings

        for theme in THEMES.values():
            self.register_theme(theme)
        settings = load_settings()
        saved_theme = settings.get("theme", DEFAULT_THEME)
        if saved_theme not in THEMES:
            saved_theme = DEFAULT_THEME
        self.theme = saved_theme

        self.push_screen(SafariFedMainScreen(self.state))

    def quit_fed(self) -> None:
        """Exit the standalone app."""

        self.exit()

    def open_in_writer_from_text(self, title: str, text: str) -> None:
        """Persist exported text and request a Safari Writer handoff."""

        slug = "".join(
            character.lower() if character.isalnum() else "-"
            for character in title.strip()
        ).strip("-")
        slug = "-".join(part for part in slug.split("-") if part) or "post"
        fd, raw_path = tempfile.mkstemp(
            prefix="safari-fed-",
            suffix=f"-{slug}.txt",
        )
        path = Path(raw_path)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        self.exit(SafariFedExitRequest(action="open-in-writer", document_path=path))


def persist_fed_state(state: SafariFedState) -> None:
    """Save the current account selection and per-account post caches to disk."""
    cache = _load_fed_cache()
    cache["active_account_id"] = state.active_account_id
    # Save posts for each account session
    posts_by_account: dict[str, list[dict]] = {}
    for account_id, session in state.sessions.items():
        posts_by_account[account_id] = _posts_to_cache(session.posts)
    cache["posts_by_account"] = posts_by_account
    _save_fed_cache(cache)


def build_fed_state(
    start_folder: str = "Home",
    client: SafariFedClient | None = None,
    clients: dict[str, SafariFedClient] | None = None,
    start_account: str | None = None,
) -> SafariFedState:
    """Create a Safari Fed state object with optional live API client."""
    configured_clients: dict[str, SafariFedClient | None]
    # start_account=None means "use cache / env default"; explicit value overrides cache
    caller_specified_account = start_account
    active_account = start_account
    use_demo_state = False
    if clients is not None:
        if clients:
            configured_clients = {
                name: configured_client for name, configured_client in clients.items()
            }
        else:
            configured_clients = {"DEMO": None}
            active_account = "DEMO"
            use_demo_state = True
    elif client is not None:
        configured_clients = {"MAIN": client}
        active_account = active_account or "MAIN"
    else:
        loaded_clients, default_account = load_clients_from_env()
        if loaded_clients:
            configured_clients = {
                name: loaded_client for name, loaded_client in loaded_clients.items()
            }
            # Only use env default if caller didn't specify an account
            if active_account is None:
                active_account = default_account
        else:
            configured_clients = {"DEMO": None}
            active_account = "DEMO"
            use_demo_state = True

    # Load cache — restore last-selected account unless caller specified one explicitly
    cache = _load_fed_cache()
    if not use_demo_state and caller_specified_account is None:
        cached_account = cache.get("active_account_id")
        if cached_account and cached_account in configured_clients:
            active_account = cached_account

    state = (
        build_demo_state(start_folder=start_folder)
        if use_demo_state
        else SafariFedState(current_folder=start_folder)
    )
    state.configure_accounts(configured_clients, active_account_id=active_account)

    # Restore per-account cached posts (real accounts only, not demo)
    if not use_demo_state:
        posts_by_account = cache.get("posts_by_account", {})
        for account_id, session in state.sessions.items():
            if account_id in posts_by_account:
                cached_posts = _posts_from_cache(posts_by_account[account_id])
                if cached_posts:
                    session.posts = cached_posts
        # Sync active session state (posts may have been restored)
        state._restore_active_session()

    return state
