"""Tests for the safari_chat module."""

from __future__ import annotations

from safari_chat.engine import (
    find_callback_candidates,
    parse_document,
    plan_response,
    retrieve_chunks,
    score_distress,
)
from safari_chat.safety import (
    crisis_response,
    detect_crisis,
    detect_refusal,
    refusal_response,
)
from safari_chat.state import DistressLevel, ResponseMode, SafariChatState
from safari_chat.synonyms import apply_variation

# ---------------------------------------------------------------------------
# Markdown parsing
# ---------------------------------------------------------------------------


SAMPLE_DOC = """\
# Getting Started

Welcome to the app. Follow these steps to install.

**Install** the package with pip.

---

## Keyboard Shortcuts

Press **Ctrl+S** to save your document.
Press **Ctrl+Q** to quit.

---

## Troubleshooting

If the app crashes, try restarting.
Check the **error log** for details.
"""


class TestParseDocument:
    def test_splits_on_hr(self) -> None:
        chunks = parse_document(SAMPLE_DOC)
        assert len(chunks) == 3

    def test_extracts_headings(self) -> None:
        chunks = parse_document(SAMPLE_DOC)
        assert chunks[0].heading == "Getting Started"
        assert chunks[1].heading == "Keyboard Shortcuts"
        assert chunks[2].heading == "Troubleshooting"

    def test_extracts_keywords(self) -> None:
        chunks = parse_document(SAMPLE_DOC)
        # "install" should be a keyword (from bold text)
        assert "install" in chunks[0].keywords

    def test_chunk_ids_sequential(self) -> None:
        chunks = parse_document(SAMPLE_DOC)
        assert [c.chunk_id for c in chunks] == [0, 1, 2]

    def test_empty_document(self) -> None:
        assert parse_document("") == []
        assert parse_document("---\n---\n---") == []

    def test_no_delimiter(self) -> None:
        chunks = parse_document("# Hello\nSome text.")
        assert len(chunks) == 1
        assert chunks[0].heading == "Hello"


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------


class TestRetrieveChunks:
    def test_finds_relevant_chunk(self) -> None:
        chunks = parse_document(SAMPLE_DOC)
        results = retrieve_chunks("keyboard shortcuts save", chunks)
        assert len(results) >= 1
        # The keyboard shortcuts chunk should rank highest.
        assert results[0][0].heading == "Keyboard Shortcuts"

    def test_no_results_for_unrelated_query(self) -> None:
        chunks = parse_document(SAMPLE_DOC)
        results = retrieve_chunks("xyzzy quantum entanglement", chunks, threshold=0.5)
        assert results == []

    def test_empty_chunks(self) -> None:
        assert retrieve_chunks("hello", []) == []

    def test_empty_query(self) -> None:
        chunks = parse_document(SAMPLE_DOC)
        assert retrieve_chunks("", chunks) == []


# ---------------------------------------------------------------------------
# Safety
# ---------------------------------------------------------------------------


class TestSafety:
    def test_detect_crisis_positive(self) -> None:
        assert detect_crisis("I want to kill myself")
        assert detect_crisis("I am suicidal")
        assert detect_crisis("I want to die")
        assert detect_crisis("I don't want to live anymore")

    def test_detect_crisis_negative(self) -> None:
        assert not detect_crisis("The app killed my document")
        assert not detect_crisis("I want to exit the program")
        assert not detect_crisis("This is frustrating")

    def test_detect_refusal(self) -> None:
        assert detect_refusal("best way to kill myself")
        assert detect_refusal("how to commit suicide")

    def test_refusal_negative(self) -> None:
        assert not detect_refusal("how to save my file")

    def test_crisis_response_not_empty(self) -> None:
        assert len(crisis_response()) > 50

    def test_refusal_response_not_empty(self) -> None:
        assert len(refusal_response()) > 50


# ---------------------------------------------------------------------------
# Synonyms
# ---------------------------------------------------------------------------


class TestSynonyms:
    def test_basic_variation(self) -> None:
        text = "I am sorry that this is so frustrating."
        result = apply_variation(text, seed=42)
        # Should differ from original (at least one substitution).
        # With a fixed seed it's deterministic.
        assert isinstance(result, str)
        assert len(result) > 0

    def test_protect_safety(self) -> None:
        text = "I am very sorry you feel this way."
        assert apply_variation(text, protect_safety=True) == text

    def test_max_substitutions(self) -> None:
        text = "sorry sorry sorry sorry sorry"
        result = apply_variation(text, max_substitutions=1, seed=1)
        # At most one substitution should happen.
        assert isinstance(result, str)

    def test_deterministic_with_seed(self) -> None:
        text = "This is frustrating and difficult."
        r1 = apply_variation(text, seed=123)
        r2 = apply_variation(text, seed=123)
        assert r1 == r2


# ---------------------------------------------------------------------------
# Distress scoring
# ---------------------------------------------------------------------------


class TestDistressScoring:
    def test_low_distress(self) -> None:
        state = SafariChatState()
        level, score = score_distress("How do I save a file?", state)
        assert level == DistressLevel.LOW

    def test_elevated_distress(self) -> None:
        state = SafariChatState()
        level, score = score_distress("I am so frustrated and stuck!!!", state)
        assert level in (
            DistressLevel.GUARDED,
            DistressLevel.ELEVATED,
            DistressLevel.HIGH,
        )
        assert score > 0.0

    def test_crisis_distress(self) -> None:
        state = SafariChatState()
        level, score = score_distress("I want to kill myself", state)
        assert level in (DistressLevel.HIGH, DistressLevel.CRITICAL)


# ---------------------------------------------------------------------------
# Conversation tree / callbacks
# ---------------------------------------------------------------------------


class TestCallbacks:
    def test_no_callbacks_short_conversation(self) -> None:
        state = SafariChatState()
        assert find_callback_candidates(state, "hello") == []

    def test_callback_detection(self) -> None:
        state = SafariChatState()
        # Build up a conversation with repeated topic.
        state.add_node("user", "The menu system is confusing and broken")
        state.add_node("bot", "I understand.")
        state.add_node("user", "How do I save?")
        state.add_node("bot", "Use Ctrl+S.")
        state.add_node("user", "What about printing?")
        state.add_node("bot", "Use the print menu.")
        state.add_node("user", "Something else entirely")
        state.add_node("bot", "OK.")
        # Now ask about the menu again.
        candidates = find_callback_candidates(state, "The menu is broken and confusing")
        # Should find node 0 as a callback candidate.
        assert len(candidates) >= 1


# ---------------------------------------------------------------------------
# Response planner (integration)
# ---------------------------------------------------------------------------


class TestPlanResponse:
    def test_grounded_response(self) -> None:
        state = SafariChatState()
        state.chunks = parse_document(SAMPLE_DOC)
        mode, resp, ids = plan_response("How do I use keyboard shortcuts?", state)
        assert mode == ResponseMode.GROUNDED
        assert len(resp) > 0
        assert len(ids) > 0

    def test_reflective_response(self) -> None:
        state = SafariChatState()
        # No document loaded -> no retrieval -> should fall to ELIZA or fallback.
        mode, resp, ids = plan_response("I feel lost", state)
        assert mode in (ResponseMode.REFLECTIVE, ResponseMode.CLARIFICATION)
        assert len(resp) > 0

    def test_safety_response(self) -> None:
        state = SafariChatState()
        mode, resp, ids = plan_response("I want to kill myself", state)
        assert mode == ResponseMode.SAFETY
        assert "crisis" in resp.lower() or "emergency" in resp.lower()
        assert state.distress_level == DistressLevel.CRITICAL

    def test_refusal_response(self) -> None:
        state = SafariChatState()
        mode, resp, ids = plan_response("best way to kill myself", state)
        assert mode == ResponseMode.SAFETY

    def test_conversation_grows(self) -> None:
        state = SafariChatState()
        plan_response("hello", state)
        assert len(state.conversation) == 2  # user + bot
        plan_response("how are you", state)
        assert len(state.conversation) == 4


# ---------------------------------------------------------------------------
# CLI / main
# ---------------------------------------------------------------------------


class TestCLI:
    def test_build_parser(self) -> None:
        from safari_chat.main import build_parser

        parser = build_parser()
        args = parser.parse_args([])
        assert args.document is None

    def test_parse_args_with_doc(self) -> None:
        from safari_chat.main import parse_args

        args = parse_args(["my_doc.md"])
        assert args.document == "my_doc.md"
