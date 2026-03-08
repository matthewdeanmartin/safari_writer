"""Main boxed Safari Base screen."""

from __future__ import annotations

import logging
from pathlib import Path

from textual import events
from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Static

from safari_base.database import BaseSession, DEFAULT_ADDRESS_SCHEMA

__all__ = ["SafariBaseScreen"]

_log = logging.getLogger("safari_base.screen")
_log.setLevel(logging.DEBUG)
if not _log.handlers:
    _handler = logging.FileHandler(Path(__file__).resolve().parent / "debug.log", mode="a")
    _handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
    _log.addHandler(_handler)

TARGET_WIDTH = 80
TARGET_HEIGHT = 60


def clamp_shell_dimension(available: int, target: int) -> int:
    """Clamp shell size to the live terminal while preserving a target size ceiling."""

    return max(1, min(available, target))


SCREEN_CSS = """
SafariBaseScreen {
    background: $background;
    align: center middle;
}

#base-root {
    width: 80;
    height: 60;
    background: $surface;
    layout: vertical;
}

#scoreboard {
    height: 1;
    background: $secondary;
    color: $foreground;
    padding: 0 1;
}

#workspace-box {
    height: 1fr;
    border: solid $accent;
    background: $surface;
    layout: vertical;
}

#workspace-title {
    height: 1;
    background: $primary;
    color: $foreground;
    padding: 0 1;
}

#workspace-body {
    height: 1fr;
    color: $foreground;
    padding: 0 1;
}

#prompt-box {
    height: 4;
    border: solid $accent;
    background: $panel;
    layout: vertical;
}

#prompt-label {
    height: 1;
    background: $secondary;
    color: $foreground;
    padding: 0 1;
}

#prompt-line {
    height: 1;
    color: $foreground;
    padding: 0 1;
}

#status-bar {
    height: 1;
    background: $primary;
    color: $foreground;
    padding: 0 1;
}

#button-bar {
    height: 1;
    background: $secondary;
    color: $accent;
    padding: 0 1;
}

#help-bar {
    height: 1;
    background: $panel;
    color: $foreground;
    padding: 0 1;
}
"""

VISIBLE_ROWS = 48
GRID_WIDTH = 74


class SafariBaseScreen(Screen[None]):
    """Minimal dBASE-style shell with boxed browse and dot prompt."""

    CSS = SCREEN_CSS

    def __init__(self, session: BaseSession) -> None:
        super().__init__()
        self.session = session
        self._prompt_buffer = ""
        self._message = "Safari Base ready"
        self._view_mode = "browse"
        self._cursor_row = 0
        self._row_offset = 0
        self._insert_mode = True
        self._caps_mode = False
        self._append_record: list[str] | None = None
        self._append_field_idx = 0

    def compose(self) -> ComposeResult:
        with Container(id="base-root"):
            yield Static("", id="scoreboard")
            with Container(id="workspace-box"):
                yield Static("", id="workspace-title")
                yield Static("", id="workspace-body")
            with Container(id="prompt-box"):
                yield Static("Dot Prompt", id="prompt-label")
                yield Static("", id="prompt-line")
            yield Static("", id="status-bar")
            yield Static("", id="button-bar")
            yield Static("", id="help-bar")

    def on_mount(self) -> None:
        _log.debug("mounted table=%s", self.session.current_table)
        self._sync_layout_bounds()
        self._refresh()

    def on_resize(self, event: events.Resize) -> None:
        _log.debug("resize width=%s height=%s", event.size.width, event.size.height)
        self._sync_layout_bounds()
        self._refresh()

    def on_key(self, event) -> None:  # type: ignore[override]
        key = event.key
        _log.debug(
            "key=%s character=%r mode=%s prompt=%r row=%s offset=%s",
            key,
            event.character,
            self._view_mode,
            self._prompt_buffer,
            self._cursor_row,
            self._row_offset,
        )
        if self._view_mode == "append" and self._handle_append_key(key, event.character):
            return
        if key == "ctrl+q":
            self.app.exit()
            return
        if key == "f1":
            self._show_help()
            return
        if key == "insert":
            self._toggle_insert_mode()
            return
        if key in {"caps_lock", "ctrl+l"}:
            self._toggle_caps_mode()
            return
        if key == "f2":
            self._show_not_implemented("ASSIST menu")
            return
        if key in {"f3", "ctrl+a"}:
            self._start_append()
            return
        if key == "f4":
            self._show_not_implemented("Edit form")
            return
        if key == "f5":
            self._show_not_implemented("Delete record")
            return
        if key == "f6":
            self._show_structure()
            return
        if key == "f7":
            self._show_tables()
            return
        if key == "f8":
            self._show_browse()
            return
        if key == "f10":
            self.app.exit()
            return
        if key == "escape":
            self._prompt_buffer = ""
            self._message = "Prompt cleared"
            self._refresh()
            return
        if key == "up":
            self._move_cursor(-1)
            return
        if key == "down":
            self._move_cursor(1)
            return
        if key == "pageup":
            self._move_cursor(-self._visible_rows())
            return
        if key == "pagedown":
            self._move_cursor(self._visible_rows())
            return
        if key == "enter":
            self._run_command(self._prompt_buffer.strip())
            self._prompt_buffer = ""
            self._refresh()
            return
        if key == "backspace":
            self._prompt_buffer = self._prompt_buffer[:-1]
            self._refresh_prompt()
            return
        character = event.character
        if character and len(character) == 1 and character.isprintable():
            self._prompt_buffer = self._accept_text(
                self._prompt_buffer,
                character,
                max_len=70,
            )
            self._refresh_prompt()
            return

    def _handle_append_key(self, key: str, character: str | None) -> bool:
        if key == "f2":
            self._save_append()
            return True
        if key in {"escape", "f3"}:
            self._cancel_append()
            return True
        if key == "insert":
            self._toggle_insert_mode()
            return True
        if key in {"caps_lock", "ctrl+l"}:
            self._toggle_caps_mode()
            return True
        if key == "up":
            self._append_field_idx = max(0, self._append_field_idx - 1)
            self._refresh()
            return True
        if key == "down":
            self._append_field_idx = min(
                len(self.session.current_columns()) - 1,
                self._append_field_idx + 1,
            )
            self._refresh()
            return True
        if key == "enter":
            if self._append_field_idx >= len(self.session.current_columns()) - 1:
                self._save_append()
            else:
                self._append_field_idx += 1
                self._refresh()
            return True
        if key == "backspace":
            if self._append_record is None:
                return True
            current_value = self._append_record[self._append_field_idx]
            self._append_record[self._append_field_idx] = current_value[:-1]
            self._refresh()
            return True
        if character and len(character) == 1 and character.isprintable():
            if self._append_record is None:
                return True
            field_name = self.session.current_columns()[self._append_field_idx]
            max_len = self._field_max_length(field_name)
            self._append_record[self._append_field_idx] = self._accept_text(
                self._append_record[self._append_field_idx],
                character,
                max_len=max_len,
            )
            self._refresh()
            return True
        return False

    def _toggle_insert_mode(self) -> None:
        self._insert_mode = not self._insert_mode
        self._message = f"Insert mode {'ON' if self._insert_mode else 'OFF'}"
        _log.debug("insert-mode=%s", self._insert_mode)
        self._refresh()

    def _toggle_caps_mode(self) -> None:
        self._caps_mode = not self._caps_mode
        self._message = f"Caps mode {'ON' if self._caps_mode else 'OFF'}"
        _log.debug("caps-mode=%s", self._caps_mode)
        self._refresh()

    def _start_append(self) -> None:
        self._view_mode = "append"
        self._append_record = [""] * len(self.session.current_columns())
        self._append_field_idx = 0
        self._message = "Append form active"
        _log.debug("append-start table=%s", self.session.current_table)
        self._refresh()

    def _cancel_append(self) -> None:
        self._append_record = None
        self._append_field_idx = 0
        self._view_mode = "browse"
        self._message = "Append cancelled"
        _log.debug("append-cancel")
        self._refresh()

    def _save_append(self) -> None:
        if self._append_record is None:
            return
        rowid = self.session.append_record(self._append_record)
        self._append_record = None
        self._append_field_idx = 0
        self._view_mode = "browse"
        self._cursor_row = max(0, self.session.record_count() - 1)
        self._ensure_cursor_visible()
        self._message = f"Saved record {rowid}"
        _log.debug("append-save rowid=%s", rowid)
        self._refresh()

    def _accept_text(self, current: str, character: str, max_len: int) -> str:
        char = character.upper() if self._caps_mode else character
        if self._insert_mode or not current:
            updated = current + char
        else:
            updated = current[:-1] + char
        return updated[:max_len]

    def _field_max_length(self, field_name: str) -> int:
        width_map = {name: width for name, width in DEFAULT_ADDRESS_SCHEMA}
        return width_map.get(field_name, 20)

    def _sync_layout_bounds(self) -> None:
        root = self.query_one("#base-root", Container)
        target_width = clamp_shell_dimension(self.size.width, TARGET_WIDTH)
        target_height = clamp_shell_dimension(self.size.height, TARGET_HEIGHT)
        root.styles.width = target_width
        root.styles.height = target_height
        _log.debug("layout width=%s height=%s", target_width, target_height)

    def _visible_rows(self) -> int:
        shell_height = clamp_shell_dimension(self.size.height, TARGET_HEIGHT)
        return max(4, shell_height - 12)

    def _show_help(self) -> None:
        self._view_mode = "help"
        self._message = "Showing startup help"
        self._refresh()

    def _show_not_implemented(self, feature: str) -> None:
        self._message = f"{feature} not implemented yet"
        _log.debug("not-implemented feature=%s", feature)
        self._refresh()

    def _show_structure(self) -> None:
        self._view_mode = "structure"
        self._message = f"Structure for {self.session.current_table}"
        self._refresh()

    def _show_tables(self) -> None:
        self._view_mode = "tables"
        self._message = "Listing tables"
        self._refresh()

    def _show_browse(self) -> None:
        self._view_mode = "browse"
        self._message = f"Browsing {self.session.current_table}"
        self._refresh()

    def _move_cursor(self, delta: int) -> None:
        record_count = self.session.record_count()
        if record_count == 0:
            self._message = "No records in current table"
            self._refresh()
            return
        self._view_mode = "browse"
        self._cursor_row = min(max(0, self._cursor_row + delta), record_count - 1)
        self._ensure_cursor_visible()
        self._refresh()

    def _ensure_cursor_visible(self) -> None:
        visible_rows = self._visible_rows()
        if self._cursor_row < self._row_offset:
            self._row_offset = self._cursor_row
        elif self._cursor_row >= self._row_offset + visible_rows:
            self._row_offset = self._cursor_row - visible_rows + 1

    def _run_command(self, command: str) -> None:
        if not command:
            self._message = "Ready"
            return

        upper = command.upper()
        if upper in {"BROWSE", "BRO"}:
            self._show_browse()
            return
        if upper in {"HELP", "?"}:
            self._show_help()
            return
        if upper in {"TABLES", "DIR"}:
            self._show_tables()
            return
        if upper in {"STRUCT", "STRUCTURE", "DISPLAY STRUCTURE"}:
            self._show_structure()
            return
        if upper == "APPEND":
            self._start_append()
            return
        if upper in {"EDIT", "MODIFY"}:
            self._show_not_implemented("Edit form")
            return
        if upper in {"DELETE", "DEL"}:
            self._show_not_implemented("Delete record")
            return
        if upper in {"ASSIST", "MENU"}:
            self._show_not_implemented("ASSIST menu")
            return
        if upper in {"QUIT", "EXIT"}:
            self.app.exit()
            return
        if upper.startswith("USE "):
            table_name = command[4:].strip()
            try:
                self.session.set_current_table(table_name)
            except ValueError:
                self._message = f"Table not found: {table_name}"
                return
            self._cursor_row = 0
            self._row_offset = 0
            self._view_mode = "browse"
            self._message = f"Using {self.session.current_table}"
            return

        self._message = f"Unknown command: {command}"

    def _refresh(self) -> None:
        self.query_one("#scoreboard", Static).update(self._scoreboard_text())
        self.query_one("#workspace-title", Static).update(self._workspace_title())
        self.query_one("#workspace-body", Static).update(self._workspace_text())
        self.query_one("#status-bar", Static).update(self._status_text())
        self.query_one("#button-bar", Static).update(self._button_text())
        self.query_one("#help-bar", Static).update(self._help_text())
        self._refresh_prompt()

    def _refresh_prompt(self) -> None:
        self.query_one("#prompt-line", Static).update(f". {self._prompt_buffer}")

    def _scoreboard_text(self) -> str:
        mode = self._view_mode.upper().ljust(9)
        return (
            f" Ins {'ON ' if self._insert_mode else 'OFF'}  "
            f"Caps {'ON ' if self._caps_mode else 'OFF'}  "
            f"Area A  Mode {mode}  "
            f"Table {self.session.current_table}"
        )

    def _workspace_title(self) -> str:
        database_name = (
            str(self.session.database_path.name)
            if self.session.database_path is not None
            else "(memory)"
        )
        return f" SAFARI BASE  Database: {database_name}  Table: {self.session.current_table} "

    def _workspace_text(self) -> str:
        if self._view_mode == "browse":
            return self._render_browse()
        if self._view_mode == "append":
            return self._render_append()
        if self._view_mode == "tables":
            return self._render_tables()
        if self._view_mode == "structure":
            return self._render_structure()
        return self._render_help()

    def _render_browse(self) -> str:
        columns = self.session.current_columns()
        width_map = {name: width for name, width in DEFAULT_ADDRESS_SCHEMA}
        widths = [max(4, min(width_map.get(name, len(name) + 2), 12)) for name in columns]

        remaining = GRID_WIDTH - 6 - max(0, len(widths) - 1)
        adjusted_widths: list[int] = []
        for width in widths:
            column_width = min(width, max(4, remaining))
            adjusted_widths.append(column_width)
            remaining -= column_width
            if remaining <= 0:
                break
        visible_columns = columns[: len(adjusted_widths)]

        header_cells = ["REC#".ljust(5)]
        divider_cells = ["".ljust(5, "─")]
        for name, width in zip(visible_columns, adjusted_widths):
            header_cells.append(name[:width].ljust(width))
            divider_cells.append("".ljust(width, "─"))

        lines = [
            " ".join(header_cells),
            " ".join(divider_cells),
        ]

        visible_rows = self._visible_rows()
        browse_rows = self.session.browse_rows(visible_rows, self._row_offset)
        for visible_index, (rowid, values) in enumerate(browse_rows):
            absolute_index = self._row_offset + visible_index
            pointer = ">" if absolute_index == self._cursor_row else " "
            row_cells = [f"{pointer}{str(rowid).rjust(4)}"]
            for value, width in zip(values[: len(adjusted_widths)], adjusted_widths):
                row_cells.append(value[:width].ljust(width))
            lines.append(" ".join(row_cells))

        while len(lines) < visible_rows + 2:
            lines.append("")

        return "\n".join(lines)

    def _render_tables(self) -> str:
        tables = self.session.table_names()
        body = [" Available tables", "", *[f"  {name}" for name in tables]]
        return "\n".join(body)

    def _render_structure(self) -> str:
        rows = self.session.structure_rows()
        lines = [" Field      Type", " ---------- ----------------"]
        for name, type_spec in rows:
            lines.append(f" {name:<10} {type_spec}")
        return "\n".join(lines)

    def _render_help(self) -> str:
        return "\n".join(
            [
                " Startup commands",
                "",
                "  BROWSE          Return to the boxed table view",
                "  ASSIST          Show the menu placeholder",
                "  TABLES          Show available tables",
                "  USE <table>     Switch to another table",
                "  STRUCT          Show current table structure",
                "  APPEND          Open the append form",
                "  EDIT            Show edit placeholder",
                "  DELETE          Show delete placeholder",
                "  QUIT            Leave Safari Base",
                "",
                " Keys",
                "  Up/Down, PgUp/PgDn navigate rows",
                "  F1 Help, F6 Structure, F7 Tables, F8 Browse",
                "  F2 Assist, F3 Append, F4 Edit, F5 Delete",
                "  Insert toggles Insert mode",
                "  CapsLock or Ctrl+L toggles Caps mode",
                "  Ctrl+A opens the append form",
                "  Esc clears the dot prompt",
                "  Ctrl+Q or F10 quits",
            ]
        )

    def _render_append(self) -> str:
        if self._append_record is None:
            return " Append form unavailable"

        columns = self.session.current_columns()
        lines = [
            " APPEND RECORD",
            "",
        ]
        for index, field_name in enumerate(columns):
            marker = ">" if index == self._append_field_idx else " "
            value = self._append_record[index]
            max_len = self._field_max_length(field_name)
            lines.append(f" {marker} {field_name:<10}: {value:<20} [{len(value):>2}/{max_len}]")
        lines.extend(
            [
                "",
                " Enter/Down next field   Up previous field",
                " F2 save record          Esc/F3 cancel",
                " Insert toggle insert    CapsLock/Ctrl+L toggle caps",
            ]
        )
        return "\n".join(lines)

    def _status_text(self) -> str:
        record_count = self.session.record_count()
        current_record = self._cursor_row + 1 if record_count else 0
        database_label = (
            str(self.session.database_path)
            if self.session.database_path is not None
            else "(memory)"
        )
        return (
            f" {database_label}  [A]  Rec {current_record}/{record_count}  "
            f"{self._message}"
        )

    def _help_text(self) -> str:
        if self._view_mode == "append":
            return " Type into the highlighted field, then Enter or Down to continue "
        return " Arrows Move  PgUp/PgDn Scroll  Enter Run Command  Esc Clear Prompt "

    def _button_text(self) -> str:
        if self._view_mode == "append":
            return " F2 Save  F3 Cancel  Insert Toggle Ins  Ctrl+L Toggle Caps  F10 Quit "
        return (
            " F1 Help  F2 Assist  F3 Append  F4 Edit  F5 Delete  "
            "F6 Struct  F7 Tables  F8 Browse  F10 Quit "
        )
