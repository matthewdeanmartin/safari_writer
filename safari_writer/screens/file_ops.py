"""File operations — filename prompt and confirmation screens."""

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Static
from textual import events


FP_CSS = """
FilePromptScreen, ConfirmScreen {
    align: center middle;
}

#fp-dialog, #confirm-dialog {
    width: 60;
    height: 7;
    border: solid $primary;
    background: $surface;
    padding: 1 2;
}

#fp-title, #confirm-title {
    text-align: center;
    text-style: bold;
    color: $accent;
}

#fp-input {
    color: $text;
    margin-top: 1;
}

#fp-hint, #confirm-hint {
    color: $text-muted;
    text-align: center;
}
"""


class FilePromptScreen(ModalScreen[str | None]):
    """Modal prompt for a filename. Returns the filename or None on cancel."""

    CSS = FP_CSS

    def __init__(self, title: str, default: str = "") -> None:
        super().__init__()
        self._title = title
        self._input_buf = default

    def compose(self) -> ComposeResult:
        from textual.containers import Container
        with Container(id="fp-dialog"):
            yield Static(self._title, id="fp-title")
            yield Static(self._render_input(), id="fp-input")
            yield Static("Enter confirm | Esc cancel", id="fp-hint")

    def _render_input(self) -> str:
        return f"> {self._input_buf}[reverse] [/reverse]"

    def _refresh_input(self) -> None:
        self.query_one("#fp-input", Static).update(self._render_input())

    def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            self.dismiss(None)
        elif event.key == "enter":
            filename = self._input_buf.strip()
            self.dismiss(filename if filename else None)
        elif event.key == "backspace":
            self._input_buf = self._input_buf[:-1]
            self._refresh_input()
        elif event.character and event.character.isprintable():
            self._input_buf += event.character
            self._refresh_input()
        event.stop()


class ConfirmScreen(ModalScreen[bool | None]):
    """Y/N confirmation dialog. Returns True, False, or None on Esc."""

    CSS = FP_CSS

    def __init__(self, prompt: str) -> None:
        super().__init__()
        self._prompt = prompt

    def compose(self) -> ComposeResult:
        from textual.containers import Container
        with Container(id="confirm-dialog"):
            yield Static(self._prompt, id="confirm-title")
            yield Static("Y/N?", id="confirm-hint")

    def on_key(self, event: events.Key) -> None:
        if event.key == "y":
            self.dismiss(True)
        elif event.key == "n" or event.key == "escape":
            self.dismiss(False)
        event.stop()
