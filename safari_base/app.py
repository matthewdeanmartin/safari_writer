"""Safari Base Textual application."""

from __future__ import annotations

import os
from pathlib import Path

from textual.app import App

from safari_base.database import BaseSession, ensure_database
from safari_base.screen import SafariBaseScreen
from safari_writer.themes import DEFAULT_THEME, THEMES

__all__ = ["SafariBaseApp"]


class SafariBaseApp(App[None]):
    """Minimal dBASE-style shell built on Textual."""

    TITLE = "Safari Base"
    CSS = ""

    def __init__(
        self,
        database_path: Path | None = None,
        session: BaseSession | None = None,
    ) -> None:
        super().__init__()
        self.session = session or ensure_database(database_path)

    def on_mount(self) -> None:
        if os.environ.get("SAFARI_HEADLESS") == "1":
            self.exit()
        for theme in THEMES.values():
            self.register_theme(theme)
        self.theme = DEFAULT_THEME
        self.push_screen(SafariBaseScreen(self.session))
