"""Tests for the branching logic in safari_chat."""

from __future__ import annotations

from safari_chat.engine import parse_document, plan_response
from safari_chat.state import ResponseMode, SafariChatState

# ---------------------------------------------------------------------------
# Sample Markdown with branches
# ---------------------------------------------------------------------------

BRANCH_DOC = """\
# Main Menu

The Main Menu is the central hub.

**Need help with saving?**
- [Disk Full error](#Disk Full Error)
- [Finding Files](#Finding Files)

---

## Disk Full Error

Your storage device is full.

1. Delete old files.
2. Use a different folder.

---

## Finding Files

If you lost your file:

1. Check current folder.
2. Check external drives.
"""


class TestBranchParsing:
    def test_extracts_branches(self) -> None:
        chunks = parse_document(BRANCH_DOC)
        assert len(chunks) == 3
        # Main Menu chunk should have 2 branches
        assert len(chunks[0].branches) == 2
        assert chunks[0].branches[0] == ("Disk Full error", "Disk Full Error")
        assert chunks[0].branches[1] == ("Finding Files", "Finding Files")

    def test_no_branches_in_other_chunks(self) -> None:
        chunks = parse_document(BRANCH_DOC)
        assert len(chunks[1].branches) == 0
        assert len(chunks[2].branches) == 0


class TestBranchingLogic:
    def test_branch_labels_in_response(self) -> None:
        chunks = parse_document(BRANCH_DOC)
        state = SafariChatState(chunks=chunks)

        mode, resp, cids = plan_response("tell me about the main menu", state)
        assert mode == ResponseMode.GROUNDED
        assert "Disk Full error" in resp
        assert "Finding Files" in resp

    def test_exact_branch_match_navigation(self) -> None:
        chunks = parse_document(BRANCH_DOC)
        state = SafariChatState(chunks=chunks)

        # 1. Ask about 'Main Menu' to set the context (retrieved_chunk_ids)
        plan_response("main menu", state)

        # 2. Select a branch exactly
        mode, resp, cids = plan_response("Disk Full error", state)

        # Should land in the target chunk
        assert mode == ResponseMode.GROUNDED
        assert "Your storage device is full" in resp
        assert cids == [1]  # Disk Full Error is chunk 1

    def test_branch_match_case_insensitive(self) -> None:
        chunks = parse_document(BRANCH_DOC)
        state = SafariChatState(chunks=chunks)

        plan_response("main menu", state)

        # Use different casing
        mode, resp, cids = plan_response("DISK FULL ERROR", state)

        assert mode == ResponseMode.GROUNDED
        assert "Your storage device is full" in resp

    def test_no_match_falls_back_to_retrieval(self) -> None:
        chunks = parse_document(BRANCH_DOC)
        state = SafariChatState(chunks=chunks)

        plan_response("main menu", state)

        # Typo should not trigger exact branch match but might still hit retrieval
        mode, resp, cids = plan_response("Disk Full errrr", state)

        # It should still find the chunk via keyword retrieval if threshold allows
        assert (
            "Your storage device is full" in resp
            or 'I found help under "Disk Full Error"' in resp
        )
