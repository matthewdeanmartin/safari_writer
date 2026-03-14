"""Writer integration tests for safari_slides."""

from pathlib import Path

from safari_slides.screens import SafariSlidesMainScreen
from safari_writer.app import SafariWriterApp
from safari_writer.state import AppState


def test_writer_preview_pushes_slide_screen(monkeypatch) -> None:
    app = SafariWriterApp(
        state=AppState(
            buffer=["# Intro", "", "---", "", "## End"], filename="deck.slides.md"
        )
    )
    pushed: list[object] = []
    monkeypatch.setattr(
        app, "push_screen", lambda screen, callback=None: pushed.append(screen)
    )

    app._action_preview_slides()

    assert app.slides_state is not None
    assert app.slides_state.slide_count == 2
    assert isinstance(pushed[0], SafariSlidesMainScreen)


def test_writer_export_slides_writes_slidemd(tmp_path) -> None:
    app = SafariWriterApp(
        state=AppState(
            buffer=["Quarterly Update", "", "Wins", "", "Next steps"],
            doc_title="Quarterly Update",
        )
    )
    target = tmp_path / "quarterly.slides.md"

    app._on_export_slides(str(target))

    rendered = target.read_text(encoding="utf-8")
    assert "title: Quarterly Update" in rendered
    assert Path(target).name in str(target)
