"""Property-based tests for non-UI Safari Slides logic."""

from __future__ import annotations

import string

from hypothesis import given
from hypothesis import strategies as st

from safari_slides.model import Presentation, RenderLine, Slide
from safari_slides.parser import _parse_metadata, parse_slidemd
from safari_slides.state import SafariSlidesState

TEXT_LINE = st.text(
    alphabet=string.ascii_letters + string.digits + " -_",
    min_size=1,
    max_size=24,
).filter(lambda value: value.strip() != "")


@st.composite
def slide_sections(draw: st.DrawFn) -> list[tuple[str, list[str]]]:
    titles = draw(
        st.lists(
            TEXT_LINE, min_size=1, max_size=5, unique_by=lambda value: value.lower()
        )
    )
    bodies = draw(
        st.lists(
            st.lists(TEXT_LINE, min_size=1, max_size=4),
            min_size=len(titles),
            max_size=len(titles),
        )
    )
    return list(zip(titles, bodies))


@given(slide_sections())
def test_parse_slidemd_assigns_sequential_slide_ids(
    sections: list[tuple[str, list[str]]],
) -> None:
    deck = "\n\n---\n\n".join(
        f"# {title}\n\n" + "\n".join(body_lines) for title, body_lines in sections
    )

    presentation = parse_slidemd(deck)

    assert len(presentation.slides) == len(sections)
    assert [slide.slide_id for slide in presentation.slides] == [
        f"slide-{index}" for index in range(1, len(sections) + 1)
    ]
    assert [slide.title for slide in presentation.slides] == [
        title.strip() for title, _body_lines in sections
    ]


@given(st.dictionaries(TEXT_LINE, TEXT_LINE, min_size=1, max_size=6))
def test_parse_metadata_normalizes_keys_to_lowercase(data: dict[str, str]) -> None:
    block = "\n".join(f"{key}: {value}" for key, value in data.items())
    parsed = _parse_metadata(block)

    assert parsed == {key.strip().lower(): value.strip() for key, value in data.items()}


@given(
    st.lists(st.integers(min_value=0, max_value=5), max_size=8),
    st.integers(min_value=1, max_value=9),
    st.integers(min_value=1, max_value=9),
)
def test_slide_properties_reflect_fragment_counts_and_coordinates(
    fragment_orders: list[int], horizontal_index: int, vertical_index: int
) -> None:
    slide = Slide(
        slide_id="slide-1",
        title="Demo",
        raw_markdown="# Demo",
        lines=tuple(
            RenderLine(f"line-{index}", order)
            for index, order in enumerate(fragment_orders)
        ),
        horizontal_index=horizontal_index,
        vertical_index=vertical_index,
    )

    assert slide.fragment_count == max(fragment_orders, default=0)
    if vertical_index > 1:
        assert slide.slide_label == f"{horizontal_index}.{vertical_index}"
    else:
        assert slide.slide_label == str(horizontal_index)


@given(st.lists(st.integers(min_value=0, max_value=4), min_size=1, max_size=6))
def test_slides_state_advance_reaches_last_slide(fragment_counts: list[int]) -> None:
    slides = tuple(
        Slide(
            slide_id=f"slide-{index + 1}",
            title=f"Slide {index + 1}",
            raw_markdown=f"# Slide {index + 1}",
            lines=tuple(
                RenderLine(f"fragment-{step}", step)
                for step in range(1, fragment_count + 1)
            ),
        )
        for index, fragment_count in enumerate(fragment_counts)
    )
    state = SafariSlidesState(presentation=Presentation(slides=slides))
    total_steps = sum(fragment_counts) + len(fragment_counts) - 1

    for _ in range(total_steps):
        state.advance()

    assert state.current_slide_index == len(slides) - 1
    assert state.fragment_step == slides[-1].fragment_count
