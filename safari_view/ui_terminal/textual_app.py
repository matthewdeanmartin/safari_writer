"""
SafariView Terminal UI.
The primary Textual application for browsing and viewing images.
"""

from __future__ import annotations

import logging
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import DirectoryTree, Footer, Header, Static

from safari_view.render import RenderContext, RenderMode, create_pipeline
from safari_view.state import SafariViewLaunchConfig, SafariViewState
from safari_view.ui_terminal.widgets import ChunkyImage

_log = logging.getLogger("safari_view.ui_terminal")

MIN_RENDER_WIDTH = 20
MIN_RENDER_HEIGHT_ROWS = 6
FILE_PANE_FALLBACK_WIDTH = 30


def resolve_render_target(
    pane_width: int,
    pane_height: int,
    console_width: int,
    console_height: int,
    browser_width: int,
) -> tuple[int, int]:
    """Return a sane render target in terminal pixels."""
    fallback_width = max(1, console_width - browser_width)
    fallback_height_rows = max(1, console_height - 2)

    resolved_width = pane_width if pane_width >= MIN_RENDER_WIDTH else fallback_width
    resolved_height_rows = (
        pane_height if pane_height >= MIN_RENDER_HEIGHT_ROWS else fallback_height_rows
    )

    return max(1, resolved_width), max(2, resolved_height_rows * 2)


class SafariViewScreen(Screen):
    """SafariView — a retro 8-bit image viewer as a Screen."""

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("f2", "toggle_browser", "File Browser"),
        ("f3", "set_mode_2600", "2600 Mode"),
        ("f4", "set_mode_800", "800 Mode"),
        ("f5", "set_mode_st", "ST Mode"),
        ("f6", "set_mode_native", "Native"),
        ("d", "toggle_dithering", "Dithering"),
        ("g", "toggle_pixel_grid", "Pixel Grid"),
        ("enter", "open_image", "Open"),
        ("escape", "back", "Back"),
    ]

    def __init__(
        self,
        state: SafariViewState | None = None,
        launch_config: SafariViewLaunchConfig | None = None,
    ) -> None:
        super().__init__()
        self.state = state or SafariViewState()
        self.launch_config = launch_config or SafariViewLaunchConfig()
        self.pipeline = create_pipeline()
        self._last_selected_path: Path | None = None

    def compose(self) -> ComposeResult:
        """Compose the screen layout."""
        yield Header()
        with Horizontal():
            with Vertical(id="file_pane"):
                yield DirectoryTree(self.state.current_path)
            with Container(id="viewer_pane"):
                yield ChunkyImage(id="image_viewer")
        yield Footer()

    def on_mount(self) -> None:
        """Called when the screen is mounted."""
        self.app.title = f"SafariView - {self.state.render_mode.name}"
        self.call_after_refresh(self._apply_startup_state)

    def on_resize(self) -> None:
        """Handle terminal resize by refreshing the image."""
        self._refresh_image()

    def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        """Called when a file is selected in the directory tree."""
        self._last_selected_path = event.path
        self._load_and_render_image(event.path)

    def action_toggle_browser(self) -> None:
        """Toggle the file browser pane visibility."""
        file_pane = self.query_one("#file_pane")
        file_pane.visible = not file_pane.visible
        self._update_focus_from_visibility()

    def action_set_mode_2600(self) -> None:
        """Set rendering mode to 2600."""
        self.state.render_mode = RenderMode.MODE_2600
        self._refresh_image()

    def action_set_mode_800(self) -> None:
        """Set rendering mode to 800."""
        self.state.render_mode = RenderMode.MODE_800
        self._refresh_image()

    def action_set_mode_st(self) -> None:
        """Set rendering mode to ST."""
        self.state.render_mode = RenderMode.MODE_ST
        self._refresh_image()

    def action_set_mode_native(self) -> None:
        """Set rendering mode to Native."""
        self.state.render_mode = RenderMode.NATIVE
        self._refresh_image()

    def action_toggle_dithering(self) -> None:
        """Toggle dithering on/off."""
        self.state.dithering = not self.state.dithering
        self._refresh_image()

    def action_toggle_pixel_grid(self) -> None:
        """Toggle pixel grid on/off."""
        self.state.pixel_grid = not self.state.pixel_grid
        self._refresh_image()

    def action_open_image(self) -> None:
        """Manually trigger open for the selected file in tree."""
        tree = self.query_one(DirectoryTree)
        if tree.cursor_node and tree.cursor_node.data:
            path = tree.cursor_node.data.path
            if path.is_file():
                self._last_selected_path = path
                self._load_and_render_image(path)

    def action_back(self) -> None:
        """Return to the previous screen."""
        self.app.pop_screen()

    def _refresh_image(self) -> None:
        """Rerender the current image with current settings."""
        if self._last_selected_path:
            self._load_and_render_image(self._last_selected_path)
        self.app.title = f"SafariView - {self.state.render_mode.name}"

    def _apply_startup_state(self) -> None:
        """Apply startup-only launch configuration once widgets are ready."""
        file_pane = self.query_one("#file_pane", Vertical)
        file_pane.visible = self.launch_config.browser_visible

        startup_path = self.launch_config.selected_path
        if startup_path is not None and startup_path.is_file():
            self._last_selected_path = startup_path

        if self.state.current_image_path is not None:
            self._last_selected_path = self.state.current_image_path
            self._load_and_render_image(self.state.current_image_path)

        self._update_focus_from_visibility()

    def _update_focus_from_visibility(self) -> None:
        """Keep focus aligned with the requested startup target."""
        file_pane = self.query_one("#file_pane", Vertical)
        tree = self.query_one(DirectoryTree)
        viewer = self.query_one("#image_viewer", ChunkyImage)

        if self.launch_config.focus_target == "viewer" or not file_pane.visible:
            self.set_focus(viewer)
        else:
            self.set_focus(tree)

    def _load_and_render_image(self, path: Path) -> None:
        """Load and transform the image for display."""
        try:
            viewer = self.query_one("#image_viewer", ChunkyImage)
            pane = self.query_one("#viewer_pane", Container)
            file_pane = self.query_one("#file_pane", Vertical)

            pane_width = max(pane.content_size.width, pane.size.width)
            pane_height = max(pane.content_size.height, pane.size.height)
            console_width = max(self.app.size.width, self.app.console.width)
            console_height = max(self.app.size.height, self.app.console.height)
            browser_width = (
                max(file_pane.size.width, FILE_PANE_FALLBACK_WIDTH)
                if file_pane.visible
                else 0
            )
            target_width, target_height = resolve_render_target(
                pane_width=pane_width,
                pane_height=pane_height,
                console_width=console_width,
                console_height=console_height,
                browser_width=browser_width,
            )

            _log.debug(
                "Rendering image path=%s mode=%s pane=%sx%s console=%sx%s browser=%s "
                "target=%sx%s",
                path,
                self.state.render_mode.name,
                pane_width,
                pane_height,
                console_width,
                console_height,
                browser_width,
                target_width,
                target_height,
            )

            context = RenderContext(
                target_width=target_width,
                target_height=target_height,
                dithering=self.state.dithering,
                pixel_grid=self.state.pixel_grid,
            )

            # Process image through pipeline
            transformed = self.pipeline.process(path, self.state.render_mode, context)

            _log.debug(
                "Rendered image path=%s transformed_size=%sx%s viewer=%sx%s",
                path,
                transformed.width,
                transformed.height,
                viewer.size.width,
                viewer.size.height,
            )
            viewer.update_image(transformed)
            self.state.current_image_path = path
            self.app.notify(f"Loaded: {path.name}")

        except Exception as e:
            _log.exception("Error loading image %s", path)
            self.app.notify(f"Error loading image: {e}", severity="error")


class SafariViewApp(App):
    """SafariView — a retro 8-bit image viewer."""

    TITLE = "SafariView"
    CSS = """
    Screen {
        background: #000033; /* Dark blue background */
        color: #00FFFF; /* Cyan text */
    }
    
    #file_pane {
        width: 30;
        border-right: solid #00FFFF;
    }
    
    #viewer_pane {
        width: 1fr;
        height: 1fr;
        align: center middle;
        overflow: hidden;
    }
    
    ChunkyImage {
        width: 1fr;
        height: 1fr;
    }
    """

    def __init__(
        self,
        state: SafariViewState | None = None,
        launch_config: SafariViewLaunchConfig | None = None,
    ) -> None:
        super().__init__()
        self.state = state or SafariViewState()
        self.launch_config = launch_config or SafariViewLaunchConfig()

    def on_mount(self) -> None:
        self.push_screen(SafariViewScreen(self.state, self.launch_config))


def main():
    """Main entry point for SafariView."""
    app = SafariViewApp()
    app.run()


if __name__ == "__main__":
    main()
