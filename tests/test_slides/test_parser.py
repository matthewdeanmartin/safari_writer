"""Parser tests for safari_slides."""

from safari_slides.parser import parse_slidemd


def test_parse_slidemd_extracts_metadata_notes_and_fragments() -> None:
    presentation = parse_slidemd("""---
title: Demo Deck
footer: Demo Footer
paginate: true
---

# Intro

- first
+ second
- third <!-- fragment -->

---
layout: title
footer: Slide Footer
---

## Closing

Note:

Remember to thank the audience.
""")

    assert presentation.metadata.title == "Demo Deck"
    assert presentation.metadata.footer == "Demo Footer"
    assert len(presentation.slides) == 2
    assert presentation.slides[0].fragment_count == 2
    assert presentation.slides[1].metadata.layout == "title"
    assert presentation.slides[1].metadata.footer == "Slide Footer"
    assert presentation.slides[1].notes == ("Remember to thank the audience.",)


def test_parse_slidemd_tracks_vertical_slide_coordinates() -> None:
    presentation = parse_slidemd("""# Topic

---

## Detail A

----

## Detail B
""")

    assert [slide.slide_label for slide in presentation.slides] == ["1", "2", "2.2"]
    assert presentation.slides[2].vertical_index == 2
