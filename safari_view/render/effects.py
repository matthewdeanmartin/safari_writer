"""
SafariView Post-processing Effects.
"""
from __future__ import annotations

from PIL import Image, ImageDraw


def apply_pixel_grid(image: Image.Image, logical_width: int, logical_height: int) -> Image.Image:
    """
    Apply a subtle grid between the 'logical' pixels to enhance the retro feel.
    The image passed in should already be at its final display size.
    """
    draw = ImageDraw.Draw(image)
    w, h = image.size
    
    # Calculate display size of one logical pixel
    pix_w = w / logical_width
    pix_h = h / logical_height
    
    # Draw horizontal lines
    for y in range(logical_height + 1):
        yy = int(y * pix_h)
        draw.line([(0, yy), (w, yy)], fill=(0, 0, 0), width=1)
        
    # Draw vertical lines
    for x in range(logical_width + 1):
        xx = int(x * pix_w)
        draw.line([(xx, 0), (xx, h)], fill=(0, 0, 0), width=1)
        
    return image
