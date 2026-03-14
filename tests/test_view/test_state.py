"""Tests for SafariView state models."""

from __future__ import annotations

from pathlib import Path

from safari_view.render import RenderMode
from safari_view.state import SafariViewState


def test_state_defaults():
    state = SafariViewState()
    assert state.current_path == Path.cwd()
    assert state.current_image_path is None
    assert state.render_mode == RenderMode.MODE_800
    assert state.dithering is True


def test_next_render_mode_cycles_through_all_modes():
    state = SafariViewState(render_mode=RenderMode.MODE_2600)

    # 2600 -> 800
    state.next_render_mode()
    assert state.render_mode == RenderMode.MODE_800

    # 800 -> ST
    state.next_render_mode()
    assert state.render_mode == RenderMode.MODE_ST

    # ST -> NATIVE
    state.next_render_mode()
    assert state.render_mode == RenderMode.NATIVE

    # NATIVE -> 2600
    state.next_render_mode()
    assert state.render_mode == RenderMode.MODE_2600
