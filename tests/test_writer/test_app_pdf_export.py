"""App-level PDF export tests."""

from __future__ import annotations

from safari_writer.app import SafariWriterApp
from safari_writer.screens.file_ops import FilePromptScreen
from safari_writer.state import AppState


def test_print_choice_pdf_uses_pdf_prompt(monkeypatch) -> None:
    app = SafariWriterApp(state=AppState(filename="draft.sfw"))
    pushed: list[tuple[object, object]] = []

    monkeypatch.setattr(
        app,
        "push_screen",
        lambda screen, callback=None: pushed.append((screen, callback)),
    )

    app._on_print_choice("pdf")

    screen, callback = pushed[0]
    assert isinstance(screen, FilePromptScreen)
    assert screen._title == "Export PDF to"
    assert screen._input_buf == "draft.pdf"
    assert callback == app._on_export_pdf


def test_on_export_pdf_writes_bytes(tmp_path) -> None:
    app = SafariWriterApp(state=AppState(buffer=["Hello PDF"]))
    output = tmp_path / "draft.pdf"

    app._on_export_pdf(str(output))

    assert output.read_bytes().startswith(b"%PDF-")
