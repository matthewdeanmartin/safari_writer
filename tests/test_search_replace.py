"""Tests for search, replace, and tab-stop logic."""

import pytest
from unittest.mock import MagicMock, patch

from safari_writer.state import AppState
from safari_writer.screens.editor import EditorArea


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

    # Mock screen so set_message / update_status don't fail
    mock_screen = MagicMock()
    type(ed).screen = property(lambda self: mock_screen)
    ed._mock_screen = mock_screen
    return ed


# ---------------------------------------------------------------------------
# _find_in_line
# ---------------------------------------------------------------------------

class TestFindInLine:
    def test_basic_find(self):
        ed = make_editor()
        assert ed._find_in_line("hello world", "world") == 6

    def test_not_found(self):
        ed = make_editor()
        assert ed._find_in_line("hello", "xyz") == -1

    def test_from_offset(self):
        ed = make_editor()
        assert ed._find_in_line("abcabc", "abc", 1) == 3

    def test_wildcard_matches(self):
        ed = make_editor()
        assert ed._find_in_line("hello", "h?llo") == 0

    def test_wildcard_no_match(self):
        ed = make_editor()
        assert ed._find_in_line("hello", "h?xyz") == -1

    def test_wildcard_middle(self):
        ed = make_editor()
        assert ed._find_in_line("cat", "c?t") == 0

    def test_wildcard_multiple_positions(self):
        ed = make_editor()
        # "bat" and "cat" both match "?at"; first at index 4
        line = "the bat and cat"
        assert ed._find_in_line(line, "?at") == 4


# ---------------------------------------------------------------------------
# _find_next
# ---------------------------------------------------------------------------

class TestFindNext:
    def test_finds_on_same_line(self):
        ed = make_editor("hello world")
        ed.state.search_string = "world"
        ed.state.last_search_row = 0
        ed.state.last_search_col = 0
        result = ed._find_next()
        assert result is True
        assert ed.state.cursor_row == 0
        assert ed.state.cursor_col == 6

    def test_finds_on_next_line(self):
        ed = make_editor("hello\nworld")
        ed.state.search_string = "world"
        ed.state.last_search_row = 0
        ed.state.last_search_col = 0
        result = ed._find_next()
        assert result is True
        assert ed.state.cursor_row == 1
        assert ed.state.cursor_col == 0

    def test_not_found_returns_false(self):
        ed = make_editor("hello world")
        ed.state.search_string = "xyz"
        ed.state.last_search_row = 0
        ed.state.last_search_col = 0
        result = ed._find_next()
        assert result is False

    def test_advances_search_position(self):
        ed = make_editor("aaa")
        ed.state.search_string = "a"
        ed.state.last_search_row = 0
        ed.state.last_search_col = 0
        ed._find_next()
        assert ed.state.last_search_col == 1
        ed._find_next()
        assert ed.state.last_search_col == 2

    def test_wraps_around_to_beginning(self):
        ed = make_editor("target\nsomething else")
        ed.state.search_string = "target"
        # Start searching from row 1 (past the match)
        ed.state.last_search_row = 1
        ed.state.last_search_col = 0
        result = ed._find_next()
        assert result is True
        assert ed.state.cursor_row == 0

    def test_no_search_string_returns_false(self):
        ed = make_editor("hello")
        ed.state.search_string = ""
        result = ed._find_next()
        assert result is False

    def test_wildcard_find(self):
        ed = make_editor("cat bat sat")
        ed.state.search_string = "?at"
        ed.state.last_search_row = 0
        ed.state.last_search_col = 0
        ed._find_next()
        assert ed.state.cursor_col == 0  # "cat" at 0


# ---------------------------------------------------------------------------
# _replace_all_in_line
# ---------------------------------------------------------------------------

class TestReplaceAllInLine:
    def test_simple_replace(self):
        ed = make_editor()
        line, count = ed._replace_all_in_line("hello world hello", "hello", "hi")
        assert line == "hi world hi"
        assert count == 2

    def test_no_match(self):
        ed = make_editor()
        line, count = ed._replace_all_in_line("hello", "xyz", "abc")
        assert line == "hello"
        assert count == 0

    def test_wildcard_replace(self):
        ed = make_editor()
        line, count = ed._replace_all_in_line("cat bat sat", "?at", "X")
        assert line == "X X X"
        assert count == 3

    def test_replace_with_longer_string(self):
        ed = make_editor()
        line, count = ed._replace_all_in_line("a b a", "a", "longer")
        assert line == "longer b longer"
        assert count == 2


# ---------------------------------------------------------------------------
# _global_replace
# ---------------------------------------------------------------------------

class TestGlobalReplace:
    def test_replaces_from_cursor_to_eof(self):
        ed = make_editor("apple\nbanana\napple")
        ed.state.search_string = "apple"
        ed.state.replace_string = "pear"
        ed.state.cursor_row = 0
        ed._global_replace()
        assert ed.state.buffer[0] == "pear"
        assert ed.state.buffer[2] == "pear"
        assert ed.state.modified is True

    def test_only_replaces_from_cursor_row(self):
        ed = make_editor("apple\nbanana\napple")
        ed.state.search_string = "apple"
        ed.state.replace_string = "pear"
        ed.state.cursor_row = 2  # start from row 2
        ed._global_replace()
        assert ed.state.buffer[0] == "apple"  # row 0 untouched
        assert ed.state.buffer[2] == "pear"

    def test_reports_count(self):
        ed = make_editor("x x x")
        ed.state.search_string = "x"
        ed.state.replace_string = "y"
        ed.state.cursor_row = 0
        ed._global_replace()
        ed._mock_screen.set_message.assert_called_with("Replaced 3 occurrence(s)")

    def test_no_search_string_shows_message(self):
        ed = make_editor("hello")
        ed.state.search_string = ""
        ed._global_replace()
        ed._mock_screen.set_message.assert_called()


# ---------------------------------------------------------------------------
# _replace_current_and_find_next
# ---------------------------------------------------------------------------

class TestReplaceCurrentAndFindNext:
    def test_replaces_at_cursor(self):
        ed = make_editor("hello world hello")
        ed.state.search_string = "hello"
        ed.state.replace_string = "hi"
        ed.state.cursor_row = 0
        ed.state.cursor_col = 0
        ed.state.last_search_row = 0
        ed.state.last_search_col = 0
        ed._replace_current_and_find_next()
        # First "hello" replaced
        assert ed.state.buffer[0].startswith("hi ")
        assert ed.state.modified is True

    def test_moves_to_next_match_after_replace(self):
        ed = make_editor("hello hello")
        ed.state.search_string = "hello"
        ed.state.replace_string = "hi"
        ed.state.cursor_row = 0
        ed.state.cursor_col = 0
        ed.state.last_search_row = 0
        ed.state.last_search_col = 0
        ed._replace_current_and_find_next()
        # After replacing "hello" at 0, cursor should be on the second "hello"
        assert ed.state.cursor_col == 3  # "hi " = 3 chars, second match starts there


# ---------------------------------------------------------------------------
# Tab forward
# ---------------------------------------------------------------------------

class TestTabForward:
    def test_moves_to_next_tab_stop(self):
        ed = make_editor("hello")
        ed.state.cursor_col = 0
        ed.state.insert_mode = False
        ed._tab_forward()
        assert ed.state.cursor_col == 5  # first tab stop at col 5

    def test_inserts_spaces_in_insert_mode(self):
        ed = make_editor("hello")
        ed.state.cursor_col = 0
        ed.state.insert_mode = True
        ed._tab_forward()
        assert ed.state.cursor_col == 5
        assert ed.state.buffer[0] == "     hello"

    def test_jumps_past_current_col(self):
        ed = make_editor("hello")
        ed.state.cursor_col = 3
        ed.state.insert_mode = False
        ed._tab_forward()
        assert ed.state.cursor_col == 5  # next stop past col 3

    def test_tab_from_col_5_goes_to_10(self):
        ed = make_editor("hello world")
        ed.state.cursor_col = 5
        ed.state.insert_mode = False
        ed._tab_forward()
        assert ed.state.cursor_col == 10
