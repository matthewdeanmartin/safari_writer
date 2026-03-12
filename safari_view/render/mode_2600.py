"""
SafariView 2600 Rendering Mode.
"""
from __future__ import annotations

from PIL import Image

from safari_view.render.pipeline import ImageTransformer, RenderContext
from safari_view.render.palettes import get_atari_2600_palette, apply_palette
from safari_view.render.effects import apply_pixel_grid


class Mode2600Transformer(ImageTransformer):
    """Atari 2600 style transformer."""

    def transform(self, image: Image.Image, context: RenderContext) -> Image.Image:
        """
        Transform the image to look like Atari 2600 graphics.
        - Extremely low resolution
        - Limited palette
        - Big chunky pixels
        """
        # Step 1: Target logical resolution (very low)
        # 40-80 logical pixels wide. Let's use 80.
        logical_width = 80
        aspect_ratio = image.height / image.width
        logical_height = max(1, int(logical_width * aspect_ratio))

        # Step 2: Downsample (nearest neighbor for chunkiness)
        small_img = image.resize((logical_width, logical_height), Image.Resampling.NEAREST)

        # Step 3: Apply palette
        palette_data = get_atari_2600_palette()
        quantized = apply_palette(small_img, palette_data, dither=context.dithering)

        # Step 4: Convert back to RGB for further processing or display
        result = quantized.convert("RGB")

        # Step 5: Upscale to target display size (nearest neighbor to keep pixels chunky)
        target_aspect = context.target_height / context.target_width
        if aspect_ratio > target_aspect:
            final_h = context.target_height
            final_w = int(final_h / aspect_ratio)
        else:
            final_w = context.target_width
            final_h = int(final_w * aspect_ratio)

        upscaled = result.resize((final_w, final_h), Image.Resampling.NEAREST)
        
        # Step 6: Post-processing (pixel grid)
        if context.pixel_grid:
            upscaled = apply_pixel_grid(upscaled, logical_width, logical_height)
            
        return upscaled
