"""Standalone Textual app for Safari Reader."""

from __future__ import annotations

from pathlib import Path

from textual.app import App

from safari_reader.screens import SafariReaderMainMenuScreen
from safari_reader.state import SafariReaderExitRequest, SafariReaderState

__all__ = ["SafariReaderApp"]


class SafariReaderApp(App[SafariReaderExitRequest | None]):
    """Keyboard-first terminal e-book reader with AtariWriter-era charm."""

    TITLE = "Safari Reader"
    CSS = ""

    def __init__(self, library_dir: Path | None = None) -> None:
        super().__init__()
        self.state = SafariReaderState()
        if library_dir is not None:
            library_dir.mkdir(parents=True, exist_ok=True)
            self.state.library_dir = library_dir

    def on_mount(self) -> None:
        from safari_writer.themes import DEFAULT_THEME, THEMES, load_settings

        for theme in THEMES.values():
            self.register_theme(theme)
        settings = load_settings()
        saved_theme = settings.get("theme", DEFAULT_THEME)
        if saved_theme not in THEMES:
            saved_theme = DEFAULT_THEME
        self.theme = saved_theme

        self.push_screen(SafariReaderMainMenuScreen(self.state))

    def quit_reader(self) -> None:
        """Exit the standalone app."""
        self.exit()

    def open_in_writer(self, path: Path) -> None:
        """Request handoff to Safari Writer to edit a file."""
        self.exit(SafariReaderExitRequest(action="open-in-writer", document_path=path))
