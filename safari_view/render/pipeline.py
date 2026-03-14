"""
SafariView Rendering Pipeline.
Handles loading, transforming, and preparing images for different backends.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING

from PIL import Image

# Allow opening large images (common for modern screenshots)
Image.MAX_IMAGE_PIXELS = None

if TYPE_CHECKING:
    from pathlib import Path


class RenderMode(Enum):
    """Available retro rendering modes."""

    MODE_2600 = auto()
    MODE_800 = auto()
    MODE_ST = auto()
    NATIVE = auto()


@dataclass
class RenderContext:
    """Context for a rendering operation."""

    target_width: int
    target_height: int
    dithering: bool = True
    palette_name: str = "default"
    zoom: float = 1.0
    pixel_grid: bool = False


class ImageTransformer(ABC):
    """Abstract base class for image transformers."""

    @abstractmethod
    def transform(self, image: Image.Image, context: RenderContext) -> Image.Image:
        """Transform the image according to the mode and context."""


class Pipeline:
    """Orchestrates the image transformation process."""

    def __init__(self, transformers: dict[RenderMode, ImageTransformer]):
        self.transformers = transformers

    def process(
        self,
        image_path: Path,
        mode: RenderMode,
        context: RenderContext,
    ) -> Image.Image:
        """Load and process an image."""
        with Image.open(image_path) as img:
            # Handle orientation if needed (EXIF)
            img = self._prepare_image(img)

            transformer = self.transformers.get(mode)
            if not transformer:
                raise ValueError(f"No transformer for mode {mode}")

            return transformer.transform(img, context)

    def _prepare_image(self, image: Image.Image) -> Image.Image:
        """Initial preparation (e.g., handles alpha by compositing onto solid background)."""
        if image.mode in ("RGBA", "LA") or (
            image.mode == "P" and "transparency" in image.info
        ):
            image = image.convert("RGBA")
            # Composite onto black to avoid junk colors from alpha-dropping
            background = Image.new("RGBA", image.size, (0, 0, 0, 255))
            image = Image.alpha_composite(background, image).convert("RGB")
        elif image.mode != "RGB":
            image = image.convert("RGB")
        # TODO: Handle EXIF orientation
        return image
