"""
SafariView 800 Rendering Mode.
"""

from __future__ import annotations

from PIL import Image

from safari_view.render.palettes import apply_palette, get_atari_800_palette
from safari_view.render.pipeline import ImageTransformer, RenderContext


class Mode800Transformer(ImageTransformer):
    """Atari 800 style transformer."""

    def transform(self, image: Image.Image, context: RenderContext) -> Image.Image:
        """
        Transform the image to look like Atari 8-bit graphics.
        - Moderate resolution (e.g., 160-320 wide)
        - Palette-limited (Atari 8-bit colors)
        - Visible blockiness
        """
        # Step 1: Target logical resolution
        # Let's use 160 for that classic blocky look
        logical_width = 160
        aspect_ratio = image.height / image.width
        logical_height = max(1, int(logical_width * aspect_ratio))

        # Step 2: Downsample
        small_img = image.resize(
            (logical_width, logical_height), Image.Resampling.NEAREST
        )

        # Step 3: Apply palette
        palette_data = get_atari_800_palette()
        quantized = apply_palette(small_img, palette_data, dither=context.dithering)

        # Step 4: Convert back to RGB
        result = quantized.convert("RGB")

        # Step 5: Upscale to target display size
        target_aspect = context.target_height / context.target_width
        if aspect_ratio > target_aspect:
            final_h = context.target_height
            final_w = int(final_h / aspect_ratio)
        else:
            final_w = context.target_width
            final_h = int(final_w * aspect_ratio)

        return result.resize((final_w, final_h), Image.Resampling.NEAREST)
