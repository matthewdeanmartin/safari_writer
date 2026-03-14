"""
SafariView Palettes.
Provides common retro palettes for rendering modes.
"""

from __future__ import annotations


from PIL import Image


def get_atari_2600_palette() -> list[int]:
    """
    Atari 2600 NTSC palette.
    Simplified subset.
    Returns a list of [r, g, b, r, g, b, ...] values for PIL palette.
    """
    # Just some sample values for now
    palette = [
        0,
        0,
        0,  # Black
        255,
        255,
        255,  # White
        255,
        0,
        0,  # Red
        0,
        255,
        0,  # Green
        0,
        0,
        255,  # Blue
        255,
        255,
        0,  # Yellow
        255,
        0,
        255,  # Magenta
        0,
        255,
        255,  # Cyan
        128,
        0,
        0,  # Dark Red
        0,
        128,
        0,  # Dark Green
        0,
        0,
        128,  # Dark Blue
        128,
        128,
        0,  # Dark Yellow
        128,
        0,
        128,  # Dark Magenta
        0,
        128,
        128,  # Dark Cyan
        192,
        192,
        192,  # Silver
        128,
        128,
        128,  # Gray
    ]
    # Pad to 256 colors
    palette.extend([0] * (256 * 3 - len(palette)))
    return palette


def get_atari_800_palette() -> list[int]:
    """
    Atari 800 palette.
    Returns a list of [r, g, b, r, g, b, ...] values for PIL palette.
    """
    # A bit more colors than 2600
    # For now, let's use a standard 256-color set or similar
    palette = []
    # Simplified: generate some ramps
    for r in [0, 64, 128, 192, 255]:
        for g in [0, 64, 128, 192, 255]:
            for b in [0, 64, 128, 192, 255]:
                palette.extend([r, g, b])

    # Pad to 256 colors
    palette.extend([0] * (256 * 3 - len(palette)))
    return palette[: 256 * 3]


def apply_palette(
    image: Image.Image, palette_data: list[int], dither: bool = True
) -> Image.Image:
    """Apply a palette to an RGB image."""
    palette_image = Image.new("P", (1, 1))
    palette_image.putpalette(palette_data)

    # Use Floyd-Steinberg dithering if requested
    dither_type = Image.Dither.FLOYDSTEINBERG if dither else Image.Dither.NONE
    return image.quantize(palette=palette_image, dither=dither_type)
