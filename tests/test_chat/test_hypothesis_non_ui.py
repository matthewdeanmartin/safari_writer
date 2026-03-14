"""Property-based tests for non-UI Safari Chat helpers."""

from __future__ import annotations

import string

from hypothesis import given
from hypothesis import strategies as st

from safari_chat.engine import parse_document, score_distress
from safari_chat.safety import detect_crisis, detect_refusal
from safari_chat.state import DistressLevel, SafariChatState
from safari_chat.synonyms import apply_variation

SAFE_TEXT = st.text(
    alphabet=st.characters(blacklist_characters="\r\n", blacklist_categories=("Cs",)),
    max_size=40,
)
WORD_TEXT = st.text(
    alphabet=string.ascii_letters + " ", min_size=1, max_size=20
).filter(lambda value: value.strip() != "")
CRISIS_PHRASES = st.sampled_from(
    [
        "kill myself",
        "I want to die",
        "self harm",
        "wish I was dead",
    ]
)
REFUSAL_PHRASES = st.sampled_from(
    [
        "best way to kill myself",
        "how to commit suicide",
        "hide self harm scars",
    ]
)


def _alternating_case(text: str) -> str:
    return "".join(
        ch.upper() if index % 2 else ch.lower() for index, ch in enumerate(text)
    )


@st.composite
def markdown_sections(draw: st.DrawFn) -> tuple[str, list[str]]:
    headings = draw(
        st.lists(
            WORD_TEXT, min_size=1, max_size=5, unique_by=lambda value: value.lower()
        )
    )
    bodies = draw(st.lists(WORD_TEXT, min_size=len(headings), max_size=len(headings)))
    sections = [f"# {heading}\n\n**{body}**" for heading, body in zip(headings, bodies)]
    return "\n\n---\n\n".join(sections), headings


@given(CRISIS_PHRASES, SAFE_TEXT, SAFE_TEXT)
def test_detect_crisis_is_case_insensitive(
    phrase: str, prefix: str, suffix: str
) -> None:
    text = f"{prefix} {_alternating_case(phrase)} {suffix}"

    assert detect_crisis(text) is True


@given(REFUSAL_PHRASES, SAFE_TEXT, SAFE_TEXT)
def test_detect_refusal_is_case_insensitive(
    phrase: str, prefix: str, suffix: str
) -> None:
    text = f"{prefix} {_alternating_case(phrase)} {suffix}"

    assert detect_refusal(text) is True


@given(SAFE_TEXT)
def test_apply_variation_respects_protect_safety(text: str) -> None:
    assert apply_variation(text, protect_safety=True) == text


@given(SAFE_TEXT, st.integers(min_value=0, max_value=1000))
def test_apply_variation_is_deterministic_for_a_seed(text: str, seed: int) -> None:
    assert apply_variation(text, seed=seed) == apply_variation(text, seed=seed)


@given(markdown_sections())
def test_parse_document_assigns_sequential_chunk_ids(
    section_data: tuple[str, list[str]],
) -> None:
    text, headings = section_data
    chunks = parse_document(text)

    assert len(chunks) == len(headings)
    assert [chunk.chunk_id for chunk in chunks] == list(range(len(chunks)))
    assert [chunk.heading for chunk in chunks] == [
        heading.strip() for heading in headings
    ]
    assert all(chunk.body for chunk in chunks)


@given(CRISIS_PHRASES)
def test_score_distress_escalates_crisis_phrases(phrase: str) -> None:
    state = SafariChatState()
    level, score = score_distress(phrase, state)

    assert 0.0 <= score <= 1.0
    assert level in {DistressLevel.HIGH, DistressLevel.CRITICAL}
    assert score >= 0.68


@given(SAFE_TEXT, st.floats(min_value=0.0, max_value=1.0))
def test_score_distress_stays_bounded(text: str, prior_score: float) -> None:
    state = SafariChatState(distress_score=prior_score)
    level, score = score_distress(text, state)

    assert 0.0 <= score <= 1.0
    assert isinstance(level, DistressLevel)
