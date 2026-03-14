
import pytest
from pathlib import Path
from safari_writer.file_types import HighlightProfile
from safari_writer.state import AppState, GlobalFormat
from safari_writer.screens.print_screen import _render_with_mail_merge
from safari_writer.export_html import export_html
from safari_writer.export_ps import export_postscript
from safari_writer.export_pdf import export_pdf
from safari_writer.screens.editor import CTRL_HEADING, CTRL_BOLD

def test_markdown_ansi_preview():
    state = AppState()
    state.buffer = ["# Heading 1", "", "This is **bold** and *italic*."]
    state.filename = "test.md"
    state.update_file_profile()
    
    assert state.highlight_profile == HighlightProfile.MARKDOWN
    
    rendered = _render_with_mail_merge(
        state.buffer, state.fmt, state.mail_merge_db, state.highlight_profile
    )
    
    # Check if "Heading 1" is in the output (it should be rendered)
    rendered_text = "\n".join(rendered)
    assert "Heading 1" in rendered_text
    # Rich adds ANSI codes for bold/etc. 
    # Since we use force_terminal=True, they should be there.
    assert "\x1b" in rendered_text

def test_markdown_export_html():
    buffer = ["# Title", "Hello **world**"]
    fmt = GlobalFormat()
    
    html_out = export_html(buffer, fmt, is_markdown=True)
    assert "<h1>Title</h1>" in html_out
    assert "<strong>world</strong>" in html_out
    assert "<!DOCTYPE html>" in html_out

def test_markdown_export_ps():
    buffer = ["# Title", "Hello **world**"]
    fmt = GlobalFormat()
    
    ps_out = export_postscript(buffer, fmt, is_markdown=True)
    # print(ps_out)
    assert "%!PS-Adobe-3.0" in ps_out
    # Check if Title (heading) is there
    # Heading numbering adds a number like "1 " or "1.1 "
    assert "Title" in ps_out
    # world should be there
    assert "world" in ps_out

def test_markdown_export_pdf():
    buffer = ["# Title", "Hello **world**"]
    fmt = GlobalFormat()
    
    pdf_bytes = export_pdf(buffer, fmt, is_markdown=True)
    assert pdf_bytes.startswith(b"%PDF")

def test_sfw_export_compatibility():
    # AtariWriter-style buffer with some controls
    buffer = [f"{CTRL_HEADING}1Heading", f"This is {CTRL_BOLD}bold{CTRL_BOLD}."]
    fmt = GlobalFormat()
    
    # PDF
    pdf_bytes = export_pdf(buffer, fmt, is_markdown=False)
    assert pdf_bytes.startswith(b"%PDF")
    
    # PS
    ps_out = export_postscript(buffer, fmt, is_markdown=False)
    assert "Heading" in ps_out
    assert "bold" in ps_out
    
    # HTML
    html_out = export_html(buffer, fmt, is_markdown=False)
    assert "Heading</h1>" in html_out
    assert "<strong>bold</strong>" in html_out

if __name__ == "__main__":
    pytest.main([__file__])
