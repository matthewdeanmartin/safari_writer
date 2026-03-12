"""
Tests for SafariView Rendering Pipeline.
"""
import pytest
from pathlib import Path
from PIL import Image
from safari_view.render import create_pipeline, RenderContext, RenderMode


def test_pipeline_creation():
    pipeline = create_pipeline()
    assert pipeline is not None
    assert RenderMode.MODE_2600 in pipeline.transformers


def test_2600_transform():
    pipeline = create_pipeline()
    # Create a small test image
    img = Image.new("RGB", (100, 100), color="red")
    img_path = Path("test_image.png")
    img.save(img_path)
    
    try:
        context = RenderContext(target_width=80, target_height=80)
        result = pipeline.process(img_path, RenderMode.MODE_2600, context)
        
        assert result.width <= 80
        assert result.height <= 80
        # Check if it's still RGB (transformers should return RGB for display)
        assert result.mode == "RGB"
    finally:
        if img_path.exists():
            img_path.unlink()


def test_800_transform():
    pipeline = create_pipeline()
    img = Image.new("RGB", (100, 100), color="blue")
    img_path = Path("test_image_800.png")
    img.save(img_path)
    
    try:
        context = RenderContext(target_width=160, target_height=160)
        result = pipeline.process(img_path, RenderMode.MODE_800, context)
        
        assert result.width <= 160
        assert result.height <= 160
    finally:
        if img_path.exists():
            img_path.unlink()
