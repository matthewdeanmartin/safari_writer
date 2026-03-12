"""
SafariView State.
Manages the application state, including current image, render mode, and configuration.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from safari_view.render import RenderMode


@dataclass
class SafariViewState:
    """State for the SafariView application."""

    current_path: Path = field(default_factory=Path.cwd)
    current_image_path: Path | None = None
    render_mode: RenderMode = RenderMode.MODE_800
    dithering: bool = True
    pixel_grid: bool = False
    zoom: float = 1.0
    slideshow_active: bool = False
    slideshow_delay: float = 3.0
    theme: str = "atari_blue"

    def next_render_mode(self) -> None:
        """Cycle to the next rendering mode."""
        modes = list(RenderMode)
        current_index = modes.index(self.render_mode)
        self.render_mode = modes[(current_index + 1) % len(modes)]
