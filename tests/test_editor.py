"""Unit tests for EditorArea buffer manipulation logic.

These tests instantiate EditorArea directly (no running TUI) by monkey-patching
the Widget.__init__ so Textual's app context isn't required.
"""

import pytest
from unittest.mock import MagicMock, PropertyMock, patch

from safari_writer.state import AppState, GlobalFormat
from safari_writer.screens.editor import EditorArea, EditorScreen, CTRL_BOLD, CTRL_CENTER


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_editor(text: str = "") -> EditorArea:
    """Return an EditorArea with a fresh state, bypassing Textual Widget init."""
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
    return ed


# ---------------------------------------------------------------------------
# Typing
# ---------------------------------------------------------------------------

class TestTypeChar:
    def test_basic_insert(self):
        ed = make_editor("")
        ed._type_char("a")
        assert ed.state.buffer[0] == "a"
        assert ed.state.cursor_col == 1

    def test_insert_mode_inserts(self):
        ed = make_editor("bc")
        ed.state.insert_mode = True
        ed._type_char("a")
        assert ed.state.buffer[0] == "abc"

    def test_typeover_mode_replaces(self):
        ed = make_editor("bc")
        ed.state.insert_mode = False
        ed._type_char("a")
        assert ed.state.buffer[0] == "ac"

    def test_caps_mode(self):
        ed = make_editor("")
        ed.state.caps_mode = True
        ed._type_char("a")
        assert ed.state.buffer[0] == "A"

    def test_marks_modified(self):
        ed = make_editor("")
        ed.state.modified = False
        ed._type_char("x")
        assert ed.state.modified


# ---------------------------------------------------------------------------
# Word wrap
# ---------------------------------------------------------------------------

class TestWordWrap:
    def _editor_with_margin(self, text: str, margin: int) -> EditorArea:
        ed = make_editor(text)
        ed.state.fmt.right_margin = margin
        return ed

    def test_no_wrap_under_margin(self):
        ed = self._editor_with_margin("hello", 10)
        ed._apply_word_wrap(0)
        assert ed.state.buffer == ["hello"]

    def test_wrap_at_space(self):
        ed = self._editor_with_margin("hello world", 8)
        ed.state.cursor_col = 11
        ed._apply_word_wrap(0)
        assert ed.state.buffer[0] == "hello"
        assert ed.state.buffer[1] == "world"

    def test_wrap_cursor_moves_to_next_line(self):
        """Cursor in the wrapped portion must land on the next line."""
        ed = self._editor_with_margin("hello world", 8)
        # Cursor is at end of "world" (col 11)
        ed.state.cursor_col = 11
        ed._apply_word_wrap(0)
        assert ed.state.cursor_row == 1
        assert ed.state.cursor_col == 5  # len("world")

    def test_wrap_cursor_stays_on_current_line(self):
        """Cursor before the wrap point should not move to next line."""
        ed = self._editor_with_margin("hello world", 8)
        ed.state.cursor_col = 3  # inside "hello"
        ed._apply_word_wrap(0)
        assert ed.state.cursor_row == 0
        assert ed.state.cursor_col == 3

    def test_wrap_prepends_to_existing_next_line(self):
        ed = self._editor_with_margin("", 8)
        ed.state.buffer = ["hello world", "next"]
        ed.state.cursor_col = 11
        ed._apply_word_wrap(0)
        assert ed.state.buffer[1].startswith("world")

    def test_hard_wrap_no_space(self):
        """When no space found, wrap at the margin itself."""
        ed = self._editor_with_margin("abcdefghij", 5)
        ed.state.cursor_col = 10
        ed._apply_word_wrap(0)
        assert ed.state.buffer[0] == "abcde"
        assert ed.state.buffer[1] == "fghij"


# ---------------------------------------------------------------------------
# Newline insertion
# ---------------------------------------------------------------------------

class TestInsertNewline:
    def test_splits_line(self):
        ed = make_editor("hello world")
        ed.state.cursor_col = 5
        ed._insert_newline()
        assert ed.state.buffer == ["hello", " world"]
        assert ed.state.cursor_row == 1
        assert ed.state.cursor_col == 0

    def test_enter_at_start(self):
        ed = make_editor("hello")
        ed.state.cursor_col = 0
        ed._insert_newline()
        assert ed.state.buffer == ["", "hello"]

    def test_enter_at_end(self):
        ed = make_editor("hello")
        ed.state.cursor_col = 5
        ed._insert_newline()
        assert ed.state.buffer == ["hello", ""]


# ---------------------------------------------------------------------------
# Backspace
# ---------------------------------------------------------------------------

class TestBackspace:
    def test_delete_char_before_cursor(self):
        ed = make_editor("ab")
        ed.state.cursor_col = 2
        ed._backspace()
        assert ed.state.buffer[0] == "a"
        assert ed.state.cursor_col == 1

    def test_merge_with_prev_line(self):
        ed = make_editor("hello\nworld")
        ed.state.cursor_row = 1
        ed.state.cursor_col = 0
        ed._backspace()
        assert ed.state.buffer == ["helloworld"]
        assert ed.state.cursor_row == 0
        assert ed.state.cursor_col == 5

    def test_noop_at_doc_start(self):
        ed = make_editor("hi")
        ed.state.cursor_row = 0
        ed.state.cursor_col = 0
        ed._backspace()
        assert ed.state.buffer == ["hi"]


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

class TestDeleteChar:
    def test_delete_at_cursor(self):
        ed = make_editor("abc")
        ed.state.cursor_col = 1
        ed._delete_char()
        assert ed.state.buffer[0] == "ac"

    def test_merge_next_line_at_eol(self):
        ed = make_editor("hello\nworld")
        ed.state.cursor_col = 5
        ed._delete_char()
        assert ed.state.buffer == ["helloworld"]

    def test_noop_at_doc_end(self):
        ed = make_editor("hi")
        ed.state.cursor_col = 2
        ed._delete_char()
        assert ed.state.buffer == ["hi"]


# ---------------------------------------------------------------------------
# Cut / Copy / Paste
# ---------------------------------------------------------------------------

class TestClipboard:
    def test_cut_removes_line(self):
        ed = make_editor("line1\nline2")
        ed.state.cursor_row = 0
        ed._cut()
        assert ed.state.buffer == ["line2"]
        assert ed.state.clipboard == "line1"

    def test_cut_single_line_clears(self):
        ed = make_editor("only")
        ed._cut()
        assert ed.state.buffer == [""]

    def test_copy_does_not_modify(self):
        ed = make_editor("hello\nworld")
        ed.state.cursor_row = 0
        ed._copy()
        assert ed.state.clipboard == "hello"
        assert ed.state.buffer == ["hello", "world"]

    def test_paste_inline_at_cursor(self):
        ed = make_editor("hello\nworld")
        ed.state.clipboard = "middle"
        ed.state.cursor_row = 0
        ed.state.cursor_col = 5  # end of "hello"
        ed._paste()
        assert ed.state.buffer[0] == "hellomiddle"
        assert ed.state.cursor_col == 5 + len("middle")


# ---------------------------------------------------------------------------
# Delete to EOL / undelete
# ---------------------------------------------------------------------------

class TestDeleteToEol:
    def test_deletes_rest_of_line(self):
        ed = make_editor("hello world")
        ed.state.cursor_col = 5
        ed._delete_to_eol()
        assert ed.state.buffer[0] == "hello"
        assert ed.state.last_deleted_line == " world"

    def test_undelete_restores(self):
        ed = make_editor("hello")
        ed.state.cursor_col = 5
        ed.state.last_deleted_line = " world"
        ed._undelete()
        assert ed.state.buffer[0] == "hello world"


# ---------------------------------------------------------------------------
# Control character insertion
# ---------------------------------------------------------------------------

class TestControlChars:
    def test_insert_bold_marker(self):
        ed = make_editor("hi")
        ed.state.cursor_col = 0
        ed._insert_control(CTRL_BOLD)
        assert ed.state.buffer[0][0] == CTRL_BOLD
        assert ed.state.cursor_col == 1

    def test_insert_center_marker(self):
        ed = make_editor("text")
        ed.state.cursor_col = 2
        ed._insert_control(CTRL_CENTER)
        assert ed.state.buffer[0] == "te\x03xt"


# ---------------------------------------------------------------------------
# Word count
# ---------------------------------------------------------------------------

class TestWordCount:
    def test_word_count_message(self):
        ed = make_editor("one two three")
        mock_screen = MagicMock()
        with patch.object(type(ed), "screen", new_callable=lambda: property(lambda self: mock_screen)):
            ed._word_count()
        mock_screen.set_message.assert_called_once_with("Word count (Document): 3")

    def test_word_count_multiline(self):
        ed = make_editor("one two\nthree four")
        mock_screen = MagicMock()
        with patch.object(type(ed), "screen", new_callable=lambda: property(lambda self: mock_screen)):
            ed._word_count()
        mock_screen.set_message.assert_called_once_with("Word count (Document): 4")


# ---------------------------------------------------------------------------
# Alphabetize
# ---------------------------------------------------------------------------

class TestAlphabetize:
    def test_sorts_lines(self):
        ed = make_editor("banana\napple\ncherry")
        ed._alphabetize()
        assert ed.state.buffer == ["apple", "banana", "cherry"]
        assert ed.state.cursor_row == 0
        assert ed.state.cursor_col == 0


# ---------------------------------------------------------------------------
# Case toggle
# ---------------------------------------------------------------------------

class TestCaseToggle:
    def test_lower_to_upper(self):
        ed = make_editor("hello")
        ed.state.cursor_col = 0
        ed._toggle_case_at_cursor()
        assert ed.state.buffer[0][0] == "H"

    def test_upper_to_lower(self):
        ed = make_editor("Hello")
        ed.state.cursor_col = 0
        ed._toggle_case_at_cursor()
        assert ed.state.buffer[0][0] == "h"

    def test_noop_at_eol(self):
        ed = make_editor("hi")
        ed.state.cursor_col = 2
        ed._toggle_case_at_cursor()
        assert ed.state.buffer[0] == "hi"


# ---------------------------------------------------------------------------
# Editor footer
# ---------------------------------------------------------------------------

class TestEditorFooter:
    def test_status_bar_shows_full_editor_status(self):
        state = AppState(filename="draft.sfw", insert_mode=False, caps_mode=True)
        screen = EditorScreen(state)

        with patch.object(AppState, "bytes_free", new_callable=PropertyMock, return_value=43210):
            text = screen._status_text()

        assert "Bytes Free: 43,210" in text
        assert "[Type-over]" in text
        assert "[Uppercase]" in text
        assert "[SFW]" in text

    def test_status_bar_defaults_to_txt_and_insert_mode(self):
        screen = EditorScreen(AppState())
        text = screen._status_text()

        assert "[Insert]" in text
        assert "[Lowercase]" in text
        assert "[TXT]" in text


class TestReplacePromptShortcut:
    def test_alt_h_opens_replace_prompt(self):
        ed = make_editor("hello")
        ed.refresh = MagicMock()
        mock_screen = MagicMock()
        event = MagicMock()
        event.key = "alt+h"
        event.character = None

        with patch.object(type(ed), "screen", new_callable=lambda: property(lambda self: mock_screen)):
            ed.on_key(event)

        assert ed._replace_active is True
        mock_screen.set_message.assert_called_with("Replace with: ")

    def test_backspace_deletes_prompt_input(self):
        ed = make_editor("hello")
        ed.refresh = MagicMock()
        mock_screen = MagicMock()
        ed._replace_active = True
        ed._input_buffer = "pear"

        event = MagicMock()
        event.key = "backspace"
        event.character = None

        with patch.object(type(ed), "screen", new_callable=lambda: property(lambda self: mock_screen)):
            ed._handle_prompt_key(event)

        assert ed._input_buffer == "pea"
        mock_screen.set_message.assert_called_with("Replace with: pea█")

    def test_alt_n_replaces_current_and_finds_next(self):
        ed = make_editor("hello hello")
        ed.refresh = MagicMock()
        mock_screen = MagicMock()
        ed.state.search_string = "hello"
        ed.state.replace_string = "hi"
        event = MagicMock()
        event.key = "alt+n"
        event.character = "n"

        with patch.object(type(ed), "screen", new_callable=lambda: property(lambda self: mock_screen)):
            ed.on_key(event)

        assert ed.state.buffer[0].startswith("hi ")
