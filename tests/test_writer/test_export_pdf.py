"""Tests for PDF export."""

from __future__ import annotations

from safari_writer.export_pdf import export_pdf
from safari_writer.mail_merge_db import FieldDef, MailMergeDB
from safari_writer.screens.editor import (CTRL_BOLD, CTRL_EJECT, CTRL_HEADER,
                                          CTRL_MERGE)
from safari_writer.state import GlobalFormat


def _pdf_text(pdf: bytes) -> str:
    return pdf.decode("latin-1", errors="ignore")


class TestExportPdf:
    def test_basic_output_is_valid_pdf(self) -> None:
        pdf = export_pdf(["Hello world"], GlobalFormat())
        assert pdf.startswith(b"%PDF-")
        assert "Hello world" in _pdf_text(pdf)

    def test_page_break_creates_multiple_pages(self) -> None:
        pdf = export_pdf(["before", f"{CTRL_EJECT}", "after"], GlobalFormat())
        text = _pdf_text(pdf)
        assert "before" in text
        assert "after" in text
        assert text.count("/Type /Page") >= 2

    def test_header_page_number_substitution(self) -> None:
        pdf = export_pdf(
            [f"{CTRL_HEADER}Page @", "body"], GlobalFormat(page_number_start=7)
        )
        assert "Page 7" in _pdf_text(pdf)

    def test_formatted_text_is_rendered(self) -> None:
        pdf = export_pdf([f"{CTRL_BOLD}bold text{CTRL_BOLD}"], GlobalFormat())
        assert "bold text" in _pdf_text(pdf)

    def test_mail_merge_integration(self) -> None:
        db = MailMergeDB(
            fields=[FieldDef("Name", 20)],
            records=[["Alice"], ["Bob"]],
        )
        pdf = export_pdf([f"Dear {CTRL_MERGE}1"], GlobalFormat(), db)
        text = _pdf_text(pdf)
        assert "Dear Alice" in text
        assert "Dear Bob" in text
        assert text.count("/Type /Page") >= 2
