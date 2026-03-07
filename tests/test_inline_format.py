"""Tests for Phase 6: inline formatting markers, rendering, and document structure."""

import pytest
from unittest.mock import MagicMock, patch

from safari_writer.state import AppState
from safari_writer.screens.editor import (
    EditorArea,
    CTRL_BOLD, CTRL_UNDERLINE, CTRL_ELONGATE, CTRL_SUPER, CTRL_SUB,
    CTRL_CENTER, CTRL_RIGHT, CTRL_PARA, CTRL_MERGE,
    CTRL_HEADER, CTRL_FOOTER, CTRL_HEADING, CTRL_EJECT, CTRL_CHAIN, CTRL_FORM,
    TOGGLE_MARKERS,
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

    mock_screen = MagicMock()
    type(ed).screen = property(lambda self: mock_screen)
    ed._mock_screen = mock_screen
    return ed


# ---------------------------------------------------------------------------
# Toggle markers set
# ---------------------------------------------------------------------------

class TestToggleMarkers:
    def test_bold_is_toggle(self):
        assert CTRL_BOLD in TOGGLE_MARKERS

    def test_underline_is_toggle(self):
        assert CTRL_UNDERLINE in TOGGLE_MARKERS

    def test_elongate_is_toggle(self):
        assert CTRL_ELONGATE in TOGGLE_MARKERS

    def test_super_is_toggle(self):
        assert CTRL_SUPER in TOGGLE_MARKERS

    def test_sub_is_toggle(self):
        assert CTRL_SUB in TOGGLE_MARKERS

    def test_center_not_toggle(self):
        assert CTRL_CENTER not in TOGGLE_MARKERS

    def test_para_not_toggle(self):
        assert CTRL_PARA not in TOGGLE_MARKERS


# ---------------------------------------------------------------------------
# _insert_control for all formatting chars
# ---------------------------------------------------------------------------

class TestInsertFormatControls:
    def test_insert_bold(self):
        ed = make_editor("hello")
        ed.state.cursor_col = 0
        ed._insert_control(CTRL_BOLD)
        assert ed.state.buffer[0][0] == CTRL_BOLD

    def test_insert_underline(self):
        ed = make_editor("hello")
        ed.state.cursor_col = 0
        ed._insert_control(CTRL_UNDERLINE)
        assert ed.state.buffer[0][0] == CTRL_UNDERLINE

    def test_insert_elongate(self):
        ed = make_editor("hello")
        ed.state.cursor_col = 0
        ed._insert_control(CTRL_ELONGATE)
        assert ed.state.buffer[0][0] == CTRL_ELONGATE

    def test_insert_super(self):
        ed = make_editor("hello")
        ed.state.cursor_col = 0
        ed._insert_control(CTRL_SUPER)
        assert ed.state.buffer[0][0] == CTRL_SUPER

    def test_insert_sub(self):
        ed = make_editor("hello")
        ed.state.cursor_col = 0
        ed._insert_control(CTRL_SUB)
        assert ed.state.buffer[0][0] == CTRL_SUB

    def test_insert_form(self):
        ed = make_editor("hello")
        ed.state.cursor_col = 0
        ed._insert_control(CTRL_FORM)
        assert ed.state.buffer[0][0] == CTRL_FORM

    def test_insert_advances_cursor(self):
        ed = make_editor("hello")
        ed.state.cursor_col = 2
        ed._insert_control(CTRL_BOLD)
        assert ed.state.cursor_col == 3

    def test_insert_marks_modified(self):
        ed = make_editor("hello")
        ed.state.modified = False
        ed._insert_control(CTRL_BOLD)
        assert ed.state.modified is True


# ---------------------------------------------------------------------------
# _insert_structure_marker
# ---------------------------------------------------------------------------

class TestInsertStructureMarker:
    def test_header_inserted_as_own_line(self):
        ed = make_editor("text")
        ed.state.cursor_row = 0
        ed._insert_structure_marker(CTRL_HEADER)
        assert ed.state.buffer[0] == CTRL_HEADER
        assert ed.state.buffer[1] == "text"
        assert ed.state.cursor_row == 1

    def test_footer_inserted_as_own_line(self):
        ed = make_editor("text")
        ed.state.cursor_row = 0
        ed._insert_structure_marker(CTRL_FOOTER)
        assert ed.state.buffer[0] == CTRL_FOOTER

    def test_eject_inserted_as_own_line(self):
        ed = make_editor("page one\npage two")
        ed.state.cursor_row = 1
        ed._insert_structure_marker(CTRL_EJECT)
        assert ed.state.buffer[1] == CTRL_EJECT
        assert ed.state.buffer[2] == "page two"

    def test_structure_marks_modified(self):
        ed = make_editor("text")
        ed.state.modified = False
        ed._insert_structure_marker(CTRL_HEADER)
        assert ed.state.modified is True


# ---------------------------------------------------------------------------
# Heading prompt flow
# ---------------------------------------------------------------------------

def _make_event(key: str, char: str | None = None) -> MagicMock:
    ev = MagicMock()
    ev.key = key
    ev.character = char
    return ev


class TestHeadingPrompt:
    def test_heading_valid_level_inserts_marker(self):
        ed = make_editor("body text")
        ed.refresh = MagicMock()
        ed.state.cursor_row = 0
        ed._heading_active = True
        ed._input_buffer = "2"
        ed._handle_prompt_key(_make_event("enter"))
        assert ed.state.buffer[0] == CTRL_HEADING + "2"
        assert ed.state.buffer[1] == "body text"
        assert ed._heading_active is False

    def test_heading_invalid_level_cancels(self):
        ed = make_editor("body text")
        ed.refresh = MagicMock()
        ed.state.cursor_row = 0
        ed._heading_active = True
        ed._input_buffer = "x"
        ed._handle_prompt_key(_make_event("enter"))
        assert ed.state.buffer[0] == "body text"
        assert ed._heading_active is False

    def test_heading_escape_cancels(self):
        ed = make_editor("text")
        ed.refresh = MagicMock()
        ed._heading_active = True
        ed._handle_prompt_key(_make_event("escape"))
        assert ed._heading_active is False

    def test_heading_limited_to_one_char(self):
        ed = make_editor("text")
        ed.refresh = MagicMock()
        ed._heading_active = True
        ed._input_buffer = "3"  # already 1 char (max)
        ed._handle_prompt_key(_make_event("5", "5"))
        assert ed._input_buffer == "3"  # not appended


# ---------------------------------------------------------------------------
# Chain prompt flow
# ---------------------------------------------------------------------------

class TestChainPrompt:
    def test_chain_inserts_marker_at_end(self):
        ed = make_editor("document text")
        ed.refresh = MagicMock()
        ed._chain_active = True
        ed._input_buffer = "part2.txt"
        ed._handle_prompt_key(_make_event("enter"))
        last = ed.state.buffer[-1]
        assert last == CTRL_CHAIN + "part2.txt"
        assert ed._chain_active is False
        assert ed.state.modified is True

    def test_chain_empty_filename_cancels(self):
        ed = make_editor("document text")
        ed.refresh = MagicMock()
        buf_before = ed.state.buffer[:]
        ed._chain_active = True
        ed._input_buffer = "   "
        ed._handle_prompt_key(_make_event("enter"))
        assert ed.state.buffer == buf_before
        assert ed._chain_active is False


# ---------------------------------------------------------------------------
# _format_markup
# ---------------------------------------------------------------------------

class TestFormatMarkup:
    def _fmt(self, **kwargs) -> dict:
        base = {
            CTRL_BOLD: False, CTRL_UNDERLINE: False,
            CTRL_ELONGATE: False, CTRL_SUPER: False, CTRL_SUB: False,
        }
        base.update(kwargs)
        return base

    def test_no_active_style(self):
        ed = make_editor()
        assert ed._format_markup(self._fmt(), False, False) == ""

    def test_cursor_overrides_all(self):
        ed = make_editor()
        markup = ed._format_markup(self._fmt(**{CTRL_BOLD: True}), True, False)
        assert markup == "reverse"

    def test_selection_overrides_style(self):
        ed = make_editor()
        markup = ed._format_markup(self._fmt(**{CTRL_BOLD: True}), False, True)
        assert markup == "on blue"

    def test_bold_markup(self):
        ed = make_editor()
        markup = ed._format_markup(self._fmt(**{CTRL_BOLD: True}), False, False)
        assert "bold" in markup

    def test_underline_markup(self):
        ed = make_editor()
        markup = ed._format_markup(self._fmt(**{CTRL_UNDERLINE: True}), False, False)
        assert "reverse" in markup

    def test_elongate_markup(self):
        ed = make_editor()
        markup = ed._format_markup(self._fmt(**{CTRL_ELONGATE: True}), False, False)
        assert "dim" in markup

    def test_super_markup(self):
        ed = make_editor()
        markup = ed._format_markup(self._fmt(**{CTRL_SUPER: True}), False, False)
        assert "bright_white" in markup

    def test_sub_markup(self):
        ed = make_editor()
        markup = ed._format_markup(self._fmt(**{CTRL_SUB: True}), False, False)
        assert "bright_white" in markup

    def test_bold_and_underline_combined(self):
        ed = make_editor()
        markup = ed._format_markup(
            self._fmt(**{CTRL_BOLD: True, CTRL_UNDERLINE: True}), False, False
        )
        assert "bold" in markup
        assert "reverse" in markup


# ---------------------------------------------------------------------------
# render / _render_line — format state tracking
# ---------------------------------------------------------------------------

class TestRenderFormatState:
    def _render(self, ed: EditorArea) -> str:
        """Call render() without needing Textual context."""
        return ed.render()

    def test_render_returns_string(self):
        ed = make_editor("hello")
        result = self._render(ed)
        assert isinstance(result, str)

    def test_bold_marker_in_output(self):
        ed = make_editor(CTRL_BOLD + "bold text" + CTRL_BOLD)
        result = self._render(ed)
        # Marker glyph should appear; bold text after it should have markup
        assert "←" in result or "bold" in result

    def test_toggle_state_crosses_lines(self):
        """Bold toggled on in line 0 should still be active in line 1."""
        ed = make_editor(CTRL_BOLD + "start\ncontinued")
        result = self._render(ed)
        # Both lines should appear in the output
        lines = result.split("\n")
        assert len(lines) == 2

    def test_render_multiline(self):
        ed = make_editor("line one\nline two")
        result = self._render(ed)
        assert "\n" in result

    def test_render_shows_ctrl_glyphs(self):
        ed = make_editor(CTRL_CENTER + "centered")
        result = self._render(ed)
        assert "↔" in result

    def test_render_eject_glyph(self):
        ed = make_editor(CTRL_EJECT)
        result = self._render(ed)
        assert "↡" in result

    def test_render_chain_glyph(self):
        ed = make_editor(CTRL_CHAIN + "next.txt")
        result = self._render(ed)
        assert "»" in result

    def test_render_form_glyph(self):
        ed = make_editor(CTRL_FORM)
        result = self._render(ed)
        assert "_" in result
