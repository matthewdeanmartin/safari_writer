"""Standalone Textual app for Safari REPL."""

from __future__ import annotations

import os
from pathlib import Path

from textual.app import App

from safari_repl.screens import ReplEditorScreen, ReplMainMenuScreen
from safari_repl.state import ReplExitRequest, ReplState

__all__ = ["SafariReplApp"]


class SafariReplApp(App[ReplExitRequest | None]):
    """Atari BASIC REPL built on safari_basic."""

    TITLE = "Safari REPL"

    def __init__(self, bas_path: Path | None = None) -> None:
        super().__init__()
        self.state = ReplState(loaded_path=bas_path)

    def on_mount(self) -> None:
        if os.environ.get("SAFARI_HEADLESS") == "1":
            self.exit()

        from safari_writer.themes import DEFAULT_THEME, THEMES, load_settings

        for theme in THEMES.values():
            self.register_theme(theme)
        settings = load_settings()
        saved_theme = settings.get("theme", DEFAULT_THEME)
        if saved_theme not in THEMES:
            saved_theme = DEFAULT_THEME
        self.theme = saved_theme

        self.push_screen(ReplMainMenuScreen(self.state))

    # --- actions called from screens ---

    def open_repl(self) -> None:
        self.push_screen(ReplEditorScreen(self.state))

    def load_file(self) -> None:
        self.push_screen(
            _FilePickerScreen(start_path=Path.cwd()),
            callback=self._on_file_picked,
        )

    def open_help(self) -> None:
        self.push_screen(_HelpScreen())

    def quit_repl(self) -> None:
        self.exit(None)

    def request_writer_launch(self, path: Path) -> None:
        self.exit(ReplExitRequest(action="open-in-writer", document_path=path))

    def _on_file_picked(self, path: Path | None) -> None:
        if path is None:
            return
        self.state.loaded_path = path
        self.state.output_lines = []
        # Refresh the main menu status bar
        from textual.app import ScreenStackError

        try:
            current = self.screen_stack[0]
            if isinstance(current, ReplMainMenuScreen):
                current.refresh()
        except (ScreenStackError, IndexError):
            pass
        # Open REPL immediately so user can run the loaded file
        self.open_repl()


# ---------------------------------------------------------------------------
# Inline helper screens (file picker + help) to avoid extra files
# ---------------------------------------------------------------------------

from textual import events  # noqa: E402
from textual.app import ComposeResult  # noqa: E402
from textual.containers import Container  # noqa: E402
from textual.screen import ModalScreen  # noqa: E402
from textual.widgets import Static  # noqa: E402

_PICKER_CSS = """
_FilePickerScreen {
    align: center middle;
    background: $background 60%;
}
#picker-dialog {
    width: 72;
    height: auto;
    max-height: 80%;
    border: solid $accent;
    background: $surface;
    padding: 1 2;
}
#picker-title {
    color: $accent;
    text-style: bold;
    text-align: center;
}
#picker-body {
    height: 1fr;
    color: $foreground;
    margin-top: 1;
}
#picker-input {
    color: $foreground;
    margin-top: 1;
}
#picker-hint {
    color: $text-muted;
    margin-top: 1;
}
_HelpScreen {
    align: center middle;
    background: $background 60%;
}
#help-dialog {
    width: 72;
    height: auto;
    border: solid $accent;
    background: $surface;
    padding: 1 2;
}
#help-title {
    color: $accent;
    text-style: bold;
    text-align: center;
    margin-bottom: 1;
}
#help-body {
    color: $foreground;
}
#help-hint {
    color: $text-muted;
    margin-top: 1;
    text-align: center;
}
"""


class _FilePickerScreen(ModalScreen[Path | None]):
    """Simple path-input dialog for loading a .BAS file."""

    CSS = _PICKER_CSS

    def __init__(self, start_path: Path) -> None:
        super().__init__()
        self._buffer = str(start_path) + "/"
        self._entries: list[Path] = []
        self._cursor = 0
        self._mode = "input"  # "input" | "list"

    def compose(self) -> ComposeResult:
        with Container(id="picker-dialog"):
            yield Static("Load .BAS File", id="picker-title")
            yield Static(self._render_list(), id="picker-body")
            yield Static(self._render_input(), id="picker-input")
            yield Static(
                "Enter accept  Tab browse dir  Esc cancel  ↑↓ select",
                id="picker-hint",
            )

    def _scan_dir(self) -> None:
        p = Path(self._buffer)
        if p.is_dir():
            self._entries = sorted(
                p.iterdir(), key=lambda x: (x.is_file(), x.name.lower())
            )
        elif p.parent.is_dir():
            stem = p.name.lower()
            self._entries = sorted(
                [e for e in p.parent.iterdir() if e.name.lower().startswith(stem)],
                key=lambda x: (x.is_file(), x.name.lower()),
            )
        else:
            self._entries = []
        self._cursor = 0

    def _render_list(self) -> str:
        if not self._entries:
            return "(no matches)"
        lines = []
        for i, entry in enumerate(self._entries[:20]):
            prefix = "> " if i == self._cursor else "  "
            suffix = "/" if entry.is_dir() else ""
            lines.append(f"{prefix}{entry.name}{suffix}")
        return "\n".join(lines)

    def _render_input(self) -> str:
        return f"Path: {self._buffer}[reverse] [/reverse]"

    def _refresh(self) -> None:
        self.query_one("#picker-body", Static).update(self._render_list())
        self.query_one("#picker-input", Static).update(self._render_input())

    def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            self.dismiss(None)
        elif event.key == "enter":
            # Accept either highlighted entry or typed path
            if self._entries and self._mode == "list":
                chosen = self._entries[self._cursor]
                if chosen.is_dir():
                    self._buffer = str(chosen) + "/"
                    self._scan_dir()
                    self._refresh()
                else:
                    self.dismiss(chosen)
            else:
                p = Path(self._buffer.strip())
                if p.is_file():
                    self.dismiss(p)
                else:
                    self._scan_dir()
                    self._mode = "list"
                    self._refresh()
        elif event.key == "tab":
            self._scan_dir()
            self._mode = "list"
            self._refresh()
        elif event.key == "up":
            if self._entries:
                self._cursor = max(0, self._cursor - 1)
                self._refresh()
        elif event.key == "down":
            if self._entries:
                self._cursor = min(len(self._entries) - 1, self._cursor + 1)
                self._refresh()
        elif event.key == "backspace":
            self._buffer = self._buffer[:-1]
            self._mode = "input"
            self._refresh()
        elif event.character and event.character.isprintable():
            self._buffer += event.character
            self._mode = "input"
            self._scan_dir()
            self._refresh()
        event.stop()


class _HelpScreen(ModalScreen[None]):
    """Help text for Safari REPL."""

    CSS = _PICKER_CSS

    HELP = """\
SAFARI REPL — Atari BASIC Interpreter
--------------------------------------
Type Atari BASIC lines at the prompt.

  Numbered lines (e.g. 10 PRINT "HI") are stored.
  Un-numbered lines execute immediately.

Key commands:
  LIST [start[,end]]  — list stored program
  RUN                 — run stored program
  NEW                 — clear program & variables
  CLR                 — clear variables only
  CONT                — continue after STOP

F2  — LIST program
F5  — RUN program
F9  — Open loaded .BAS in Safari Writer editor
Esc — Return to main menu

From the main menu:
  L — Load a .BAS file from disk
  R — Enter the REPL (loads file if one is set)
  Q — Quit
"""

    def compose(self) -> ComposeResult:
        with Container(id="help-dialog"):
            yield Static("Safari REPL Help", id="help-title")
            yield Static(self.HELP, id="help-body")
            yield Static("Enter or Esc to close", id="help-hint")

    def on_key(self, event: events.Key) -> None:
        if event.key in {"enter", "escape"}:
            self.dismiss(None)
        event.stop()
