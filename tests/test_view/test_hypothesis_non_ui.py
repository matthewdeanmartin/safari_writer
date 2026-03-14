"""Property-based tests for non-UI SafariView helpers."""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st
from PIL import Image

from safari_view.render import RenderMode
from safari_view.render.palettes import (
    apply_palette,
    get_atari_2600_palette,
    get_atari_800_palette,
)
from safari_view.state import SafariViewState


@given(st.sampled_from([get_atari_2600_palette, get_atari_800_palette]))
def test_palettes_have_full_pil_palette_shape(factory) -> None:
    palette = factory()

    assert len(palette) == 256 * 3
    assert all(0 <= value <= 255 for value in palette)


@given(
    st.integers(min_value=1, max_value=16),
    st.integers(min_value=1, max_value=16),
    st.tuples(
        st.integers(min_value=0, max_value=255),
        st.integers(min_value=0, max_value=255),
        st.integers(min_value=0, max_value=255),
    ),
    st.booleans(),
)
def test_apply_palette_preserves_image_size(
    width: int, height: int, color: tuple[int, int, int], dither: bool
) -> None:
    image = Image.new("RGB", (width, height), color=color)

    rendered = apply_palette(image, get_atari_800_palette(), dither=dither)

    assert rendered.size == image.size
    assert rendered.mode == "P"


@given(st.sampled_from(list(RenderMode)))
def test_next_render_mode_cycles_back_to_start(start_mode: RenderMode) -> None:
    state = SafariViewState(render_mode=start_mode)

    for _ in range(len(RenderMode)):
        state.next_render_mode()

    assert state.render_mode is start_mode
