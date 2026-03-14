"""Standalone Textual app for Safari DOS."""

from __future__ import annotations

import os
from pathlib import Path

from textual.app import App

from safari_dos.screens import (
    SafariDosBrowserScreen,
    SafariDosDevicesScreen,
    SafariDosFavoritesScreen,
    SafariDosGarbageScreen,
    SafariDosHelpScreen,
    SafariDosMainMenuScreen,
)
from safari_dos.services import (
    list_favorites,
    list_recent_documents,
    list_recent_locations,
)
from safari_dos.state import SafariDosExitRequest, SafariDosLaunchConfig, SafariDosState

__all__ = ["SafariDosApp"]


class SafariDosApp(App[SafariDosExitRequest | None]):
    """Atari DOS-inspired file manager for Safari Writer."""

    TITLE = "Safari DOS"

    def __init__(
        self,
        start_path: Path | None = None,
        *,
        state: SafariDosState | None = None,
        launch_config: SafariDosLaunchConfig | None = None,
    ) -> None:
        super().__init__()
        current_path = (start_path or Path.cwd()).resolve()
        self.state = state or SafariDosState(
            current_path=current_path,
            favorites=list_favorites(),
            recent_locations=list_recent_locations(),
            recent_documents=list_recent_documents(),
        )
        self.launch_config = launch_config or SafariDosLaunchConfig()

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

        self._launch_initial_screen()

    def open_browser(
        self,
        *,
        picker_mode: str | None = None,
        selected_path: Path | None = None,
    ) -> None:
        self.push_screen(
            SafariDosBrowserScreen(
                self.state,
                picker_mode=picker_mode,
                initial_selection_path=selected_path,
            )
        )

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

    def open_favorites(self) -> None:
        self.push_screen(
            SafariDosFavoritesScreen(self.state),
            callback=self._on_choose_favorite,
        )

    def open_help(self) -> None:
        self.push_screen(SafariDosHelpScreen())

    def open_style_switcher(self) -> None:
        from safari_writer.screens.style_switcher import StyleSwitcherScreen

        self.push_screen(StyleSwitcherScreen(self.theme))

    def quit_dos(self) -> None:
        self.exit()

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

    def _on_choose_favorite(self, path: Path | None) -> None:
        if path is None:
            return
        if path.is_dir():
            self.state.current_path = path.resolve()
            self.open_browser()
            return
        if path.exists():
            self.request_writer_launch(path.resolve())

    def _launch_initial_screen(self) -> None:
        screen = self.launch_config.initial_screen
        if screen == "browser":
            self.open_browser(
                picker_mode=self.launch_config.picker_mode,
                selected_path=self.launch_config.selected_path,
            )
            return
        if screen == "devices":
            self.open_devices()
            return
        if screen == "favorites":
            self.open_favorites()
            return
        if screen == "garbage":
            self.open_garbage()
            return
        if screen == "help":
            self.open_help()
            return
        self.push_screen(SafariDosMainMenuScreen(self.state))
