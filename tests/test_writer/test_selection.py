"""Tests for text selection, selection-aware cut/copy/paste, word count, alphabetize."""

import pytest
from unittest.mock import MagicMock, patch

from safari_writer.state import AppState
from safari_writer.screens.editor import (
    EditorArea,
    _to_flat,
    _from_flat,
    _selection_range,
)


def make_editor(text: str = "") -> EditorArea:
    state = AppState()
    state.buffer = text.split("\n") if text else [""]
    state.cursor_row = 0
    state.cursor_col = 0

    with patch("textual.widget.Widget.__init__", return_value=None):
        ed = EditorArea.__new__(EditorArea)
        ed.state = state
        ed.tab_stops = set(range(5, 81, 5))
        ed._search_active = False
        ed._replace_active = False
        ed._heading_active = False
        ed._chain_active = False
        ed._input_buffer = ""
        ed._last_undo_action = ""

    mock_screen = MagicMock()
    type(ed).screen = property(lambda self: mock_screen)
    ed._mock_screen = mock_screen
    return ed


# ---------------------------------------------------------------------------
# Flat-position helpers
# ---------------------------------------------------------------------------


class TestFlatHelpers:
    def test_to_flat_first_line(self):
        buf = ["hello", "world"]
        assert _to_flat(buf, 0, 0) == 0
        assert _to_flat(buf, 0, 5) == 5

    def test_to_flat_second_line(self):
        buf = ["hello", "world"]
        # row 1 col 0 = 5 (hello) + 1 (newline) = 6
        assert _to_flat(buf, 1, 0) == 6
        assert _to_flat(buf, 1, 3) == 9

    def test_from_flat_first_line(self):
        buf = ["hello", "world"]
        assert _from_flat(buf, 0) == (0, 0)
        assert _from_flat(buf, 4) == (0, 4)

    def test_from_flat_second_line(self):
        buf = ["hello", "world"]
        assert _from_flat(buf, 6) == (1, 0)
        assert _from_flat(buf, 9) == (1, 3)

    def test_roundtrip(self):
        buf = ["abc", "de", "fghij"]
        for row in range(len(buf)):
            for col in range(len(buf[row]) + 1):
                flat = _to_flat(buf, row, col)
                assert _from_flat(buf, flat) == (row, col)


class TestSelectionRange:
    def test_anchor_before_cursor(self):
        buf = ["hello world"]
        start, end = _selection_range(buf, (0, 0), (0, 5))
        assert start == (0, 0)
        assert end == (0, 5)

    def test_cursor_before_anchor(self):
        buf = ["hello world"]
        start, end = _selection_range(buf, (0, 5), (0, 0))
        assert start == (0, 0)
        assert end == (0, 5)

    def test_equal_returns_same(self):
        buf = ["hello"]
        start, end = _selection_range(buf, (0, 2), (0, 2))
        assert start == end == (0, 2)


# ---------------------------------------------------------------------------
# _has_selection / _begin_selection / _clear_selection
# ---------------------------------------------------------------------------


class TestSelectionState:
    def test_no_selection_by_default(self):
        ed = make_editor("hello")
        assert ed._has_selection() is False

    def test_begin_selection_sets_anchor(self):
        ed = make_editor("hello")
        ed.state.cursor_row = 0
        ed.state.cursor_col = 2
        ed._begin_selection()
        assert ed.state.selection_anchor == (0, 2)

    def test_begin_selection_does_not_overwrite(self):
        ed = make_editor("hello")
        ed.state.selection_anchor = (0, 1)
        ed.state.cursor_col = 3
        ed._begin_selection()
        assert ed.state.selection_anchor == (0, 1)  # unchanged

    def test_has_selection_when_cursor_moved(self):
        ed = make_editor("hello")
        ed.state.selection_anchor = (0, 0)
        ed.state.cursor_col = 3
        assert ed._has_selection() is True

    def test_no_selection_when_cursor_equals_anchor(self):
        ed = make_editor("hello")
        ed.state.selection_anchor = (0, 2)
        ed.state.cursor_col = 2
        assert ed._has_selection() is False

    def test_clear_selection(self):
        ed = make_editor("hello")
        ed.state.selection_anchor = (0, 0)
        ed.state.cursor_col = 3
        ed._clear_selection()
        assert ed.state.selection_anchor is None
        assert ed._has_selection() is False


# ---------------------------------------------------------------------------
# _selected_text
# ---------------------------------------------------------------------------


class TestSelectedText:
    def test_single_line_selection(self):
        ed = make_editor("hello world")
        ed.state.selection_anchor = (0, 6)
        ed.state.cursor_col = 11
        assert ed._selected_text() == "world"

    def test_single_line_reversed(self):
        ed = make_editor("hello world")
        ed.state.selection_anchor = (0, 11)
        ed.state.cursor_col = 6
        assert ed._selected_text() == "world"

    def test_multiline_selection(self):
        ed = make_editor("hello\nworld")
        ed.state.selection_anchor = (0, 0)
        ed.state.cursor_row = 1
        ed.state.cursor_col = 5
        assert ed._selected_text() == "hello\nworld"

    def test_partial_multiline(self):
        ed = make_editor("abcde\nfghij")
        ed.state.selection_anchor = (0, 2)  # "cde"
        ed.state.cursor_row = 1
        ed.state.cursor_col = 3  # "fgh"
        text = ed._selected_text()
        assert text == "cde\nfgh"

    def test_no_selection_returns_empty(self):
        ed = make_editor("hello")
        assert ed._selected_text() == ""


# ---------------------------------------------------------------------------
# _delete_selection
# ---------------------------------------------------------------------------


class TestDeleteSelection:
    def test_delete_within_line(self):
        ed = make_editor("hello world")
        ed.state.selection_anchor = (0, 6)
        ed.state.cursor_col = 11
        ed._delete_selection()
        assert ed.state.buffer[0] == "hello "
        assert ed.state.cursor_col == 6
        assert ed.state.selection_anchor is None

    def test_delete_whole_line(self):
        ed = make_editor("hello world")
        ed.state.selection_anchor = (0, 0)
        ed.state.cursor_col = 11
        ed._delete_selection()
        assert ed.state.buffer[0] == ""

    def test_delete_across_lines(self):
        ed = make_editor("hello\nworld")
        ed.state.selection_anchor = (0, 3)  # from "lo"
        ed.state.cursor_row = 1
        ed.state.cursor_col = 3  # up to "wor"
        ed._delete_selection()
        assert ed.state.buffer == ["helld"]
        assert ed.state.cursor_row == 0
        assert ed.state.cursor_col == 3

    def test_delete_marks_modified(self):
        ed = make_editor("hello")
        ed.state.selection_anchor = (0, 0)
        ed.state.cursor_col = 5
        ed.state.modified = False
        ed._delete_selection()
        assert ed.state.modified is True

    def test_delete_reversed_selection(self):
        ed = make_editor("hello world")
        # Anchor after cursor — should still work
        ed.state.selection_anchor = (0, 11)
        ed.state.cursor_col = 6
        ed._delete_selection()
        assert ed.state.buffer[0] == "hello "
        assert ed.state.cursor_col == 6


# ---------------------------------------------------------------------------
# Cut with selection
# ---------------------------------------------------------------------------


class TestCutWithSelection:
    def test_cut_selection(self):
        ed = make_editor("hello world")
        ed.state.selection_anchor = (0, 6)
        ed.state.cursor_col = 11
        ed._cut()
        assert ed.state.clipboard == "world"
        assert ed.state.buffer[0] == "hello "

    def test_cut_no_selection_cuts_line(self):
        ed = make_editor("line1\nline2")
        ed.state.cursor_row = 0
        ed._cut()
        assert ed.state.clipboard == "line1"
        assert ed.state.buffer == ["line2"]


# ---------------------------------------------------------------------------
# Copy with selection
# ---------------------------------------------------------------------------


class TestCopyWithSelection:
    def test_copy_selection(self):
        ed = make_editor("hello world")
        ed.state.selection_anchor = (0, 0)
        ed.state.cursor_col = 5
        ed._copy()
        assert ed.state.clipboard == "hello"
        assert ed.state.buffer[0] == "hello world"  # unchanged

    def test_copy_no_selection_copies_line(self):
        ed = make_editor("hello\nworld")
        ed.state.cursor_row = 0
        ed._copy()
        assert ed.state.clipboard == "hello"


# ---------------------------------------------------------------------------
# Paste (inline, and replacing selection)
# ---------------------------------------------------------------------------


class TestPaste:
    def test_paste_single_line_inline(self):
        ed = make_editor("helo")
        ed.state.clipboard = "l"
        ed.state.cursor_col = 3
        ed._paste()
        assert ed.state.buffer[0] == "hello"
        assert ed.state.cursor_col == 4

    def test_paste_at_start(self):
        ed = make_editor("world")
        ed.state.clipboard = "hello "
        ed.state.cursor_col = 0
        ed._paste()
        assert ed.state.buffer[0] == "hello world"

    def test_paste_multiline(self):
        ed = make_editor("ac")
        ed.state.clipboard = "b\n"
        ed.state.cursor_col = 1  # between a and c
        ed._paste()
        assert ed.state.buffer[0] == "ab"
        assert ed.state.buffer[1] == "c"

    def test_paste_replaces_selection(self):
        ed = make_editor("hello world")
        ed.state.selection_anchor = (0, 6)
        ed.state.cursor_col = 11
        ed.state.clipboard = "there"
        ed._paste()
        assert ed.state.buffer[0] == "hello there"
        assert ed.state.selection_anchor is None

    def test_paste_noop_empty_clipboard(self):
        ed = make_editor("hello")
        ed.state.clipboard = ""
        ed._paste()
        assert ed.state.buffer[0] == "hello"


# ---------------------------------------------------------------------------
# Word count with selection
# ---------------------------------------------------------------------------


class TestWordCountWithSelection:
    def test_word_count_selection(self):
        ed = make_editor("one two three four")
        ed.state.selection_anchor = (0, 0)
        ed.state.cursor_col = 7  # "one two"
        ed._word_count()
        ed._mock_screen.set_message.assert_called_with("Word count (Selection): 2")

    def test_word_count_whole_file(self):
        ed = make_editor("one two three")
        ed._word_count()
        ed._mock_screen.set_message.assert_called_with("Word count (Document): 3")

    def test_word_count_multiline_file(self):
        ed = make_editor("one two\nthree four")
        ed._word_count()
        ed._mock_screen.set_message.assert_called_with("Word count (Document): 4")


# ---------------------------------------------------------------------------
# Alphabetize with selection
# ---------------------------------------------------------------------------


class TestAlphabetizeWithSelection:
    def test_alphabetize_selected_lines(self):
        ed = make_editor("banana\napple\ncherry\ndate")
        # Select lines 0-2 (banana, apple, cherry)
        ed.state.selection_anchor = (0, 0)
        ed.state.cursor_row = 2
        ed.state.cursor_col = 0
        ed._alphabetize()
        assert ed.state.buffer == ["apple", "banana", "cherry", "date"]
        assert ed.state.cursor_row == 0
        assert ed.state.selection_anchor is None

    def test_alphabetize_all_lines_no_selection(self):
        ed = make_editor("banana\napple\ncherry")
        ed._alphabetize()
        assert ed.state.buffer == ["apple", "banana", "cherry"]

    def test_alphabetize_selected_subset_leaves_rest(self):
        ed = make_editor("zzz\nbanana\napple\naaa")
        # Select lines 1-2 only
        ed.state.selection_anchor = (1, 0)
        ed.state.cursor_row = 2
        ed.state.cursor_col = 0
        ed._alphabetize()
        assert ed.state.buffer[0] == "zzz"
        assert ed.state.buffer[1] == "apple"
        assert ed.state.buffer[2] == "banana"
        assert ed.state.buffer[3] == "aaa"
