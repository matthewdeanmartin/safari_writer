"""Main Safari Base shell screen."""

from __future__ import annotations

import logging
from pathlib import Path

from textual import events
from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Static

from safari_base.database import BaseSession, DEFAULT_ADDRESS_SCHEMA

__all__ = ["SCREEN_CSS", "SafariBaseScreen", "clamp_shell_dimension"]

_log = logging.getLogger("safari_base.screen")
_log.setLevel(logging.DEBUG)
if not _log.handlers:
    _handler = logging.FileHandler(Path(__file__).resolve().parent / "debug.log", mode="a")
    _handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
    _log.addHandler(_handler)

TARGET_WIDTH = 100
TARGET_HEIGHT = 34


def clamp_shell_dimension(available: int, target: int) -> int:
    """Clamp shell size to the live terminal while preserving a target size ceiling."""

    return max(1, min(available, target))


SCREEN_CSS = """
SafariBaseScreen {
    background: $background;
    align: center middle;
}

#base-root {
    width: 100;
    height: 34;
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

#prompt-line {
    height: 1;
    background: $panel;
    color: $foreground;
    padding: 0 1;
}

#status-bar {
    height: 1;
    background: $primary;
    color: $foreground;
    padding: 0 1;
}
"""


class SafariBaseScreen(Screen[None]):
    """Roomier dBASE-style shell with a single-line prompt and status bar."""

    CSS = SCREEN_CSS

    def __init__(self, session: BaseSession) -> None:
        super().__init__()
        self.session = session
        self._prompt_buffer = ""
        self._prompt_cursor = 0
        self._message = "Safari Base ready"
        self._view_mode = "browse"
        self._cursor_row = 0
        self._row_offset = 0
        self._cursor_col = 0
        self._col_offset = 0
        self._insert_mode = True
        self._caps_mode = False
        self._append_record: list[str] | None = None
        self._append_field_idx = 0
        self._append_field_cursor = 0

    def compose(self) -> ComposeResult:
        with Container(id="base-root"):
            yield Static("", id="scoreboard")
            with Container(id="workspace-box"):
                yield Static("", id="workspace-title")
                yield Static("", id="workspace-body")
            yield Static("", id="prompt-line")
            yield Static("", id="status-bar")

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
            "key=%s character=%r mode=%s prompt=%r cursor=%s row=%s offset=%s",
            key,
            event.character,
            self._view_mode,
            self._prompt_buffer,
            self._prompt_cursor,
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
        if key in {"f2", "f10", "alt"}:
            self._show_assist()
            return
        if key in {"f3", "ctrl+a"}:
            self._start_append()
            return
        if key == "f4":
            self._show_not_implemented("Edit form")
            return
        if key in {"f5", "ctrl+d"}:
            self._show_not_implemented("Delete mark")
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
        if key == "escape":
            self._prompt_buffer = ""
            self._prompt_cursor = 0
            self._message = "Prompt cleared"
            self._refresh()
            return
        if key == "up":
            self._move_cursor(-1)
            return
        if key == "down":
            self._move_cursor(1)
            return
        if key in {"left", "right", "home", "end", "tab", "shift+tab"} and self._handle_browse_navigation(key):
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
            self._prompt_cursor = 0
            self._refresh()
            return
        if key == "left":
            self._prompt_cursor = max(0, self._prompt_cursor - 1)
            self._refresh_prompt()
            return
        if key == "right":
            self._prompt_cursor = min(len(self._prompt_buffer), self._prompt_cursor + 1)
            self._refresh_prompt()
            return
        if key == "home":
            self._prompt_cursor = 0
            self._refresh_prompt()
            return
        if key == "end":
            self._prompt_cursor = len(self._prompt_buffer)
            self._refresh_prompt()
            return
        if key == "backspace":
            self._prompt_buffer, self._prompt_cursor = self._delete_backward(
                self._prompt_buffer,
                self._prompt_cursor,
            )
            self._refresh_prompt()
            return
        if key == "delete":
            self._prompt_buffer, self._prompt_cursor = self._delete_forward(
                self._prompt_buffer,
                self._prompt_cursor,
            )
            self._refresh_prompt()
            return
        character = event.character
        if character and len(character) == 1 and character.isprintable():
            self._prompt_buffer, self._prompt_cursor = self._accept_text(
                self._prompt_buffer,
                character,
                self._prompt_cursor,
                max_len=self._prompt_max_length(),
            )
            self._refresh_prompt()

    def _handle_append_key(self, key: str, character: str | None) -> bool:
        if key in {"f2", "ctrl+s", "ctrl+w"}:
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
        if key in {"shift+tab", "up"}:
            self._append_field_idx = max(0, self._append_field_idx - 1)
            self._append_field_cursor = self._current_append_field_length()
            self._refresh()
            return True
        if key in {"tab", "down"}:
            self._append_field_idx = min(
                len(self.session.current_columns()) - 1,
                self._append_field_idx + 1,
            )
            self._append_field_cursor = self._current_append_field_length()
            self._refresh()
            return True
        if key == "enter":
            if self._append_field_idx >= len(self.session.current_columns()) - 1:
                self._save_append()
            else:
                self._append_field_idx += 1
                self._append_field_cursor = self._current_append_field_length()
                self._refresh()
            return True
        if key == "left":
            self._append_field_cursor = max(0, self._append_field_cursor - 1)
            self._refresh()
            return True
        if key == "right":
            self._append_field_cursor = min(
                self._current_append_field_length(),
                self._append_field_cursor + 1,
            )
            self._refresh()
            return True
        if key == "home":
            self._append_field_cursor = 0
            self._refresh()
            return True
        if key == "end":
            self._append_field_cursor = self._current_append_field_length()
            self._refresh()
            return True
        if key == "backspace":
            if self._append_record is None:
                return True
            current_value = self._append_record[self._append_field_idx]
            updated, cursor = self._delete_backward(
                current_value,
                self._append_field_cursor,
            )
            self._append_record[self._append_field_idx] = updated
            self._append_field_cursor = cursor
            self._refresh()
            return True
        if key == "delete":
            if self._append_record is None:
                return True
            current_value = self._append_record[self._append_field_idx]
            updated, cursor = self._delete_forward(
                current_value,
                self._append_field_cursor,
            )
            self._append_record[self._append_field_idx] = updated
            self._append_field_cursor = cursor
            self._refresh()
            return True
        if character and len(character) == 1 and character.isprintable():
            if self._append_record is None:
                return True
            field_name = self.session.current_columns()[self._append_field_idx]
            max_len = self._field_max_length(field_name)
            updated, cursor = self._accept_text(
                self._append_record[self._append_field_idx],
                character,
                self._append_field_cursor,
                max_len=max_len,
            )
            self._append_record[self._append_field_idx] = updated
            self._append_field_cursor = cursor
            self._refresh()
            return True
        return False

    def _handle_browse_navigation(self, key: str) -> bool:
        if self._view_mode != "browse" or self._prompt_buffer:
            return False
        if key in {"left", "shift+tab"}:
            self._move_column(-1)
            return True
        if key in {"right", "tab"}:
            self._move_column(1)
            return True
        if key == "home":
            self._set_column(0)
            return True
        if key == "end":
            self._set_column(len(self.session.current_columns()) - 1)
            return True
        return False

    def _show_assist(self) -> None:
        self._show_not_implemented("ASSIST menu")

    def _current_append_field_length(self) -> int:
        if self._append_record is None:
            return 0
        return len(self._append_record[self._append_field_idx])

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
        self._append_field_cursor = 0
        self._message = "Append form active"
        _log.debug("append-start table=%s", self.session.current_table)
        self._refresh()

    def _cancel_append(self) -> None:
        self._append_record = None
        self._append_field_idx = 0
        self._append_field_cursor = 0
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
        self._append_field_cursor = 0
        self._view_mode = "browse"
        self._cursor_row = max(0, self.session.record_count() - 1)
        self._ensure_cursor_visible()
        self._message = f"Saved record {rowid}"
        _log.debug("append-save rowid=%s", rowid)
        self._refresh()

    def _accept_text(
        self,
        current: str,
        character: str,
        cursor: int,
        max_len: int,
    ) -> tuple[str, int]:
        char = character.upper() if self._caps_mode else character
        if self._insert_mode or cursor >= len(current):
            updated = current[:cursor] + char + current[cursor:]
        else:
            updated = current[:cursor] + char + current[cursor + 1 :]
        updated = updated[:max_len]
        return updated, min(cursor + 1, len(updated))

    def _delete_backward(self, current: str, cursor: int) -> tuple[str, int]:
        if cursor <= 0:
            return current, cursor
        updated = current[: cursor - 1] + current[cursor:]
        return updated, cursor - 1

    def _delete_forward(self, current: str, cursor: int) -> tuple[str, int]:
        if cursor >= len(current):
            return current, cursor
        updated = current[:cursor] + current[cursor + 1 :]
        return updated, cursor

    def _field_max_length(self, field_name: str) -> int:
        width_map = {name: width for name, width in DEFAULT_ADDRESS_SCHEMA}
        return width_map.get(field_name, 20)

    def _browse_columns(self) -> list[tuple[str, int]]:
        width_map = {name: width for name, width in DEFAULT_ADDRESS_SCHEMA}
        return [
            (name, max(4, min(width_map.get(name, len(name) + 2), 14)))
            for name in self.session.current_columns()
        ]

    def _visible_browse_columns(self) -> tuple[list[str], list[int], int]:
        columns_with_widths = self._browse_columns()
        if not columns_with_widths:
            return [], [], 0

        available = self._browse_grid_width() - 6
        start = min(self._col_offset, len(columns_with_widths) - 1)
        visible_names: list[str] = []
        visible_widths: list[int] = []
        index = start
        while index < len(columns_with_widths):
            name, width = columns_with_widths[index]
            gap = 1 if visible_widths else 0
            if visible_widths and available < width + gap:
                break
            if not visible_widths and available < 4:
                break
            available -= width + gap
            visible_names.append(name)
            visible_widths.append(width)
            index += 1
        if not visible_names:
            name, width = columns_with_widths[start]
            visible_names.append(name)
            visible_widths.append(min(width, max(4, self._browse_grid_width() - 6)))
        return visible_names, visible_widths, start

    def _current_field_name(self) -> str:
        columns = self.session.current_columns()
        if not columns:
            return ""
        self._cursor_col = min(max(self._cursor_col, 0), len(columns) - 1)
        return columns[self._cursor_col]

    def _set_column(self, index: int) -> None:
        columns = self.session.current_columns()
        if not columns:
            self._cursor_col = 0
            self._col_offset = 0
            self._refresh()
            return
        self._cursor_col = min(max(0, index), len(columns) - 1)
        self._ensure_column_visible()
        self._message = f"Field {self._current_field_name()}"
        self._refresh()

    def _move_column(self, delta: int) -> None:
        self._set_column(self._cursor_col + delta)

    def _ensure_column_visible(self) -> None:
        columns = self.session.current_columns()
        if not columns:
            self._col_offset = 0
            return
        self._cursor_col = min(max(self._cursor_col, 0), len(columns) - 1)
        self._col_offset = min(max(0, self._col_offset), len(columns) - 1)
        visible_names, _visible_widths, start = self._visible_browse_columns()
        if self._cursor_col < start:
            self._col_offset = self._cursor_col
        elif visible_names:
            end = start + len(visible_names) - 1
            if self._cursor_col > end:
                self._col_offset = self._cursor_col
                while True:
                    visible_names, _visible_widths, start = self._visible_browse_columns()
                    end = start + len(visible_names) - 1
                    if self._cursor_col <= end or self._col_offset <= 0:
                        break
                    self._col_offset -= 1

    def _prompt_max_length(self) -> int:
        return max(20, self._shell_width() - 6)

    def _shell_width(self) -> int:
        return clamp_shell_dimension(self.size.width, TARGET_WIDTH)

    def _shell_height(self) -> int:
        return clamp_shell_dimension(self.size.height, TARGET_HEIGHT)

    def _browse_grid_width(self) -> int:
        return max(40, self._shell_width() - 8)

    def _sync_layout_bounds(self) -> None:
        root = self.query_one("#base-root", Container)
        target_width = self._shell_width()
        target_height = self._shell_height()
        root.styles.width = target_width
        root.styles.height = target_height
        _log.debug("layout width=%s height=%s", target_width, target_height)

    def _visible_rows(self) -> int:
        return max(4, self._shell_height() - 8)

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
        self._ensure_column_visible()
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
            self._show_assist()
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
            self._cursor_col = 0
            self._col_offset = 0
            self._view_mode = "browse"
            self._message = f"Using {self.session.current_table}"
            return

        self._message = f"Unknown command: {command}"

    def _refresh(self) -> None:
        self.query_one("#scoreboard", Static).update(self._scoreboard_text())
        self.query_one("#workspace-title", Static).update(self._workspace_title())
        self.query_one("#workspace-body", Static).update(self._workspace_text())
        self.query_one("#status-bar", Static).update(self._status_text())
        self._refresh_prompt()

    def _refresh_prompt(self) -> None:
        self.query_one("#prompt-line", Static).update(f". {self._prompt_buffer}")

    def _scoreboard_text(self) -> str:
        mode = self._view_mode.upper().ljust(9)
        return (
            f" SAFARI BASE  Area [A]  Ins {'ON ' if self._insert_mode else 'OFF'}  "
            f"Caps {'ON ' if self._caps_mode else 'OFF'}  Mode {mode}  "
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
        visible_columns, adjusted_widths, start_col = self._visible_browse_columns()

        header_cells = ["REC#".ljust(5)]
        divider_cells = ["".ljust(5, "-")]
        for column_index, (name, width) in enumerate(zip(visible_columns, adjusted_widths), start=start_col):
            if column_index == self._cursor_col:
                header_cells.append(self._focus_cell(name, width))
            else:
                header_cells.append(name[:width].ljust(width))
            divider_cells.append("".ljust(width, "-"))

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
            visible_values = values[start_col : start_col + len(adjusted_widths)]
            for column_index, (value, width) in enumerate(zip(visible_values, adjusted_widths), start=start_col):
                if absolute_index == self._cursor_row and column_index == self._cursor_col:
                    row_cells.append(self._focus_cell(value, width))
                else:
                    row_cells.append(value[:width].ljust(width))
            lines.append(" ".join(row_cells))

        while len(lines) < visible_rows + 2:
            lines.append("")

        return "\n".join(lines)

    def _focus_cell(self, value: str, width: int) -> str:
        inner_width = max(1, width - 2)
        return f"[{value[:inner_width].ljust(inner_width)}]"

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
                "  Left/Right/Home/End edit the dot prompt",
                "  F1 Help, F6 Structure, F7 Tables, F8 Browse",
                "  F10 Assist (F2 legacy alias), F3 Append, F4 Edit",
                "  Ctrl+D delete placeholder (F5 legacy alias)",
                "  Insert toggles Insert mode",
                "  CapsLock toggles Caps mode (Ctrl+L legacy alias)",
                "  Ctrl+S/Ctrl+W/F2 save append, Esc/F3 cancel",
                "  Ctrl+A opens append, Ctrl+Q quits",
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
            lines.append(f" {marker} {field_name:<10}: {value:<28} [{len(value):>2}/{max_len}]")
        lines.extend(
            [
                "",
                " Enter/Tab/Down next field   Shift+Tab/Up previous field",
                " Left/Right/Home/End move in field",
                " Ctrl+S/Ctrl+W/F2 save       Esc/F3 cancel",
                " Insert toggle insert        CapsLock/Ctrl+L toggle caps",
            ]
        )
        return "\n".join(lines)

    def _status_text(self) -> str:
        record_count = self.session.record_count()
        current_record = self._cursor_row + 1 if record_count else 0
        field_name = self._current_field_name()
        field_count = len(self.session.current_columns())
        database_label = (
            str(self.session.database_path)
            if self.session.database_path is not None
            else "(memory)"
        )
        return (
            f" {database_label}  {self.session.current_table}  [A]  "
            f"Rec {current_record}/{record_count}  "
            f"Fld {field_name or '-'} {min(self._cursor_col + 1, max(1, field_count))}/{field_count or 0}  "
            f"Ins {'ON' if self._insert_mode else 'OFF'}  "
            f"Caps {'ON' if self._caps_mode else 'OFF'}  "
            f"{self._message}"
        )
