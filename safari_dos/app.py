"""Standalone Textual app for Safari DOS."""

from __future__ import annotations

from pathlib import Path

from textual.app import App

from safari_dos.screens import (
    SafariDosBrowserScreen,
    SafariDosDevicesScreen,
    SafariDosGarbageScreen,
    SafariDosMainMenuScreen,
)
from safari_dos.services import list_favorites, list_recent_documents, list_recent_locations
from safari_dos.state import SafariDosExitRequest, SafariDosState

__all__ = ["SafariDosApp"]


class SafariDosApp(App[SafariDosExitRequest | None]):
    """Atari DOS-inspired file manager for Safari Writer."""

    TITLE = "Safari DOS"

    def __init__(self, start_path: Path | None = None) -> None:
        super().__init__()
        current_path = (start_path or Path.cwd()).resolve()
        self.state = SafariDosState(
            current_path=current_path,
            favorites=list_favorites(),
            recent_locations=list_recent_locations(),
            recent_documents=list_recent_documents(),
        )

    def on_mount(self) -> None:
        self.push_screen(SafariDosMainMenuScreen(self.state))

    def open_browser(self) -> None:
        self.push_screen(SafariDosBrowserScreen(self.state))

    def open_devices(self) -> None:
        self.push_screen(
            SafariDosDevicesScreen(self.state),
            callback=self._on_choose_device,
        )

    def open_garbage(self) -> None:
        self.push_screen(
            SafariDosGarbageScreen(),
            callback=self._on_restore_from_garbage,
        )

    def request_writer_launch(self, path: Path) -> None:
        self.exit(SafariDosExitRequest(action="open-in-writer", document_path=path))

    def _on_choose_device(self, path: Path | None) -> None:
        if path is None:
            return
        self.state.current_path = path
        self.open_browser()

    def _on_restore_from_garbage(self, restored: Path | None) -> None:
        if restored is None:
            return
        self.state.current_path = restored.parent
        self.open_browser()
