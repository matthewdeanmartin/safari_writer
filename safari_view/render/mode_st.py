"""
SafariView ST and Native Rendering Modes.
"""

from __future__ import annotations

from PIL import Image

from safari_view.render.palettes import apply_palette, get_atari_800_palette
from safari_view.render.pipeline import ImageTransformer, RenderContext


class ModeSTTransformer(ImageTransformer):
    """Atari ST style transformer."""

    def transform(self, image: Image.Image, context: RenderContext) -> Image.Image:
        """
        Transform the image to look like Atari ST graphics.
        - Higher resolution (e.g., 320-640 wide)
        - Palette-limited (Atari ST colors)
        - Clean but retro
        """
        # Step 1: Target logical resolution
        logical_width = 320
        aspect_ratio = image.height / image.width
        logical_height = max(1, int(logical_width * aspect_ratio))

        # Step 2: Downsample
        small_img = image.resize(
            (logical_width, logical_height), Image.Resampling.BICUBIC
        )

        # Step 3: Apply palette (using 800 palette for now as placeholder)
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


class NativeTransformer(ImageTransformer):
    """Native style transformer (minimal changes)."""

    def transform(self, image: Image.Image, context: RenderContext) -> Image.Image:
        """
        Just resize to fit the target dimensions.
        """
        aspect_ratio = image.height / image.width
        target_aspect = context.target_height / context.target_width

        if aspect_ratio > target_aspect:
            final_h = context.target_height
            final_w = int(final_h / aspect_ratio)
        else:
            final_w = context.target_width
            final_h = int(final_w * aspect_ratio)

        return image.resize((final_w, final_h), Image.Resampling.LANCZOS)
