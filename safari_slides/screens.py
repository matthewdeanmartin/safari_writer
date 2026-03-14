"""Textual screens for Safari Slides."""

from __future__ import annotations

from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Static

from safari_slides.model import Slide
from safari_slides.state import SafariSlidesState

__all__ = ["SafariSlidesMainScreen"]

_STATUS_STYLE = "bold reverse"

SLIDES_CSS = """
SafariSlidesMainScreen {
    background: $background;
    color: $foreground;
}

#slides-header {
    dock: top;
    height: 1;
    background: $primary;
    color: $text;
    padding: 0 1;
}

#slides-footer {
    dock: bottom;
    height: 1;
    background: $primary;
    color: $text;
    padding: 0 1;
}

#slides-body {
    height: 1fr;
    padding: 1 2;
    overflow-y: auto;
    background: $surface;
}

#slides-notes {
    dock: bottom;
    height: auto;
    min-height: 0;
    padding: 0 2 1 2;
    background: $secondary;
    color: $text;
}
"""


class SafariSlidesMainScreen(Screen):
    """Single-screen slide presentation viewer."""

    CSS = SLIDES_CSS
    BINDINGS = [
        Binding("space", "advance", "Next", show=False),
        Binding("right", "advance", "Next", show=False),
        Binding("down", "advance", "Next", show=False),
        Binding("left", "retreat", "Prev", show=False),
        Binding("up", "retreat", "Prev", show=False),
        Binding("home", "first_slide", "First", show=False),
        Binding("end", "last_slide", "Last", show=False),
        Binding("n", "toggle_notes", "Notes", show=False),
        Binding("q", "quit_viewer", "Quit", show=False),
        Binding("escape", "quit_viewer", "Quit", show=False),
    ]

    def __init__(self, state: SafariSlidesState) -> None:
        super().__init__()
        self.state = state

    def compose(self) -> ComposeResult:
        yield Static("", id="slides-header")
        with Container(id="slides-body"):
            yield Static("", id="slides-content")
        yield Static("", id="slides-notes")
        yield Static("", id="slides-footer")

    def on_mount(self) -> None:
        self._refresh()

    def action_advance(self) -> None:
        self.state.advance()
        self._refresh()

    def action_retreat(self) -> None:
        self.state.retreat()
        self._refresh()

    def action_first_slide(self) -> None:
        self.state.first_slide()
        self._refresh()

    def action_last_slide(self) -> None:
        self.state.last_slide()
        self._refresh()

    def action_toggle_notes(self) -> None:
        self.state.show_notes = not self.state.show_notes
        self._refresh()

    def action_quit_viewer(self) -> None:
        if hasattr(self.app, "quit_slides"):
            self.app.quit_slides()
        else:
            self.app.pop_screen()

    def on_key(self, event: events.Key) -> None:
        if event.key.lower() in {"pagedown", "pageup"}:
            if event.key.lower() == "pagedown":
                self.action_advance()
            else:
                self.action_retreat()
            event.stop()

    def _refresh(self) -> None:
        slide = self.state.current_slide
        self.query_one("#slides-header", Static).update(self._header_text(slide))
        self.query_one("#slides-content", Static).update(self._body_text(slide))
        self.query_one("#slides-notes", Static).update(self._notes_text(slide))
        self.query_one("#slides-footer", Static).update(self._footer_text(slide))

    def _header_text(self, slide: Slide) -> str:
        title = self.state.presentation.metadata.title or "Safari Slides"
        count = self.state.slide_count
        index = self.state.current_slide_index + 1
        return (
            f"[{_STATUS_STYLE}] {title} [/]"
            f"  Slide {index}/{count} ({slide.slide_label})"
            f"  Layout: {slide.metadata.layout}"
        )

    def _body_text(self, slide: Slide) -> str:
        visible_lines: list[str] = []
        trimmed_title = slide.title.strip().lower()
        for line in slide.lines:
            if line.fragment_order and line.fragment_order > self.state.fragment_step:
                continue
            text = line.text
            if (
                not visible_lines
                and text.strip().lstrip("#").strip().lower() == trimmed_title
            ):
                continue
            visible_lines.append(text)
        lines = [slide.title, "=" * len(slide.title), ""]
        lines.extend(visible_lines or ["(empty slide)"])
        if slide.fragment_count:
            lines.extend(
                [
                    "",
                    f"[Fragments: {self.state.fragment_step}/{slide.fragment_count}]",
                ]
            )
        return "\n".join(lines).rstrip()

    def _notes_text(self, slide: Slide) -> str:
        if not self.state.show_notes:
            return ""
        if not slide.notes:
            return "Notes: (none)"
        return "Notes:\n" + "\n".join(f"- {note}" for note in slide.notes)

    def _footer_text(self, slide: Slide) -> str:
        footer = slide.metadata.footer or self.state.presentation.metadata.footer
        hints = " Left/Right move  Space reveal  N notes  Home/End jump  Q exit "
        if footer:
            return f"{footer}  |{hints}"
        return hints
