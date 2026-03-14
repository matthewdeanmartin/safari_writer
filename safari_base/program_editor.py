"""Program Editor screen for Safari Base.

Implements MODIFY COMMAND — a full-screen line editor for .prg files,
modeled after the dBASE III Plus program editor.

Layout:
┌──────────────────────────────────────────────────────────────────────────────┐
│ MODIFY COMMAND FILE: REPORT.PRG                                              │
├──────┬───────────────────────────────────────────────────────────────────────┤
│ 1    │ USE CUSTOMER                                                           │
│ 2    │ SET FILTER TO BALANCE > 0                                              │
│ ...  │ ...                                                                    │
├──────────────────────────────────────────────────────────────────────────────┤
│ Line 4   Col 1   F1=Help  F2=Save  F3=Exit                                    │
└──────────────────────────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from textual import events
from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Static

__all__ = ["EDITOR_CSS", "ProgramEditorScreen"]

_log = logging.getLogger("safari_base.program_editor")
if os.environ.get("SAFARI_LOG"):
    _log.setLevel(logging.DEBUG)
    if not _log.handlers:
        _handler = logging.FileHandler(
            Path(__file__).resolve().parent / "debug.log", mode="a"
        )
        _handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
        _log.addHandler(_handler)
else:
    _log.addHandler(logging.NullHandler())


TARGET_WIDTH = 100
TARGET_HEIGHT = 34
LINE_NUM_WIDTH = 6  # Width of the line-number gutter

EDITOR_CSS = """
ProgramEditorScreen {
    background: $background;
    align: center middle;
}

#editor-root {
    width: 100;
    height: 34;
    background: $surface;
    layout: vertical;
}

#editor-title {
    height: 1;
    background: $primary;
    color: $foreground;
    padding: 0 1;
}

#editor-body {
    height: 1fr;
    background: $surface;
    color: $foreground;
    padding: 0 0;
}

#editor-status {
    height: 1;
    background: $primary;
    color: $foreground;
    padding: 0 1;
}
"""


class ProgramEditorScreen(Screen[bool]):
    """Full-screen program editor for .prg files.

    Returns True if the file was saved, False if exited without saving.
    """

    CSS = EDITOR_CSS

    def __init__(
        self,
        file_path: Path | str,
        *,
        work_dir: Path | str | None = None,
    ) -> None:
        super().__init__()
        self._file_path = Path(file_path)
        self._work_dir = Path(work_dir) if work_dir else self._file_path.parent
        # Editor state
        self._lines: list[str] = []
        self._cursor_line = 0  # 0-based line index
        self._cursor_col = 0  # 0-based column index
        self._scroll_offset = 0  # first visible line
        self._insert_mode = True
        self._dirty = False
        self._message = ""
        self._show_help = False
        # Load file
        self._load_file()

    def _load_file(self) -> None:
        """Load the .prg file into the buffer."""
        if self._file_path.exists():
            try:
                text = self._file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                text = self._file_path.read_text(encoding="latin-1")
            # Split into lines, strip trailing newline to avoid ghost empty line
            raw_lines = text.split("\n")
            if raw_lines and raw_lines[-1] == "":
                raw_lines.pop()
            self._lines = raw_lines if raw_lines else [""]
        else:
            # New file — start with one empty line
            self._lines = [""]
        self._dirty = False

    def _save_file(self) -> None:
        """Save the buffer to the .prg file."""
        # Ensure parent directory exists
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        text = "\n".join(self._lines)
        if not text.endswith("\n"):
            text += "\n"
        self._file_path.write_text(text, encoding="utf-8")
        self._dirty = False
        self._message = f"Saved {self._file_path.name}"
        _log.debug("saved %s (%d lines)", self._file_path, len(self._lines))

    # --- Textual lifecycle ---------------------------------------------------

    def compose(self) -> ComposeResult:
        with Container(id="editor-root"):
            yield Static("", id="editor-title")
            yield Static("", id="editor-body")
            yield Static("", id="editor-status")

    def on_mount(self) -> None:
        self._sync_layout()
        self._refresh()

    def on_resize(self, event: events.Resize) -> None:
        self._sync_layout()
        self._refresh()

    def _sync_layout(self) -> None:
        root = self.query_one("#editor-root", Container)
        w = max(1, min(self.size.width, TARGET_WIDTH))
        h = max(1, min(self.size.height, TARGET_HEIGHT))
        root.styles.width = w
        root.styles.height = h

    # --- Geometry helpers ----------------------------------------------------

    def _visible_lines(self) -> int:
        """Number of code lines visible in the body area."""
        try:
            h = max(1, min(self.size.height, TARGET_HEIGHT))
        except Exception:
            h = TARGET_HEIGHT
        # title=1, status=1, body gets the rest
        return max(4, h - 2)

    def _body_width(self) -> int:
        """Usable text width (excluding gutter)."""
        try:
            w = max(1, min(self.size.width, TARGET_WIDTH))
        except Exception:
            w = TARGET_WIDTH
        return max(20, w - LINE_NUM_WIDTH - 3)  # 3 for "│ " prefix and padding

    # --- Key handling --------------------------------------------------------

    def on_key(self, event: events.Key) -> None:
        key = event.key
        _log.debug(
            "editor key=%s char=%r line=%s col=%s",
            key,
            event.character,
            self._cursor_line,
            self._cursor_col,
        )

        if self._show_help:
            # Any key dismisses help
            self._show_help = False
            self._message = ""
            self._refresh()
            return

        # Function keys
        if key == "f1":
            self._show_help = True
            self._message = "Help — press any key to dismiss"
            self._refresh()
            return
        if key in {"f2", "ctrl+s", "ctrl+w"}:
            self._save_file()
            self._refresh()
            return
        if key in {"f3", "escape"}:
            self._exit_editor()
            return
        if key == "insert":
            self._insert_mode = not self._insert_mode
            self._message = f"Insert {'ON' if self._insert_mode else 'OFF'}"
            self._refresh()
            return

        # Navigation
        if key == "up":
            self._move_up()
            return
        if key == "down":
            self._move_down()
            return
        if key == "left":
            self._move_left()
            return
        if key == "right":
            self._move_right()
            return
        if key == "home":
            self._cursor_col = 0
            self._refresh()
            return
        if key == "end":
            self._cursor_col = len(self._current_line())
            self._refresh()
            return
        if key == "pageup":
            self._move_up(self._visible_lines())
            return
        if key == "pagedown":
            self._move_down(self._visible_lines())
            return
        if key == "ctrl+home":
            self._cursor_line = 0
            self._cursor_col = 0
            self._ensure_visible()
            self._refresh()
            return
        if key == "ctrl+end":
            self._cursor_line = len(self._lines) - 1
            self._cursor_col = len(self._current_line())
            self._ensure_visible()
            self._refresh()
            return

        # Editing
        if key == "enter":
            self._split_line()
            return
        if key == "backspace":
            self._backspace()
            return
        if key == "delete":
            self._delete_char()
            return
        if key == "tab":
            self._insert_text("    ")
            return
        # Line operations
        if key == "ctrl+y":
            self._delete_line()
            return
        if key == "ctrl+k":
            self._delete_to_eol()
            return

        # Printable character
        character = event.character
        if character and len(character) == 1 and character.isprintable():
            self._insert_text(character)

    # --- Movement ------------------------------------------------------------

    def _move_up(self, count: int = 1) -> None:
        self._cursor_line = max(0, self._cursor_line - count)
        self._clamp_col()
        self._ensure_visible()
        self._refresh()

    def _move_down(self, count: int = 1) -> None:
        self._cursor_line = min(len(self._lines) - 1, self._cursor_line + count)
        self._clamp_col()
        self._ensure_visible()
        self._refresh()

    def _move_left(self) -> None:
        if self._cursor_col > 0:
            self._cursor_col -= 1
        elif self._cursor_line > 0:
            # Wrap to end of previous line
            self._cursor_line -= 1
            self._cursor_col = len(self._current_line())
        self._ensure_visible()
        self._refresh()

    def _move_right(self) -> None:
        line_len = len(self._current_line())
        if self._cursor_col < line_len:
            self._cursor_col += 1
        elif self._cursor_line < len(self._lines) - 1:
            # Wrap to start of next line
            self._cursor_line += 1
            self._cursor_col = 0
        self._ensure_visible()
        self._refresh()

    def _clamp_col(self) -> None:
        """Ensure cursor column doesn't exceed the current line length."""
        self._cursor_col = min(self._cursor_col, len(self._current_line()))

    def _ensure_visible(self) -> None:
        """Scroll so the cursor line is visible."""
        visible = self._visible_lines()
        if self._cursor_line < self._scroll_offset:
            self._scroll_offset = self._cursor_line
        elif self._cursor_line >= self._scroll_offset + visible:
            self._scroll_offset = self._cursor_line - visible + 1

    # --- Editing operations --------------------------------------------------

    def _current_line(self) -> str:
        if 0 <= self._cursor_line < len(self._lines):
            return self._lines[self._cursor_line]
        return ""

    def _insert_text(self, text: str) -> None:
        line = self._current_line()
        col = self._cursor_col
        if self._insert_mode or col >= len(line):
            new_line = line[:col] + text + line[col:]
        else:
            # Overwrite mode
            end = min(col + len(text), len(line))
            new_line = line[:col] + text + line[end:]
        self._lines[self._cursor_line] = new_line
        self._cursor_col = col + len(text)
        self._dirty = True
        self._refresh()

    def _split_line(self) -> None:
        """Split the current line at the cursor (Enter key)."""
        line = self._current_line()
        col = self._cursor_col
        before = line[:col]
        after = line[col:]
        self._lines[self._cursor_line] = before
        self._lines.insert(self._cursor_line + 1, after)
        self._cursor_line += 1
        self._cursor_col = 0
        self._dirty = True
        self._ensure_visible()
        self._refresh()

    def _backspace(self) -> None:
        if self._cursor_col > 0:
            line = self._current_line()
            col = self._cursor_col
            self._lines[self._cursor_line] = line[: col - 1] + line[col:]
            self._cursor_col -= 1
            self._dirty = True
        elif self._cursor_line > 0:
            # Join with previous line
            prev_line = self._lines[self._cursor_line - 1]
            curr_line = self._current_line()
            self._lines[self._cursor_line - 1] = prev_line + curr_line
            self._lines.pop(self._cursor_line)
            self._cursor_line -= 1
            self._cursor_col = len(prev_line)
            self._dirty = True
            self._ensure_visible()
        self._refresh()

    def _delete_char(self) -> None:
        line = self._current_line()
        col = self._cursor_col
        if col < len(line):
            self._lines[self._cursor_line] = line[:col] + line[col + 1 :]
            self._dirty = True
        elif self._cursor_line < len(self._lines) - 1:
            # Join with next line
            next_line = self._lines[self._cursor_line + 1]
            self._lines[self._cursor_line] = line + next_line
            self._lines.pop(self._cursor_line + 1)
            self._dirty = True
        self._refresh()

    def _delete_line(self) -> None:
        """Delete the entire current line (Ctrl+Y)."""
        if len(self._lines) > 1:
            self._lines.pop(self._cursor_line)
            if self._cursor_line >= len(self._lines):
                self._cursor_line = len(self._lines) - 1
        else:
            self._lines[0] = ""
        self._clamp_col()
        self._dirty = True
        self._ensure_visible()
        self._refresh()

    def _delete_to_eol(self) -> None:
        """Delete from cursor to end of line (Ctrl+K)."""
        line = self._current_line()
        self._lines[self._cursor_line] = line[: self._cursor_col]
        self._dirty = True
        self._refresh()

    def _exit_editor(self) -> None:
        """Exit the editor. If dirty, the user already chose not to save."""
        if self._dirty:
            self._message = "Unsaved changes! F2=Save, F3=Exit without saving"
            # On second F3/Esc press, actually exit
            if hasattr(self, "_exit_warned") and self._exit_warned:
                self.dismiss(False)
                return
            self._exit_warned = True
            self._refresh()
            return
        self.dismiss(not self._dirty)

    # --- Rendering -----------------------------------------------------------

    def _refresh(self) -> None:
        if not self.is_mounted:
            return
        self.query_one("#editor-title", Static).update(self._render_title())
        self.query_one("#editor-body", Static).update(self._render_body())
        self.query_one("#editor-status", Static).update(self._render_status())

    def _render_title(self) -> str:
        name = self._file_path.name.upper()
        dirty_marker = " *" if self._dirty else ""
        return f" MODIFY COMMAND FILE: {name}{dirty_marker}"

    def _render_body(self) -> str:
        if self._show_help:
            return self._render_help_text()

        visible = self._visible_lines()
        body_width = self._body_width()
        lines_out: list[str] = []

        for i in range(visible):
            line_idx = self._scroll_offset + i
            if line_idx < len(self._lines):
                line_num = str(line_idx + 1).rjust(LINE_NUM_WIDTH - 1)
                line_text = self._lines[line_idx]

                # Apply horizontal scrolling if line is wider than body
                # For now, just truncate to body_width
                display_text = line_text[:body_width]

                # Show cursor position with a block character
                if line_idx == self._cursor_line:
                    col = self._cursor_col
                    if col < len(display_text):
                        # Cursor on a character — show it highlighted
                        before = display_text[:col]
                        cursor_char = display_text[col]
                        after = display_text[col + 1 :]
                        display_text = (
                            f"{before}[reverse]{cursor_char}[/reverse]{after}"
                        )
                    elif col == len(display_text):
                        # Cursor at end of line
                        display_text += "[reverse] [/reverse]"

                lines_out.append(f"{line_num} \u2502 {display_text}")
            else:
                # Empty line below the content — show tilde like vi
                pad = " " * (LINE_NUM_WIDTH - 1)
                lines_out.append(f"{pad} \u2502")

        return "\n".join(lines_out)

    def _render_status(self) -> str:
        line_display = self._cursor_line + 1
        col_display = self._cursor_col + 1
        ins_text = "Ins" if self._insert_mode else "Ovr"
        total_lines = len(self._lines)
        msg = self._message or ""
        return (
            f" Line {line_display}  Col {col_display}  "
            f"Lines {total_lines}  {ins_text}  "
            f"F1=Help  F2=Save  F3=Exit  "
            f"{msg}"
        )

    def _render_help_text(self) -> str:
        return "\n".join(
            [
                "",
                "  Program Editor Help",
                "",
                "  Navigation:",
                "    Arrow keys     Move cursor",
                "    Home / End     Start / end of line",
                "    PgUp / PgDn    Page up / down",
                "    Ctrl+Home      Top of file",
                "    Ctrl+End       End of file",
                "",
                "  Editing:",
                "    Enter          New line",
                "    Backspace      Delete character left",
                "    Delete         Delete character right",
                "    Tab            Insert 4 spaces",
                "    Insert         Toggle insert / overwrite",
                "    Ctrl+Y         Delete entire line",
                "    Ctrl+K         Delete to end of line",
                "",
                "  File:",
                "    F2 / Ctrl+S    Save file",
                "    F3 / Esc       Exit editor",
                "",
                "  Press any key to dismiss this help.",
            ]
        )
