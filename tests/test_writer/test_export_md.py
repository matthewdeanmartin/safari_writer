"""Tests for Markdown export."""

import pytest
from safari_writer.export_md import export_markdown
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
    CTRL_MERGE,
    CTRL_HEADER,
    CTRL_FOOTER,
    CTRL_HEADING,
    CTRL_EJECT,
    CTRL_CHAIN,
    CTRL_FORM,
)


def fmt(**kw):
    return GlobalFormat(**kw)


class TestPlainText:
    def test_simple(self):
        result = export_markdown(["Hello", "World"], fmt())
        assert "Hello\nWorld\n" == result

    def test_empty_doc(self):
        result = export_markdown([""], fmt())
        assert result == "\n"


class TestBold:
    def test_bold_wrapping(self):
        buf = [f"{CTRL_BOLD}text{CTRL_BOLD}"]
        result = export_markdown(buf, fmt())
        assert "**text**" in result

    def test_bold_mid_line(self):
        buf = [f"hello {CTRL_BOLD}bold{CTRL_BOLD} world"]
        result = export_markdown(buf, fmt())
        assert "hello **bold** world" in result


class TestUnderline:
    def test_underline_wrapping(self):
        buf = [f"{CTRL_UNDERLINE}text{CTRL_UNDERLINE}"]
        result = export_markdown(buf, fmt())
        assert "<u>text</u>" in result


class TestElongated:
    def test_elongated_as_bold(self):
        buf = [f"{CTRL_ELONGATE}text{CTRL_ELONGATE}"]
        result = export_markdown(buf, fmt())
        assert "**text**" in result


class TestSuperSub:
    def test_superscript(self):
        buf = [f"E=mc{CTRL_SUPER}2{CTRL_SUPER}"]
        result = export_markdown(buf, fmt())
        assert "<sup>2</sup>" in result

    def test_subscript(self):
        buf = [f"H{CTRL_SUB}2{CTRL_SUB}O"]
        result = export_markdown(buf, fmt())
        assert "<sub>2</sub>" in result


class TestAlignment:
    def test_center(self):
        buf = [f"{CTRL_CENTER}Centered Text"]
        result = export_markdown(buf, fmt())
        assert "<center>Centered Text</center>" in result

    def test_right(self):
        buf = [f"{CTRL_RIGHT}Right Text"]
        result = export_markdown(buf, fmt())
        assert "<!-- flush right -->" in result
        assert "Right Text" in result


class TestHeading:
    def test_level_1(self):
        buf = [f"{CTRL_HEADING}1Introduction"]
        result = export_markdown(buf, fmt())
        assert "# 1.0 Introduction" in result

    def test_level_3(self):
        buf = [f"{CTRL_HEADING}3Sub Section"]
        result = export_markdown(buf, fmt())
        assert "### 1.0.1 Sub Section" in result

    def test_auto_numbers_outline(self):
        buf = [
            f"{CTRL_HEADING}1Intro",
            f"{CTRL_HEADING}2Background",
            f"{CTRL_HEADING}2Scope",
            f"{CTRL_HEADING}1Next",
        ]
        result = export_markdown(buf, fmt())
        assert "# 1.0 Intro" in result
        assert "## 1.1 Background" in result
        assert "## 1.2 Scope" in result
        assert "# 2.0 Next" in result


class TestPageBreak:
    def test_eject(self):
        buf = ["Before", CTRL_EJECT, "After"]
        result = export_markdown(buf, fmt())
        assert "---" in result


class TestParagraphMark:
    def test_blank_line_before(self):
        buf = [f"{CTRL_PARA}Indented"]
        result = export_markdown(buf, fmt())
        lines = result.split("\n")
        # Should have blank line before indented content
        idx = next(i for i, l in enumerate(lines) if "Indented" in l)
        assert idx > 0
        assert lines[idx - 1] == ""


class TestHeaderFooter:
    def test_header_at_top(self):
        buf = [f"{CTRL_HEADER}My Title", "Body"]
        result = export_markdown(buf, fmt())
        lines = result.strip().split("\n")
        assert "My Title" in lines[0]

    def test_footer_at_bottom(self):
        buf = [f"{CTRL_FOOTER}Page Info", "Body"]
        result = export_markdown(buf, fmt())
        lines = result.strip().split("\n")
        assert "Page Info" in lines[-1]


class TestChain:
    def test_chain_comment(self):
        buf = [f"{CTRL_CHAIN}next.sfw"]
        result = export_markdown(buf, fmt())
        assert "<!-- chain: next.sfw -->" in result


class TestMergeField:
    def test_merge_placeholder(self):
        buf = [f"Dear {CTRL_MERGE}1"]
        result = export_markdown(buf, fmt())
        assert "{{field1}}" in result


class TestFormBlank:
    def test_form_blank(self):
        buf = [f"Name: {CTRL_FORM}"]
        result = export_markdown(buf, fmt())
        assert "[________]" in result


class TestUnclosedToggle:
    def test_unclosed_bold_auto_closes(self):
        buf = [f"{CTRL_BOLD}open ended"]
        result = export_markdown(buf, fmt())
        assert "**open ended**" in result
