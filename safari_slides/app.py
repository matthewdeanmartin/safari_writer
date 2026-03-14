"""Standalone Textual app for Safari Slides."""

from __future__ import annotations

import os
from pathlib import Path

from textual.app import App

from safari_slides.screens import SafariSlidesMainScreen
from safari_slides.services import build_welcome_deck, load_presentation
from safari_slides.state import SafariSlidesState

__all__ = ["SafariSlidesApp"]


class SafariSlidesApp(App[None]):
    """Keyboard-first slide viewer with Safari suite styling."""

    TITLE = "Safari Slides"
    CSS = ""

    def __init__(self, source_path: Path | None = None) -> None:
        super().__init__()
        self.state = SafariSlidesState()
        self._source_path = source_path

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

        if self._source_path is None:
            presentation = build_welcome_deck()
            self.state.set_presentation(presentation)
        else:
            source_text = self._source_path.read_text(encoding="utf-8")
            presentation = load_presentation(self._source_path)
            self.state.set_presentation(
                presentation,
                source_path=self._source_path,
                source_text=source_text,
            )
        self.push_screen(SafariSlidesMainScreen(self.state))

    def quit_slides(self) -> None:
        """Exit the standalone app."""

        self.exit()
