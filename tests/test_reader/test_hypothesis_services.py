"""Property-based tests for non-UI Safari Reader services."""

from __future__ import annotations

import string

from hypothesis import given
from hypothesis import strategies as st

from safari_reader.services import format_book_text, parse_chapters, strip_html_tags

PLAIN_TEXT = st.text(
    alphabet=string.ascii_letters + string.digits + " ",
    min_size=1,
    max_size=24,
).filter(lambda value: value.strip() != "")
WORD_TEXT = st.text(
    alphabet=string.ascii_letters + string.digits,
    min_size=1,
    max_size=10,
)
CHAPTER_PREFIX = st.sampled_from(["CHAPTER", "BOOK", "PART", "SECTION", "ACT", "SCENE"])


@given(st.lists(PLAIN_TEXT, min_size=1, max_size=5))
def test_strip_html_tags_is_idempotent_for_simple_markup(fragments: list[str]) -> None:
    html = "<div>" + "<br>".join(f"<p>{fragment}</p>" for fragment in fragments) + "</div>"

    stripped = strip_html_tags(html)

    assert strip_html_tags(stripped) == stripped
    assert [line for line in stripped.splitlines() if line] == fragments


@given(
    st.lists(
        st.tuples(CHAPTER_PREFIX, PLAIN_TEXT),
        min_size=1,
        max_size=5,
    )
)
def test_parse_chapters_returns_offsets_inside_document(
    sections: list[tuple[str, str]]
) -> None:
    document = "\n\n".join(f"{prefix} {title}\nBody {index}" for index, (prefix, title) in enumerate(sections))
    chapters = parse_chapters(document)

    assert len(chapters) == len(sections)
    for (label, offset), (prefix, title) in zip(chapters, sections):
        assert label.startswith(prefix)
        assert title.strip() in label
        assert 0 <= offset < len(document)


@given(
        st.lists(
            st.lists(WORD_TEXT, min_size=1, max_size=8),
            min_size=1,
            max_size=4,
        ),
    st.integers(min_value=20, max_value=100),
    st.integers(min_value=0, max_value=10),
)
def test_format_book_text_preserves_word_sequence_and_width_bounds(
    paragraphs: list[list[str]], width: int, margin: int
) -> None:
    original = "\n\n".join(" ".join(words) for words in paragraphs)
    formatted = format_book_text(original, width=width, margin=margin)
    max_line_length = margin + max(20, width - margin * 2)

    assert formatted.split() == original.split()
    for line in formatted.splitlines():
        if not line:
            continue
        assert line.startswith(" " * margin)
        assert len(line) <= max_line_length
