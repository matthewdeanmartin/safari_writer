"""Unit tests for ProofreaderScreen logic."""

import pytest
from unittest.mock import MagicMock, patch, mock_open

from safari_writer.state import AppState
from safari_writer.screens.proofreader import (
    ProofreaderScreen,
    _check_word,
    _extract_words,
    _dict_lookup,
    MODE_MENU,
    MODE_HIGHLIGHT,
    MODE_PRINT,
    MODE_CORRECT,
    MODE_CORRECT_MENU,
    MODE_CORRECT_WORD,
    MODE_CORRECT_CONFIRM,
    MODE_DICT_SEARCH,
    MODE_DICT_RESULTS,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_screen(buffer: list[str] | None = None) -> ProofreaderScreen:
    state = AppState()
    if buffer is not None:
        state.buffer = buffer
    with patch("textual.screen.Screen.__init__", return_value=None):
        screen = ProofreaderScreen.__new__(ProofreaderScreen)
        screen._state = state
        screen._checker = None  # no real dictionary in unit tests
        screen._personal = set()
        screen._mode = MODE_MENU
        screen._input_buf = ""
        screen._words = []
        screen._scan_idx = 0
        screen._errors = []
        screen._current_error = None
        screen._replacement = ""
        screen._dict_results = []
        screen._dict_page = 0
        screen._dict_prefix = ""
        screen._from_correct = False
    # Stub UI methods — patch instance methods directly
    screen._set_message = MagicMock()
    screen._set_body = MagicMock()
    screen._set_help = MagicMock()
    return screen


def make_key(key: str, character: str | None = None):
    """Create a minimal fake key event."""
    ev = MagicMock()
    ev.key = key
    ev.character = character if character is not None else (key if len(key) == 1 else None)
    ev.stop = MagicMock()
    return ev


# ---------------------------------------------------------------------------
# _extract_words
# ---------------------------------------------------------------------------

class TestExtractWords:
    def test_simple_line(self):
        words = _extract_words(["hello world"])
        assert ("hello", 0) in [(w, c) for (r, c, w) in words]
        assert ("world", 6) in [(w, c) for (r, c, w) in words]

    def test_multiple_lines(self):
        words = _extract_words(["foo", "bar"])
        rows = [r for (r, c, w) in words]
        assert 0 in rows
        assert 1 in rows

    def test_strips_control_chars(self):
        # Control chars should be treated as whitespace, not included in words
        words = _extract_words(["\x01bold\x01 text"])
        word_strs = [w for (r, c, w) in words]
        assert "bold" in word_strs
        assert "text" in word_strs
        # No word should contain a control character
        for w in word_strs:
            assert all(ord(ch) >= 32 for ch in w)

    def test_empty_buffer(self):
        assert _extract_words([""]) == []

    def test_numbers_not_extracted(self):
        words = _extract_words(["abc 123 def"])
        word_strs = [w for (r, c, w) in words]
        assert "123" not in word_strs
        assert "abc" in word_strs
        assert "def" in word_strs

    def test_punctuation_stripped_in_extraction(self):
        words = _extract_words(["hello, world!"])
        # The regex [A-Za-z']+ keeps apostrophes but not punctuation
        word_strs = [w for (r, c, w) in words]
        assert any("hello" in w for w in word_strs)


# ---------------------------------------------------------------------------
# _check_word
# ---------------------------------------------------------------------------

class TestCheckWord:
    def test_no_checker_always_ok(self):
        assert _check_word("anythng", None, set(), set()) is True

    def test_kept_word_passes(self):
        assert _check_word("misspeled", None, {"misspeled"}, set()) is True

    def test_personal_dict_word_passes(self):
        assert _check_word("misspeled", None, set(), {"misspeled"}) is True

    def test_non_alpha_start_passes(self):
        assert _check_word("123abc", None, set(), set()) is True

    def test_empty_string_passes(self):
        assert _check_word("", None, set(), set()) is True

    def test_checker_called_for_unknown(self):
        checker = MagicMock()
        checker.check.return_value = False
        result = _check_word("zxqfoo", checker, set(), set())
        assert result is False
        checker.check.assert_called_once()

    def test_checker_called_strips_punctuation(self):
        checker = MagicMock()
        checker.check.return_value = True
        _check_word("hello,", checker, set(), set())
        checker.check.assert_called_with("hello")


# ---------------------------------------------------------------------------
# Mode transitions
# ---------------------------------------------------------------------------

class TestModeTransitions:
    def test_highlight_mode_entered(self):
        screen = make_screen(["good text here"])
        screen._render_highlight_scan = MagicMock()
        screen._enter_highlight()
        assert screen._mode == MODE_HIGHLIGHT
        screen._render_highlight_scan.assert_called_once()

    def test_print_mode_no_errors(self):
        screen = make_screen(["hello world"])
        # checker is None → all words pass → no errors
        screen._enter_print()
        assert screen._mode == MODE_PRINT
        assert screen._errors == []

    def test_print_mode_with_fake_errors(self):
        screen = make_screen(["hello world"])
        checker = MagicMock()
        checker.check.return_value = False
        screen._checker = checker
        screen._enter_print()
        assert len(screen._errors) > 0

    def test_correct_mode_no_errors_goes_to_done(self):
        screen = make_screen(["hello world"])
        screen._advance_to_next_error = MagicMock()
        screen._enter_correct()
        assert screen._mode == MODE_CORRECT
        screen._advance_to_next_error.assert_called_once()

    def test_advance_no_errors_shows_complete(self):
        screen = make_screen(["hello world"])
        # checker None → no errors → advance should complete immediately
        screen._words = _extract_words(["hello world"])
        screen._scan_idx = 0
        screen._advance_to_next_error()
        assert screen._current_error is None
        assert screen._mode == MODE_MENU  # done → back to menu-like state


# ---------------------------------------------------------------------------
# Correction workflow
# ---------------------------------------------------------------------------

class TestCorrectionWorkflow:
    def _screen_with_error(self) -> ProofreaderScreen:
        screen = make_screen(["teh quick brown fox"])
        screen._current_error = (0, 0, "teh")
        screen._mode = MODE_CORRECT_MENU
        return screen

    def test_enter_keeps_word(self):
        screen = self._screen_with_error()
        screen._advance_to_next_error = MagicMock()
        ev = make_key("enter")
        screen._handle_correct_menu_key("enter")
        assert "teh" in screen._state.kept_spellings

    def test_c_enters_correct_word_mode(self):
        screen = self._screen_with_error()
        screen._handle_correct_menu_key("c")
        assert screen._mode == MODE_CORRECT_WORD

    def test_typing_replacement(self):
        screen = self._screen_with_error()
        screen._mode = MODE_CORRECT_WORD
        screen._input_buf = ""
        ev = make_key("t", "t")
        screen._handle_correct_word_key("t", ev)
        assert screen._input_buf == "t"

    def test_backspace_in_replacement(self):
        screen = self._screen_with_error()
        screen._mode = MODE_CORRECT_WORD
        screen._input_buf = "th"
        ev = make_key("backspace")
        screen._handle_correct_word_key("backspace", ev)
        assert screen._input_buf == "t"

    def test_enter_with_replacement_prompts_confirm(self):
        screen = self._screen_with_error()
        screen._mode = MODE_CORRECT_WORD
        screen._input_buf = "the"
        ev = make_key("enter")
        screen._handle_correct_word_key("enter", ev)
        assert screen._mode == MODE_CORRECT_CONFIRM
        assert screen._replacement == "the"

    def test_enter_empty_replacement_stays_in_word_mode(self):
        screen = self._screen_with_error()
        screen._mode = MODE_CORRECT_WORD
        screen._input_buf = ""
        ev = make_key("enter")
        screen._handle_correct_word_key("enter", ev)
        # Should not advance — no replacement typed
        assert screen._mode == MODE_CORRECT_WORD

    def test_confirm_y_applies_correction(self):
        screen = self._screen_with_error()
        screen._mode = MODE_CORRECT_CONFIRM
        screen._replacement = "the"
        screen._advance_to_next_error = MagicMock()
        screen._handle_correct_confirm_key("y")
        assert screen._state.buffer[0].startswith("the")
        screen._advance_to_next_error.assert_called_once()

    def test_confirm_n_returns_to_menu(self):
        screen = self._screen_with_error()
        screen._mode = MODE_CORRECT_CONFIRM
        screen._replacement = "the"
        screen._handle_correct_confirm_key("n")
        assert screen._mode == MODE_CORRECT_MENU

    def test_esc_in_correct_menu_returns_to_main_menu(self):
        screen = self._screen_with_error()
        screen._enter_menu = MagicMock()
        screen._handle_correct_menu_key("escape")
        screen._enter_menu.assert_called_once()


# ---------------------------------------------------------------------------
# Apply correction to buffer
# ---------------------------------------------------------------------------

class TestApplyCorrection:
    def test_replaces_word_in_buffer(self):
        screen = make_screen(["teh quick brown fox"])
        screen._current_error = (0, 0, "teh")
        screen._replacement = "the"
        screen._advance_to_next_error = MagicMock()
        screen._apply_correction()
        assert screen._state.buffer[0] == "the quick brown fox"

    def test_marks_buffer_modified(self):
        screen = make_screen(["teh quick brown fox"])
        screen._current_error = (0, 0, "teh")
        screen._replacement = "the"
        screen._advance_to_next_error = MagicMock()
        screen._apply_correction()
        assert screen._state.modified is True

    def test_replacement_in_middle_of_line(self):
        screen = make_screen(["the quikc brown fox"])
        screen._current_error = (0, 4, "quikc")
        screen._replacement = "quick"
        screen._advance_to_next_error = MagicMock()
        screen._apply_correction()
        assert screen._state.buffer[0] == "the quick brown fox"


# ---------------------------------------------------------------------------
# Dictionary search
# ---------------------------------------------------------------------------

class TestDictSearch:
    def test_enter_dict_search_mode(self):
        screen = make_screen()
        screen._enter_dict_search(from_correct=False)
        assert screen._mode == MODE_DICT_SEARCH
        assert screen._from_correct is False

    def test_short_prefix_rejected(self):
        screen = make_screen()
        screen._mode = MODE_DICT_SEARCH
        screen._input_buf = "a"
        ev = make_key("enter")
        screen._handle_dict_search_key("enter", ev)
        assert screen._mode == MODE_DICT_SEARCH  # stays in search

    def test_valid_prefix_calls_lookup(self):
        screen = make_screen()
        screen._mode = MODE_DICT_SEARCH
        screen._input_buf = "he"
        screen._show_dict_results_page = MagicMock()
        with patch("safari_writer.screens.proofreader._dict_lookup", return_value=["hello", "help"]):
            ev = make_key("enter")
            screen._handle_dict_search_key("enter", ev)
        screen._show_dict_results_page.assert_called_once()
        assert screen._dict_results == ["hello", "help"]

    def test_backspace_in_search(self):
        screen = make_screen()
        screen._mode = MODE_DICT_SEARCH
        screen._input_buf = "he"
        ev = make_key("backspace")
        screen._handle_dict_search_key("backspace", ev)
        assert screen._input_buf == "h"

    def test_typing_adds_to_prefix(self):
        screen = make_screen()
        screen._mode = MODE_DICT_SEARCH
        screen._input_buf = "h"
        ev = make_key("e", "e")
        screen._handle_dict_search_key("e", ev)
        assert screen._input_buf == "he"

    def test_results_paging_next(self):
        screen = make_screen()
        screen._dict_results = [f"word{i}" for i in range(200)]
        screen._dict_page = 0
        screen._show_dict_results_page = MagicMock()
        screen._mode = MODE_DICT_RESULTS
        screen._handle_dict_results_key("pagedown")
        assert screen._dict_page == 1
        screen._show_dict_results_page.assert_called_once()

    def test_results_paging_prev(self):
        screen = make_screen()
        screen._dict_results = [f"word{i}" for i in range(200)]
        screen._dict_page = 1
        screen._show_dict_results_page = MagicMock()
        screen._mode = MODE_DICT_RESULTS
        screen._handle_dict_results_key("pageup")
        assert screen._dict_page == 0
        screen._show_dict_results_page.assert_called_once()

    def test_results_no_prev_at_page_0(self):
        screen = make_screen()
        screen._dict_results = [f"word{i}" for i in range(200)]
        screen._dict_page = 0
        screen._show_dict_results_page = MagicMock()
        screen._mode = MODE_DICT_RESULTS
        screen._handle_dict_results_key("pageup")
        assert screen._dict_page == 0
        screen._show_dict_results_page.assert_not_called()


# ---------------------------------------------------------------------------
# Personal dictionary
# ---------------------------------------------------------------------------

class TestPersonalDictionary:
    def test_save_kept_words(self, tmp_path):
        screen = make_screen()
        screen._state.kept_spellings = {"foo", "bar"}
        screen._personal = set()
        screen._enter_menu = MagicMock()
        filename = str(tmp_path / "personal.txt")
        screen._save_personal_dict(filename)
        text = open(filename).read()
        words = set(text.split())
        assert words == {"foo", "bar"}

    def test_save_capped_at_256(self, tmp_path):
        screen = make_screen()
        screen._state.kept_spellings = {f"word{i}" for i in range(300)}
        screen._personal = set()
        screen._enter_menu = MagicMock()
        filename = str(tmp_path / "personal.txt")
        screen._save_personal_dict(filename)
        words = open(filename).read().split()
        assert len(words) <= 256

    def test_save_empty_does_not_write(self, tmp_path):
        screen = make_screen()
        screen._state.kept_spellings = set()
        screen._personal = set()
        screen._enter_menu = MagicMock()
        filename = str(tmp_path / "personal.txt")
        screen._save_personal_dict(filename)
        import os
        assert not os.path.exists(filename)

    def test_load_personal_dict(self, tmp_path):
        filename = tmp_path / "personal.txt"
        filename.write_text("foo bar baz")
        screen = make_screen()
        screen._enter_menu = MagicMock()
        screen._load_personal_dict(str(filename))
        assert "foo" in screen._personal
        assert "bar" in screen._personal
        assert "baz" in screen._personal

    def test_load_personal_dict_missing_file(self):
        screen = make_screen()
        screen._enter_menu = MagicMock()
        screen._load_personal_dict("/nonexistent/path/personal.txt")
        # Should show error message and return to menu without crashing
        screen._set_message.assert_called()
        screen._enter_menu.assert_called_once()

    def test_loaded_words_skip_checker(self):
        screen = make_screen()
        screen._personal = {"jabberwocky"}
        checker = MagicMock()
        checker.check.return_value = False
        assert _check_word("jabberwocky", checker, set(), screen._personal) is True
        checker.check.assert_not_called()

    def test_kept_spellings_persist_across_words(self):
        screen = make_screen(["teh teh teh"])
        screen._state.kept_spellings = {"teh"}
        # All instances of "teh" should pass because it's kept
        words = _extract_words(screen._state.buffer)
        for (r, c, w) in words:
            assert _check_word(w, None, screen._state.kept_spellings, set()) is True


# ---------------------------------------------------------------------------
# Exit
# ---------------------------------------------------------------------------

class TestExit:
    def test_exit_pops_screen(self):
        screen = make_screen()
        mock_app = MagicMock()
        object.__setattr__(screen, "_app", mock_app)
        with patch.object(type(screen), "app", new_callable=lambda: property(lambda self: mock_app)):
            screen.action_exit_proofreader()
        mock_app.pop_screen.assert_called_once()
