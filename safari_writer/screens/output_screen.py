"""Program output screen — displays output from Safari Basic, ASM, Base, or Python."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static
from textual import events

PREVIEW_CSS = """
OutputScreen {
    background: $surface;
}

#output-header {
    dock: top;
    height: 1;
    background: $primary;
    color: $text;
    padding: 0 1;
}

#output-footer {
    dock: bottom;
    height: 1;
    background: $primary;
    color: $text;
    padding: 0 1;
}

#output-body {
    height: 1fr;
    overflow-y: auto;
}
"""


class OutputScreen(Screen):
    """Full-screen read-only output of the program execution."""

    CSS = PREVIEW_CSS

    def __init__(self, output: str, title: str = "PROGRAM OUTPUT") -> None:
        super().__init__()
        self._output_lines = output.splitlines()
        self._title = title
        self._scroll_offset = 0

    def compose(self) -> ComposeResult:
        yield Static(f" {self._title}", id="output-header")
        yield Static("", id="output-body")
        yield Static(
            " PgUp/PgDn  Up/Down  Home/End  Any key to Return",
            id="output-footer",
        )

    def on_mount(self) -> None:
        self._update_view()

    def _update_view(self) -> None:
        if not self.is_mounted:
            return
        height = max(1, self.size.height - 2)
        visible = self._output_lines[self._scroll_offset : self._scroll_offset + height]
        body_text = "\n".join(visible)
        self.query_one("#output-body", Static).update(body_text)

        self.query_one("#output-header", Static).update(
            f" {self._title}   Line {self._scroll_offset + 1}/{len(self._output_lines)}"
        )

    def on_key(self, event: events.Key) -> None:
        height = max(1, self.size.height - 2)
        max_offset = max(0, len(self._output_lines) - height)

        if event.key in ("up",):
            self._scroll_offset = max(0, self._scroll_offset - 1)
            self._update_view()
        elif event.key in ("down",):
            self._scroll_offset = min(max_offset, self._scroll_offset + 1)
            self._update_view()
        elif event.key == "pageup":
            self._scroll_offset = max(0, self._scroll_offset - height)
            self._update_view()
        elif event.key == "pagedown":
            self._scroll_offset = min(max_offset, self._scroll_offset + height)
            self._update_view()
        elif event.key == "home":
            self._scroll_offset = 0
            self._update_view()
        elif event.key == "end":
            self._scroll_offset = max_offset
            self._update_view()
        else:
            # Any other key (Esc, Enter, etc.) returns to editor
            self.app.pop_screen()

        event.stop()

    def on_resize(self) -> None:
        self._update_view()
