"""Standalone Textual app for Safari Fed."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from textual.app import App

from safari_fed.client import SafariFedClient, load_clients_from_env
from safari_fed.screens import SafariFedMainScreen
from safari_fed.state import SafariFedExitRequest, SafariFedState, build_demo_state

__all__ = ["SafariFedApp"]


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


def build_fed_state(
    start_folder: str = "Home",
    client: SafariFedClient | None = None,
    clients: dict[str, SafariFedClient] | None = None,
    start_account: str | None = None,
) -> SafariFedState:
    """Create a Safari Fed state object with optional live API client."""
    configured_clients: dict[str, SafariFedClient | None]
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
            active_account = active_account or default_account
        else:
            configured_clients = {"DEMO": None}
            active_account = "DEMO"
            use_demo_state = True
    state = (
        build_demo_state(start_folder=start_folder)
        if use_demo_state
        else SafariFedState(current_folder=start_folder)
    )
    state.configure_accounts(configured_clients, active_account_id=active_account)
    return state
