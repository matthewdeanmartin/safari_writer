"""Tests for the ANSI print preview rendering engine."""

import pytest
from safari_writer.state import GlobalFormat
from safari_writer.screens.print_screen import (
    _render_document,
    _count_pages,
    _render_inline,
    _strip_inline,
)
from safari_writer.screens.editor import (
    CTRL_BOLD, CTRL_UNDERLINE, CTRL_CENTER, CTRL_RIGHT,
    CTRL_ELONGATE, CTRL_SUPER, CTRL_SUB, CTRL_PARA,
    CTRL_MERGE, CTRL_HEADER, CTRL_FOOTER, CTRL_HEADING,
    CTRL_EJECT, CTRL_CHAIN, CTRL_FORM, TOGGLE_MARKERS,
)


def default_fmt(**overrides):
    fmt = GlobalFormat()
    for k, v in overrides.items():
        setattr(fmt, k, v)
    return fmt


class TestRenderInline:
    def _init_state(self):
        return {m: False for m in TOGGLE_MARKERS}

    def test_plain_text(self):
        text, state = _render_inline("Hello world", self._init_state())
        assert "Hello world" in text

    def test_bold_markup(self):
        line = f"{CTRL_BOLD}bold{CTRL_BOLD}"
        text, state = _render_inline(line, self._init_state())
        assert "[bold]" in text
        assert "bold" in text

    def test_underline_markup(self):
        line = f"{CTRL_UNDERLINE}text{CTRL_UNDERLINE}"
        text, state = _render_inline(line, self._init_state())
        assert "[underline]" in text

    def test_merge_field_display(self):
        line = f"Dear {CTRL_MERGE}1"
        text, state = _render_inline(line, self._init_state())
        assert "<<@>>" in text

    def test_form_blank_display(self):
        line = f"Name: {CTRL_FORM}"
        text, state = _render_inline(line, self._init_state())
        assert "[________]" in text

    def test_toggle_state_carries(self):
        state = self._init_state()
        _, state = _render_inline(f"{CTRL_BOLD}start", state)
        assert state[CTRL_BOLD] is True
        _, state = _render_inline(f"continue{CTRL_BOLD}", state)
        assert state[CTRL_BOLD] is False

    def test_rich_brackets_escaped(self):
        text, _ = _render_inline("array[0]", self._init_state())
        assert "\\[" in text


class TestStripInline:
    def test_removes_controls(self):
        assert _strip_inline(f"{CTRL_BOLD}hello{CTRL_BOLD}") == "hello"

    def test_preserves_text(self):
        assert _strip_inline("plain text") == "plain text"

    def test_preserves_tabs(self):
        assert _strip_inline("col1\tcol2") == "col1\tcol2"


class TestRenderDocument:
    def test_plain_text_renders(self):
        buf = ["Hello", "World"]
        lines = _render_document(buf, default_fmt())
        joined = "\n".join(lines)
        assert "Hello" in joined
        assert "World" in joined

    def test_header_appears_on_page(self):
        buf = [f"{CTRL_HEADER}My Title", "Body text"]
        lines = _render_document(buf, default_fmt())
        joined = "\n".join(lines)
        assert "My Title" in joined

    def test_footer_appears_on_page(self):
        buf = [f"{CTRL_FOOTER}Page @", "Body text"]
        lines = _render_document(buf, default_fmt())
        joined = "\n".join(lines)
        # Footer with page number substituted
        assert "Page 1" in joined

    def test_page_eject_creates_page_break(self):
        buf = ["Before", CTRL_EJECT, "After"]
        lines = _render_document(buf, default_fmt())
        # Should have page separator rule
        rule_lines = [l for l in lines if "─" in l and "Page" in l]
        assert len(rule_lines) >= 1

    def test_section_heading(self):
        buf = [f"{CTRL_HEADING}2My Section"]
        lines = _render_document(buf, default_fmt())
        joined = "\n".join(lines)
        assert "1.1" in joined
        assert "My Section" in joined

    def test_section_headings_auto_number(self):
        buf = [
            f"{CTRL_HEADING}1Intro",
            f"{CTRL_HEADING}2Background",
            f"{CTRL_HEADING}2Scope",
            f"{CTRL_HEADING}1Next",
        ]
        lines = _render_document(buf, default_fmt())
        joined = "\n".join(lines)
        assert "1.0 Intro" in joined
        assert "1.1 Background" in joined
        assert "1.2 Scope" in joined
        assert "2.0 Next" in joined

    def test_chain_file_noted(self):
        buf = [f"{CTRL_CHAIN}nextfile.sfw"]
        lines = _render_document(buf, default_fmt())
        joined = "\n".join(lines)
        assert "Chain:" in joined
        assert "nextfile.sfw" in joined

    def test_center_alignment(self):
        buf = [f"{CTRL_CENTER}Centered"]
        lines = _render_document(buf, default_fmt(left_margin=0))
        # Centered text should have leading spaces
        content_lines = [l for l in lines if "Centered" in l]
        assert len(content_lines) > 0
        # With margin 0 and width 70, should have some leading spaces
        assert content_lines[0].startswith(" ")

    def test_right_alignment(self):
        buf = [f"{CTRL_RIGHT}Right"]
        lines = _render_document(buf, default_fmt(left_margin=0))
        content_lines = [l for l in lines if "Right" in l]
        assert len(content_lines) > 0
        assert content_lines[0].startswith(" ")

    def test_paragraph_indent(self):
        buf = [f"{CTRL_PARA}Indented line"]
        fmt = default_fmt(left_margin=0, para_indent=5)
        lines = _render_document(buf, fmt)
        content_lines = [l for l in lines if "Indented" in l]
        assert len(content_lines) > 0
        assert content_lines[0].startswith("     ")

    def test_left_margin_applied(self):
        buf = ["Hello"]
        fmt = default_fmt(left_margin=4)
        lines = _render_document(buf, fmt)
        content_lines = [l for l in lines if "Hello" in l]
        assert len(content_lines) > 0
        assert content_lines[0].startswith("    ")

    def test_empty_document(self):
        buf = [""]
        lines = _render_document(buf, default_fmt())
        assert isinstance(lines, list)


class TestCountPages:
    def test_single_page(self):
        buf = ["Hello"]
        lines = _render_document(buf, default_fmt())
        assert _count_pages(lines) == 1

    def test_page_break_creates_two_pages(self):
        buf = ["Before", CTRL_EJECT, "After"]
        lines = _render_document(buf, default_fmt())
        assert _count_pages(lines) == 2

    def test_multiple_breaks(self):
        buf = ["P1", CTRL_EJECT, "P2", CTRL_EJECT, "P3"]
        lines = _render_document(buf, default_fmt())
        assert _count_pages(lines) >= 3


class TestHeaderFooterPageNumber:
    def test_page_number_in_header(self):
        buf = [f"{CTRL_HEADER}Page @", "Body"]
        lines = _render_document(buf, default_fmt())
        joined = "\n".join(lines)
        assert "Page 1" in joined

    def test_custom_start_page(self):
        buf = [f"{CTRL_HEADER}Page @", "Body"]
        lines = _render_document(buf, default_fmt(page_number_start=5))
        joined = "\n".join(lines)
        assert "Page 5" in joined

    def test_page_number_in_footer(self):
        buf = [f"{CTRL_FOOTER}- @ -", "Body"]
        lines = _render_document(buf, default_fmt())
        joined = "\n".join(lines)
        assert "- 1 -" in joined
