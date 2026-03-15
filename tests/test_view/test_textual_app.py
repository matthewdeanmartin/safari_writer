"""
Tests for the SafariView Textual application sizing behavior.
"""

from __future__ import annotations

import asyncio

from PIL import Image

from safari_view.ui_terminal.textual_app import (
    MIN_RENDER_HEIGHT_ROWS,
    MIN_RENDER_WIDTH,
    SafariViewApp,
    resolve_render_target,
)
from safari_view.ui_terminal.widgets import ChunkyImage


def test_resolve_render_target_uses_pane_size_when_available():
    width, height = resolve_render_target(
        pane_width=90,
        pane_height=20,
        console_width=120,
        console_height=40,
        browser_width=30,
    )

    assert width == 90
    assert height == 40


def test_resolve_render_target_falls_back_when_pane_is_tiny():
    width, height = resolve_render_target(
        pane_width=3,
        pane_height=2,
        console_width=120,
        console_height=40,
        browser_width=30,
    )

    assert width == 90
    assert height == 76


def test_textual_viewer_mounts_with_real_size():
    async def run() -> None:
        app = SafariViewApp()
        async with app.run_test() as pilot:
            # Wait for the screen to be pushed
            await pilot.pause()
            screen = app.screen
            viewer = screen.query_one("#image_viewer", ChunkyImage)
            assert viewer.size.width >= MIN_RENDER_WIDTH
            assert viewer.size.height >= MIN_RENDER_HEIGHT_ROWS

    asyncio.run(run())


def test_load_and_render_uses_stable_dimensions(tmp_path):
    captured: dict[str, object] = {}

    async def run() -> None:
        app = SafariViewApp()

        async with app.run_test() as pilot:
            await pilot.pause()
            screen = app.screen

            def fake_process(path, mode, context):
                captured["path"] = path
                captured["mode"] = mode
                captured["context"] = context
                return Image.new("RGB", (32, 32), color="green")

            screen.pipeline.process = fake_process

            image_path = tmp_path / "sample.png"
            image_path.write_text("fake", encoding="utf-8")  # Must exist
            screen._load_and_render_image(image_path)
            await pilot.pause()

    asyncio.run(run())

    context = captured["context"]
    assert captured["path"] == tmp_path / "sample.png"
    assert context.target_width >= MIN_RENDER_WIDTH
    assert context.target_height >= MIN_RENDER_HEIGHT_ROWS * 2

    context = captured["context"]
    assert captured["path"] == tmp_path / "sample.png"
    assert context.target_width >= MIN_RENDER_WIDTH
    assert context.target_height >= MIN_RENDER_HEIGHT_ROWS * 2
