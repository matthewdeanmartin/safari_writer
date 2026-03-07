"""Unit tests for GlobalFormatScreen parameter editing logic."""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from safari_writer.state import GlobalFormat
from safari_writer.screens.global_format import (
    GlobalFormatScreen,
    PARAMS,
    KEY_TO_PARAM,
    GFRow,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_screen() -> GlobalFormatScreen:
    """Return a GlobalFormatScreen with a fresh GlobalFormat, bypassing Textual."""
    fmt = GlobalFormat()
    with patch("textual.screen.Screen.__init__", return_value=None):
        screen = GlobalFormatScreen.__new__(GlobalFormatScreen)
        screen._fmt = fmt
        screen._editing_key = None
        screen._input_buf = ""
        screen._rows = {}
        # Build row stubs so set_message / refresh_value don't crash
        for p in PARAMS:
            row = MagicMock()
            row._param = p
            row._value = getattr(fmt, p.attr)
            row._editing = False
            screen._rows[p.key] = row
    # Stub widget-dependent methods
    screen.set_message = MagicMock()
    screen.query_one = MagicMock()
    return screen


# ---------------------------------------------------------------------------
# PARAMS table sanity
# ---------------------------------------------------------------------------

class TestParamTable:
    def test_all_14_params_present(self):
        assert len(PARAMS) == 14

    def test_keys_unique(self):
        keys = [p.key for p in PARAMS]
        assert len(keys) == len(set(keys))

    def test_key_to_param_lookup(self):
        for p in PARAMS:
            assert KEY_TO_PARAM[p.key] is p

    def test_defaults_in_valid_range(self):
        fmt = GlobalFormat()
        for p in PARAMS:
            val = getattr(fmt, p.attr)
            assert p.min_val <= val <= p.max_val, (
                f"{p.key} default {val} out of [{p.min_val}, {p.max_val}]"
            )


# ---------------------------------------------------------------------------
# GlobalFormat dataclass
# ---------------------------------------------------------------------------

class TestGlobalFormatDefaults:
    def test_default_values(self):
        fmt = GlobalFormat()
        assert fmt.top_margin == 12
        assert fmt.bottom_margin == 12
        assert fmt.left_margin == 10
        assert fmt.right_margin == 70
        assert fmt.line_spacing == 2
        assert fmt.para_spacing == 2
        assert fmt.col2_left == 8
        assert fmt.col2_right == 70
        assert fmt.type_font == 1
        assert fmt.para_indent == 5
        assert fmt.justification == 0
        assert fmt.page_number_start == 1
        assert fmt.page_length == 132
        assert fmt.page_wait == 0

    def test_reset_defaults(self):
        fmt = GlobalFormat()
        fmt.top_margin = 99
        fmt.left_margin = 1
        fmt.reset_defaults()
        assert fmt.top_margin == 12
        assert fmt.left_margin == 10


# ---------------------------------------------------------------------------
# Editing workflow
# ---------------------------------------------------------------------------

class TestEditing:
    def test_start_editing_sets_state(self):
        screen = make_screen()
        screen._start_editing("T")
        assert screen._editing_key == "T"
        assert screen._input_buf == ""
        screen._rows["T"].refresh_value.assert_called()

    def test_commit_valid_value(self):
        screen = make_screen()
        screen._start_editing("T")
        screen._input_buf = "20"
        param = KEY_TO_PARAM["T"]
        screen._commit_edit(param)
        assert screen._fmt.top_margin == 20
        assert screen._editing_key is None
        assert screen._input_buf == ""

    def test_commit_empty_cancels(self):
        screen = make_screen()
        original = screen._fmt.top_margin
        screen._start_editing("T")
        screen._input_buf = ""
        param = KEY_TO_PARAM["T"]
        screen._commit_edit(param)
        # Should cancel, not crash, and leave value unchanged
        assert screen._fmt.top_margin == original

    def test_commit_below_min_rejected(self):
        screen = make_screen()
        screen._start_editing("L")  # L: left margin, min 1
        screen._input_buf = "0"
        param = KEY_TO_PARAM["L"]
        screen._commit_edit(param)
        # Value should NOT be saved; editing key stays set
        assert screen._fmt.left_margin == 10  # default unchanged
        assert screen._editing_key == "L"     # still editing

    def test_commit_above_max_rejected(self):
        screen = make_screen()
        screen._start_editing("R")  # R: right margin, max 132
        screen._input_buf = "200"
        param = KEY_TO_PARAM["R"]
        screen._commit_edit(param)
        assert screen._fmt.right_margin == 70  # default unchanged
        assert screen._editing_key == "R"

    def test_commit_at_boundary_min(self):
        screen = make_screen()
        screen._start_editing("L")  # min 1
        screen._input_buf = "1"
        param = KEY_TO_PARAM["L"]
        screen._commit_edit(param)
        assert screen._fmt.left_margin == 1
        assert screen._editing_key is None

    def test_commit_at_boundary_max(self):
        screen = make_screen()
        screen._start_editing("R")  # max 132
        screen._input_buf = "132"
        param = KEY_TO_PARAM["R"]
        screen._commit_edit(param)
        assert screen._fmt.right_margin == 132
        assert screen._editing_key is None

    def test_cancel_restores_display(self):
        screen = make_screen()
        screen._start_editing("T")
        screen._input_buf = "99"
        param = KEY_TO_PARAM["T"]
        screen._cancel_edit(param)
        assert screen._editing_key is None
        assert screen._input_buf == ""
        # Row should be refreshed with original value (no editing highlight)
        screen._rows["T"].refresh_value.assert_called_with(12, editing=False)

    def test_all_params_can_be_edited(self):
        """Cycle through every param, set its min value, confirm accepted."""
        for p in PARAMS:
            screen = make_screen()
            screen._start_editing(p.key)
            screen._input_buf = str(p.min_val)
            screen._commit_edit(p)
            assert getattr(screen._fmt, p.attr) == p.min_val, f"Failed for {p.key}"
            assert screen._editing_key is None


# ---------------------------------------------------------------------------
# Reset defaults
# ---------------------------------------------------------------------------

class TestResetDefaults:
    def test_reset_restores_all(self):
        screen = make_screen()
        screen._fmt.top_margin = 99
        screen._fmt.justification = 1
        screen._fmt.page_wait = 1
        screen.action_reset_defaults()
        assert screen._fmt.top_margin == 12
        assert screen._fmt.justification == 0
        assert screen._fmt.page_wait == 0

    def test_reset_ignored_while_editing(self):
        screen = make_screen()
        screen._fmt.top_margin = 99
        screen._editing_key = "T"
        screen.action_reset_defaults()
        # Should NOT reset when editing
        assert screen._fmt.top_margin == 99

    def test_reset_refreshes_all_rows(self):
        screen = make_screen()
        screen.action_reset_defaults()
        for p in PARAMS:
            screen._rows[p.key].refresh_value.assert_called()


# ---------------------------------------------------------------------------
# Escape / exit behaviour
# ---------------------------------------------------------------------------

class TestEscapeBehavior:
    def test_esc_while_editing_cancels_not_exits(self):
        screen = make_screen()
        mock_app = MagicMock()
        screen._editing_key = "T"
        screen._input_buf = "50"
        with patch.object(type(screen), "app", new_callable=lambda: property(lambda self: mock_app)):
            screen.action_accept_and_exit()
        mock_app.pop_screen.assert_not_called()
        assert screen._editing_key is None

    def test_esc_while_idle_pops_screen(self):
        screen = make_screen()
        mock_app = MagicMock()
        screen._editing_key = None
        with patch.object(type(screen), "app", new_callable=lambda: property(lambda self: mock_app)):
            screen.action_accept_and_exit()
        mock_app.pop_screen.assert_called_once()
