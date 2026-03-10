"""Tests for PostScript export."""

from __future__ import annotations

from safari_writer.export_ps import export_postscript, _ps_escape, _parse_spans, _strip
from safari_writer.state import GlobalFormat
from safari_writer.screens.editor import (
    CTRL_BOLD,
    CTRL_UNDERLINE,
    CTRL_CENTER,
    CTRL_RIGHT,
    CTRL_ELONGATE,
    CTRL_SUPER,
    CTRL_SUB,
    CTRL_PARA,
    CTRL_HEADER,
    CTRL_FOOTER,
    CTRL_HEADING,
    CTRL_EJECT,
)


class TestPsEscape:
    def test_plain_text(self) -> None:
        assert _ps_escape("Hello world") == "Hello world"

    def test_escapes_backslash(self) -> None:
        assert _ps_escape("a\\b") == "a\\\\b"

    def test_escapes_parens(self) -> None:
        assert _ps_escape("(test)") == "\\(test\\)"

    def test_combined(self) -> None:
        assert _ps_escape("a\\(b)") == "a\\\\\\(b\\)"


class TestStrip:
    def test_removes_control_chars(self) -> None:
        assert _strip(f"{CTRL_BOLD}hello{CTRL_BOLD}") == "hello"

    def test_preserves_tabs(self) -> None:
        assert _strip("a\tb") == "a\tb"

    def test_empty_string(self) -> None:
        assert _strip("") == ""


class TestParseSpans:
    def test_plain_text(self) -> None:
        spans = _parse_spans("Hello world")
        assert len(spans) == 1
        assert spans[0].text == "Hello world"
        assert not spans[0].bold

    def test_bold_span(self) -> None:
        spans = _parse_spans(f"{CTRL_BOLD}bold text{CTRL_BOLD}")
        assert any(s.text == "bold text" and s.bold for s in spans)

    def test_underline_span(self) -> None:
        spans = _parse_spans(f"{CTRL_UNDERLINE}underlined{CTRL_UNDERLINE}")
        assert any(s.text == "underlined" and s.underline for s in spans)

    def test_mixed_formatting(self) -> None:
        text = f"plain {CTRL_BOLD}bold{CTRL_BOLD} rest"
        spans = _parse_spans(text)
        texts = [s.text for s in spans]
        assert "plain " in texts
        assert "bold" in texts
        assert " rest" in texts

    def test_superscript(self) -> None:
        spans = _parse_spans(f"x{CTRL_SUPER}2{CTRL_SUPER}")
        assert any(s.text == "2" and s.superscript for s in spans)

    def test_subscript(self) -> None:
        spans = _parse_spans(f"H{CTRL_SUB}2{CTRL_SUB}O")
        assert any(s.text == "2" and s.subscript for s in spans)

    def test_elongated(self) -> None:
        spans = _parse_spans(f"{CTRL_ELONGATE}wide{CTRL_ELONGATE}")
        assert any(s.text == "wide" and s.elongated for s in spans)

    def test_empty_string(self) -> None:
        spans = _parse_spans("")
        assert spans == []


class TestExportPostscript:
    def test_basic_output_is_valid_ps(self) -> None:
        ps = export_postscript(["Hello world"], GlobalFormat())
        assert ps.startswith("%!PS-Adobe-3.0")
        assert "%%EOF" in ps
        assert "showpage" in ps

    def test_empty_buffer(self) -> None:
        ps = export_postscript([""], GlobalFormat())
        assert "%!PS-Adobe-3.0" in ps
        assert "%%EOF" in ps

    def test_multiline_buffer(self) -> None:
        ps = export_postscript(["Line 1", "Line 2", "Line 3"], GlobalFormat())
        assert "(Line 1)" in ps
        assert "(Line 2)" in ps
        assert "(Line 3)" in ps

    def test_header_line(self) -> None:
        ps = export_postscript([f"{CTRL_HEADER}My Header", "body"], GlobalFormat())
        assert "(My Header)" in ps

    def test_footer_line(self) -> None:
        ps = export_postscript([f"{CTRL_FOOTER}Page @", "body"], GlobalFormat())
        # Footer with page number substitution
        assert "Page" in ps

    def test_page_break(self) -> None:
        lines = ["before", f"{CTRL_EJECT}", "after"]
        ps = export_postscript(lines, GlobalFormat())
        # Should have multiple showpage calls (2 pages)
        assert ps.count("showpage") >= 2

    def test_centered_line(self) -> None:
        ps = export_postscript([f"{CTRL_CENTER}centered text"], GlobalFormat())
        assert "(centered text)" in ps

    def test_right_aligned_line(self) -> None:
        ps = export_postscript([f"{CTRL_RIGHT}right text"], GlobalFormat())
        assert "(right text)" in ps

    def test_bold_text_uses_bold_font(self) -> None:
        ps = export_postscript([f"{CTRL_BOLD}bold text{CTRL_BOLD}"], GlobalFormat())
        assert "Courier-Bold" in ps

    def test_heading_line(self) -> None:
        ps = export_postscript([f"{CTRL_HEADING}1My Heading"], GlobalFormat())
        assert "My Heading" in ps

    def test_paragraph_indent(self) -> None:
        ps = export_postscript([f"{CTRL_PARA}indented"], GlobalFormat())
        assert "(indented)" in ps

    def test_font_selection_pica(self) -> None:
        fmt = GlobalFormat(type_font=1)
        ps = export_postscript(["text"], fmt)
        assert "Courier" in ps

    def test_font_selection_proportional(self) -> None:
        fmt = GlobalFormat(type_font=3)
        ps = export_postscript(["text"], fmt)
        assert "Helvetica" in ps

    def test_page_number_in_header(self) -> None:
        fmt = GlobalFormat(page_number_start=5)
        ps = export_postscript([f"{CTRL_HEADER}Page @", "body"], fmt)
        assert "Page 5" in ps

    def test_special_chars_escaped(self) -> None:
        ps = export_postscript(["Hello (world)"], GlobalFormat())
        assert "\\(world\\)" in ps

    def test_underlined_text_draws_line(self) -> None:
        ps = export_postscript(
            [f"{CTRL_UNDERLINE}underlined{CTRL_UNDERLINE}"], GlobalFormat()
        )
        assert "rlineto" in ps  # underline drawing uses rlineto

    def test_mail_merge_integration(self) -> None:
        from safari_writer.mail_merge_db import MailMergeDB, FieldDef

        db = MailMergeDB(
            fields=[FieldDef("Name", 20)],
            records=[["Alice"], ["Bob"]],
        )
        from safari_writer.screens.editor import CTRL_MERGE

        buffer = [f"Dear {CTRL_MERGE}1"]
        ps = export_postscript(buffer, GlobalFormat(), db)
        assert "Alice" in ps
        assert "Bob" in ps
        # Two copies = at least two showpage calls
        assert ps.count("showpage") >= 2
