"""Service-layer tests for safari_slides."""

from safari_slides.services import (
    build_slidemd_from_writer,
    is_slide_filename,
    slides_state_from_writer,
)
from safari_writer.state import AppState, GlobalFormat


def test_is_slide_filename_recognizes_supported_suffixes() -> None:
    assert is_slide_filename("deck.slides.md") is True
    assert is_slide_filename("deck.slide.md") is True
    assert is_slide_filename("deck.slidemd") is True
    assert is_slide_filename("deck.md") is False


def test_build_slidemd_from_writer_generates_slide_deck() -> None:
    rendered = build_slidemd_from_writer(
        ["Quarterly Update", "", "Revenue is up.", "", "Next steps follow."],
        GlobalFormat(),
        title="Quarterly Update",
    )

    assert "title: Quarterly Update" in rendered
    assert "# Slide 1" in rendered or "# Quarterly Update" in rendered
    assert rendered.strip().startswith("---")


def test_slides_state_from_writer_uses_existing_slide_documents() -> None:
    state = AppState(
        buffer=["# Intro", "", "---", "", "## End"],
        filename="deck.slides.md",
    )

    slides_state = slides_state_from_writer(state)

    assert slides_state.slide_count == 2
    assert slides_state.current_slide.title == "Intro"
    assert slides_state.source_text.startswith("# Intro")
