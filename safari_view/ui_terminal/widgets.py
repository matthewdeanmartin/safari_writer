"""
SafariView ChunkyImage Widget.
Renders a PIL image using Unicode block characters in the terminal.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from rich.color import Color
from rich.style import Style
from rich.text import Text
from textual.widget import Widget

if TYPE_CHECKING:
    from PIL import Image


class ChunkyImage(Widget):
    """
    A widget that displays an image using Unicode half-blocks.
    This provides the 'chunky' retro look in the terminal.
    """

    def __init__(self, image: Image.Image | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.image = image

    def update_image(self, image: Image.Image) -> None:
        """Update the image and refresh the widget."""
        self.image = image
        self.refresh()

    def render(self) -> Any:
        """Render the image to terminal segments."""
        if not self.image:
            return Text("No image loaded")

        # Convert image to RGB if not already
        img = self.image.convert("RGB")
        width, height = img.size

        # Each terminal cell can show two 'pixels' using the half-block character
        # ▄ (lower half block) or ▀ (upper half block)
        # We'll use the upper half block ▀.
        # Foreground color = top pixel, Background color = bottom pixel.

        pixels = cast(Any, img.load())
        text = Text()

        for y in range(0, height, 2):
            for x in range(width):
                # Top pixel
                r1, g1, b1 = pixels[x, y]

                # Bottom pixel (if within bounds, otherwise same as top or black)
                if y + 1 < height:
                    r2, g2, b2 = pixels[x, y + 1]
                else:
                    r2, g2, b2 = 0, 0, 0

                style = Style(
                    color=Color.from_rgb(r1, g1, b1), bgcolor=Color.from_rgb(r2, g2, b2)
                )

                text.append("▀", style)
            text.append("\n")

        return text
