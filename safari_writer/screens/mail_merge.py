"""Mail Merge screen — flat-file database for form letters."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from textual.app import ComposeResult
from textual.screen import ModalScreen, Screen
from textual.widgets import Static
from textual import events

from safari_writer.mail_merge_db import (
    DEFAULT_FIELDS as _DEFAULT_FIELDS,
    MAX_FIELD_DATA_LEN,
    MAX_FIELD_NAME_LEN,
    MAX_FIELDS,
    MAX_RECORDS as _MAX_RECORDS,
    FieldDef,
    MailMergeDB,
    load_mail_merge_db,
    save_mail_merge_db,
)
from safari_writer.state import AppState

DEFAULT_FIELDS = _DEFAULT_FIELDS
MAX_RECORDS = _MAX_RECORDS


# ---------------------------------------------------------------------------
# Mode constants
# ---------------------------------------------------------------------------

MODE_MAIN          = "main"
MODE_SCHEMA        = "schema"        # edit field definitions (Format Record)
MODE_SCHEMA_EDIT   = "schema_edit"   # editing one field inline
MODE_CREATE        = "create"        # entering records into a freshly-created DB
MODE_ENTER         = "enter"         # entering a new record field-by-field
MODE_ENTER_CONFIRM = "enter_confirm" # "Definitions Complete Y/N?"
MODE_UPDATE        = "update"        # browsing existing records
MODE_UPDATE_DELETE = "update_delete" # "Are You Sure? Y/N"
MODE_UPDATE_EDIT   = "update_edit"   # editing a field of an existing record
MODE_SUBSET        = "subset"        # build subset: choose field number
MODE_SUBSET_FIELD  = "subset_field"  # entering low/high values
MODE_SAVE          = "save"
MODE_LOAD          = "load"
MODE_APPEND        = "append"
MODE_INDEX         = "index"         # inline directory listing
MODE_PRINT         = "print"         # print/merge prompt

# Schema sub-actions
SCHEMA_ACTION_RENAME = "rename"
SCHEMA_ACTION_MAXLEN = "maxlen"
SCHEMA_ACTION_INSERT = "insert"
SCHEMA_ACTION_DELETE = "delete"

# Index sub-modes
INDEX_DRIVE_1 = "drive1"
INDEX_DRIVE_2 = "drive2"


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

MM_CSS = """
MailMergeScreen {
    align: center middle;
    background: $background;
}

#mm-outer {
    width: 78;
    height: 30;
    border: solid $accent;
    background: $surface;
    layout: vertical;
}

#mm-message {
    height: 1;
    background: $primary;
    color: $text;
    padding: 0 1;
}

#mm-title {
    height: 1;
    text-align: center;
    text-style: bold;
    color: $accent;
    margin-top: 1;
}

#mm-status {
    height: 1;
    background: $secondary;
    color: $text;
    padding: 0 1;
}

#mm-body {
    height: 1fr;
    padding: 1 2;
    color: $text;
    overflow-y: auto;
}

#mm-help {
    height: 1;
    background: $primary-darken-2;
    color: $text-muted;
    padding: 0 1;
}

MailMergeHelpScreen {
    align: center middle;
}

#help-dialog {
    width: 72;
    height: auto;
    max-height: 90%;
    border: solid $primary;
    background: $surface;
    padding: 1 2;
}

#help-title {
    text-align: center;
    text-style: bold;
    color: $accent;
    margin-bottom: 1;
}

#help-content {
    color: $text;
}

#help-footer {
    text-align: center;
    color: $primary;
    margin-top: 1;
}
"""

HELP_CONTENT = """\
MAIL MERGE MENU
  C  Create File         Start a fresh database (clears current)
  E  Edit File           Browse and edit existing records
  B  Build Subset        Filter records by a field range
  A  Append File         Merge another file with the same schema
  P  Print File          Run the mail merge and print
  1  Index Drive 1       List files in the current folder
  2  Index Drive 2       List files in a second folder / drive
  L  Load File           Load a database file from disk
  S  Save File           Save the current database to disk
  F  Format Record       Change field names and field lengths (extra)
  R  Return              Go back to the Main Menu

EDIT FILE — RECORD NAVIGATION
  PgDn / N      Next record
  PgUp / P      Previous record
  E             Edit all fields of current record
  ↑ / ↓         Select individual field (then Enter to edit just that field)
  Ctrl+D        Delete current record (with confirmation)
  Esc           Return to Mail Merge menu

FORMAT RECORD
  Up / Down     Select a field
  R             Rename the selected field
  M             Change the field max length (1-20)
  I             Insert a new field after the current one
  D             Delete the selected field

ENTERING RECORDS
  Type text and press Enter to move to the next field.
  Empty fields are allowed.
  On the last field, Y saves the record; N returns to last field.
  Records are auto-saved to disk whenever you save the database.

BUILD SUBSET
  Choose the field number to filter.
  Enter Low Value, then High Value (alphabetic range).
  Subset stays active until you press Esc from the main menu.

USING MERGE FIELDS IN A DOCUMENT
  In the editor, insert the merge marker (@) followed by the field
  number, e.g. @1 for the first field, @3 for the third field.

OTHER
  F1 / ?        Show this help screen
  Esc           Return to the previous Mail Merge menu\
"""


# ---------------------------------------------------------------------------
# Help modal
# ---------------------------------------------------------------------------


class MailMergeHelpScreen(ModalScreen[None]):
    """Mail Merge command reference shown as a modal overlay."""

    def compose(self) -> ComposeResult:
        from textual.containers import Container
        with Container(id="help-dialog"):
            yield Static("=== MAIL MERGE HELP ===", id="help-title")
            yield Static(HELP_CONTENT, id="help-content")
            yield Static("Press any key to close", id="help-footer")

    def on_key(self, event: events.Key) -> None:
        self.dismiss(None)


# ---------------------------------------------------------------------------
# Main screen
# ---------------------------------------------------------------------------


class MailMergeScreen(Screen):
    """Mail Merge database module."""

    CSS = MM_CSS

    BINDINGS = []

    def __init__(self, app_state: AppState, initial_mode: str = MODE_MAIN) -> None:
        super().__init__()
        self._app_state = app_state
        self._initial_mode = initial_mode
        if app_state.mail_merge_db is None:
            app_state.mail_merge_db = MailMergeDB()
        self._db = app_state.mail_merge_db

        self._mode = MODE_MAIN
        self._input_buf = ""

        # Schema editing
        self._schema_field_idx = 0
        self._schema_action = ""
        self._from_create = False

        # Data entry (new record)
        self._entry_record: list[str] = []
        self._entry_field_idx = 0

        # Update (browse) mode
        self._update_record_idx = 0
        self._update_field_idx = 0       # which field is highlighted
        self._update_editing = False     # True when actually editing a field

        # Subset
        self._subset_field_idx = 0
        self._subset_low = ""
        self._subset_high = ""
        self._subset_entering = "field"
        self._active_subset: list[int] | None = None

        # Index
        self._index_entries: list[tuple[str, str, str]] = []  # (name, size, type)
        self._index_selected = 0
        self._index_directory = Path.cwd()
        self._index_purpose = ""  # "load" | "append" | "browse"

        # Misc
        self._message_text = ""
        self._status_text = ""
        self._body_text = ""
        self._help_text = ""
        self._enter_main()

    # ------------------------------------------------------------------
    # Compose / mount
    # ------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        from textual.containers import Container

        with Container(id="mm-outer"):
            yield Static(self._message_text, id="mm-message")
            yield Static("*** MAIL MERGE ***", id="mm-title")
            yield Static(self._status_text, id="mm-status")
            yield Static(self._body_text, id="mm-body")
            yield Static(self._help_text, id="mm-help")

    def on_mount(self) -> None:
        self._enter_main()
        if self._initial_mode == MODE_ENTER:
            self._enter_data_entry()
        elif self._initial_mode == MODE_UPDATE:
            self._enter_update()
        elif self._initial_mode == MODE_SCHEMA:
            self._enter_schema()
        elif self._initial_mode == MODE_SUBSET:
            self._enter_subset()

    # ------------------------------------------------------------------
    # Mode entry helpers
    # ------------------------------------------------------------------

    def _enter_main(self, preserve_message: bool = False) -> None:
        self._mode = MODE_MAIN
        self._refresh_status()
        subset_note = ""
        if self._active_subset is not None:
            subset_note = f"  [bold yellow]SUBSET ACTIVE: {len(self._active_subset)} records[/]"
        filename_note = f"  [dim]File: {self._db.filename or '(unsaved)'}[/]"
        self._set_body(
            f"{filename_note}{subset_note}\n\n"
            "[bold]C[/]  Create File\n"
            "[bold]N[/]  New Record\n"
            "[bold]E[/]  Edit File\n"
            "[bold]B[/]  Build Subset\n"
            "[bold]A[/]  Append File\n"
            "[bold]P[/]  Print File\n"
            "\n"
            "[bold]1[/]  Index Drive 1\n"
            "[bold]2[/]  Index Drive 2\n"
            "[bold]L[/]  Load File\n"
            "[bold]S[/]  Save File\n"
            "\n"
            "[bold]R[/]  Return to Safari Writer\n"
            "\n"
            "[dim]F  Format Record (extra)    F1/?  Help[/]"
        )
        if not preserve_message:
            self._set_message("SELECT ITEM")
        self._set_help(" C Create  N New  E Edit  B Subset  A Append  P Print  1/2 Index  L Load  S Save  R Return")

    def _enter_schema(self) -> None:
        self._mode = MODE_SCHEMA
        self._schema_field_idx = min(self._schema_field_idx, max(0, len(self._db.fields) - 1))
        self._render_schema()
        self._set_message("Format Record: Up/Down select  R Rename  M Max-len  I Insert  D Delete  Esc done")
        self._set_help(" ↑↓ Select  R Rename  M MaxLen  I Insert  D Delete  Esc Back")

    def _enter_data_entry(self) -> None:
        self._mode = MODE_ENTER
        if self._db.records_free <= 0:
            self._set_message("Database full — max 255 records reached.")
            self._enter_main()
            return
        self._entry_record = self._db.new_record()
        self._entry_field_idx = 0
        self._input_buf = ""
        self._render_entry_form()
        self._set_message(f"Field 1/{len(self._db.fields)}: {self._db.fields[0].name} — type value, Enter to advance")
        self._set_help(" Enter  Next field    Esc  Abort")

    def _enter_update(self) -> None:
        self._mode = MODE_UPDATE
        if not self._db.records:
            self._set_message("No records yet — use C to create and enter records first.")
            self._enter_main()
            return
        # Clamp index
        self._update_record_idx = min(self._update_record_idx, len(self._db.records) - 1)
        self._update_field_idx = 0
        self._update_editing = False
        self._render_update_record()

    def _enter_subset(self) -> None:
        self._mode = MODE_SUBSET
        self._subset_low = ""
        self._subset_high = ""
        self._subset_field_idx = 0
        self._subset_entering = "field"
        self._input_buf = ""
        self._render_subset()
        self._set_message("Build Subset: enter field number (1–{}) to filter on".format(len(self._db.fields)))
        self._set_help(" Enter Confirm  Esc Cancel")

    def _enter_index(self, directory: Path, purpose: str) -> None:
        """Show an inline directory listing. purpose = 'load' | 'append' | 'browse'."""
        self._mode = MODE_INDEX
        self._index_directory = directory
        self._index_purpose = purpose
        self._index_selected = 0
        self._scan_index()
        self._render_index()

    def _enter_print(self) -> None:
        self._mode = MODE_PRINT
        count = len(self._active_subset) if self._active_subset is not None else len(self._db.records)
        self._input_buf = ""
        body = (
            "[bold]Print File / Mail Merge[/]\n\n"
            f"  Records to merge: {count}\n"
            f"  Database: {self._db.filename or '(unsaved)'}\n\n"
            "  This will print one copy of the current document\n"
            "  for each record, substituting @N merge fields.\n\n"
            "  Press Y to begin, N or Esc to cancel.\n"
        )
        self._set_body(body)
        self._set_message(f"Print {count} merged document(s)?  Y / N")
        self._set_help(" Y Begin print  N/Esc Cancel")

    # ------------------------------------------------------------------
    # Key dispatcher
    # ------------------------------------------------------------------

    def on_key(self, event: events.Key) -> None:
        if event.key == "f1" or event.character == "?":
            self.action_show_help()
            event.stop()
            return
        # Normalize key to lowercase for consistent matching
        key = event.key.lower()
        {
            MODE_MAIN:          self._key_main,
            MODE_SCHEMA:        self._key_schema,
            MODE_SCHEMA_EDIT:   self._key_schema_edit,
            MODE_CREATE:        self._key_data_entry,   # same handler as ENTER
            MODE_ENTER:         self._key_data_entry,
            MODE_ENTER_CONFIRM: self._key_data_entry_confirm,
            MODE_UPDATE:        self._key_update,
            MODE_UPDATE_DELETE: self._key_update_delete,
            MODE_UPDATE_EDIT:   self._key_update_edit,
            MODE_SUBSET:        self._key_subset,
            MODE_SUBSET_FIELD:  self._key_subset_field,
            MODE_SAVE:          self._key_filename,
            MODE_LOAD:          self._key_filename,
            MODE_APPEND:        self._key_filename,
            MODE_INDEX:         self._key_index,
            MODE_PRINT:         self._key_print,
        }.get(self._mode, lambda k, e: None)(key, event)
        event.stop()

    # ------------------------------------------------------------------
    # Main menu
    # ------------------------------------------------------------------

    def _key_main(self, key: str, event) -> None:
        if getattr(self, "_print_preview_shown", False):
            self._print_preview_shown = False
            self._enter_main()
            return

        k = key.lower()
        if k == "c":
            self._do_create_file()
        elif k == "n":
            self._enter_data_entry()
        elif k == "e":
            self._enter_update()
        elif k == "b":
            self._enter_subset()
        elif k == "a":
            self._mode = MODE_APPEND
            self._input_buf = ""
            self._set_body("Append database file:\n\n> ")
            self._set_message("Enter filename to append, or press 1/2 to browse, Esc to cancel")
            self._set_help(" Enter Append  Esc Cancel")
        elif k == "p":
            self._enter_print()
        elif key == "1":
            self._enter_index(Path.cwd(), "browse")
        elif key == "2":
            self._enter_index_drive2()
        elif k == "l":
            self._mode = MODE_LOAD
            self._input_buf = ""
            self._set_body("Load database from file:\n\n> ")
            self._set_message("Enter filename to load, or press 1 to browse, Esc to cancel")
            self._set_help(" Enter Load  1 Browse  Esc Cancel")
        elif k == "s":
            self._mode = MODE_SAVE
            self._input_buf = self._db.filename
            self._set_body(f"Save database to file:\n\n> {self._input_buf}")
            self._set_message("Enter filename, Enter to confirm")
            self._set_help(" Enter Save  Esc Cancel")
        elif k == "f":
            self._enter_schema()
        elif k == "r" or key == "escape":
            self.action_exit_module()

    def _do_create_file(self) -> None:
        """C — Create File: reset DB to defaults and go straight into schema edit."""
        self._db = MailMergeDB()
        self._app_state.mail_merge_db = self._db
        self._active_subset = None
        self._update_record_idx = 0
        self._refresh_status()
        self._from_create = True
        # Enter schema first so user can adjust field definitions
        self._schema_field_idx = 0
        self._mode = MODE_SCHEMA
        self._render_schema()
        self._set_message("New file — review/edit field layout, then Esc to start entering records")
        self._set_help(" ↑↓ Select  R Rename  M MaxLen  I Insert  D Delete  Esc → Enter Records")

    def _enter_index_drive2(self) -> None:
        """Index Drive 2 — try to find a second drive/volume."""
        import platform
        system = platform.system()
        drives: list[Path] = []
        if system == "Windows":
            import ctypes
            bitmask = ctypes.windll.kernel32.GetLogicalDrives()  # type: ignore[attr-defined]
            for i in range(26):
                if bitmask & (1 << i):
                    letter = chr(65 + i)
                    drive_path = f"{letter}:\\"
                    drive_type = ctypes.windll.kernel32.GetDriveTypeW(drive_path)  # type: ignore[attr-defined]
                    if drive_type in (2, 3) and Path(drive_path) != Path.cwd().anchor:
                        drives.append(Path(drive_path))
        elif system == "Darwin":
            volumes = Path("/Volumes")
            if volumes.exists():
                drives = [v for v in sorted(volumes.iterdir()) if v.is_dir()]
        else:
            for base in (Path("/media"), Path("/mnt")):
                if base.exists():
                    drives += [d for d in sorted(base.iterdir()) if d.is_dir()]

        if drives:
            self._enter_index(drives[0], "browse")
        else:
            self._enter_index(Path.home(), "browse")

    # ------------------------------------------------------------------
    # Schema editing
    # ------------------------------------------------------------------

    def _key_schema(self, key: str, event) -> None:
        fields = self._db.fields
        if key == "up":
            self._schema_field_idx = max(0, self._schema_field_idx - 1)
            self._render_schema()
        elif key == "down":
            self._schema_field_idx = min(len(fields) - 1, self._schema_field_idx + 1)
            self._render_schema()
        elif key.lower() == "r":
            self._schema_action = SCHEMA_ACTION_RENAME
            self._input_buf = fields[self._schema_field_idx].name
            self._mode = MODE_SCHEMA_EDIT
            self._set_message(f"Rename field: {self._input_buf}")
            self._set_help(" Enter Confirm  Esc Cancel")
        elif key.lower() == "m":
            self._schema_action = SCHEMA_ACTION_MAXLEN
            self._input_buf = str(fields[self._schema_field_idx].max_len)
            self._mode = MODE_SCHEMA_EDIT
            self._set_message(f"Max length (1–{MAX_FIELD_DATA_LEN}): {self._input_buf}")
            self._set_help(" Enter Confirm  Esc Cancel")
        elif key.lower() == "i":
            if len(fields) >= MAX_FIELDS:
                self._set_message(f"Cannot insert — maximum {MAX_FIELDS} fields already defined.")
                return
            self._schema_action = SCHEMA_ACTION_INSERT
            self._input_buf = ""
            self._mode = MODE_SCHEMA_EDIT
            self._set_message("New field name (max 12 chars): ")
            self._set_help(" Enter Confirm  Esc Cancel")
        elif key.lower() == "d":
            if len(fields) <= 1:
                self._set_message("Cannot delete the last field.")
                return
            self._schema_action = SCHEMA_ACTION_DELETE
            self._mode = MODE_SCHEMA_EDIT
            fname = fields[self._schema_field_idx].name
            self._set_message(f"Delete field '{fname}'? Y/N")
            self._set_help(" Y Confirm  N Cancel")
        elif key == "escape":
            # If we came from Create, go to data entry next
            if hasattr(self, '_from_create') and self._from_create:
                self._from_create = False
                self._enter_data_entry()
            else:
                self._enter_main()

    def _key_schema_edit(self, key: str, event) -> None:
        action = self._schema_action
        idx = self._schema_field_idx

        if action == SCHEMA_ACTION_DELETE:
            if key.lower() == "y":
                for rec in self._db.records:
                    if idx < len(rec):
                        rec.pop(idx)
                self._db.fields.pop(idx)
                self._schema_field_idx = min(idx, len(self._db.fields) - 1)
                self._mode = MODE_SCHEMA
                self._render_schema()
                self._set_message("Field deleted.")
            else:
                self._mode = MODE_SCHEMA
                self._render_schema()
                self._set_message("Cancelled.")
            return

        if key == "escape":
            self._mode = MODE_SCHEMA
            self._render_schema()
            self._set_message("Cancelled.")
            return

        if key == "enter":
            val = self._input_buf.strip()
            if action == SCHEMA_ACTION_RENAME:
                if not val:
                    self._set_message("Name cannot be empty.")
                    return
                self._db.fields[idx].name = val[:MAX_FIELD_NAME_LEN]
            elif action == SCHEMA_ACTION_MAXLEN:
                if not val.isdigit() or not (1 <= int(val) <= MAX_FIELD_DATA_LEN):
                    self._set_message(f"Enter a number 1–{MAX_FIELD_DATA_LEN}.")
                    return
                new_len = int(val)
                self._db.fields[idx].max_len = new_len
                for rec in self._db.records:
                    if idx < len(rec):
                        rec[idx] = rec[idx][:new_len]
            elif action == SCHEMA_ACTION_INSERT:
                if not val:
                    self._set_message("Name cannot be empty.")
                    return
                new_field = FieldDef(val[:MAX_FIELD_NAME_LEN])
                insert_pos = idx + 1
                self._db.fields.insert(insert_pos, new_field)
                for rec in self._db.records:
                    rec.insert(insert_pos, "")
                self._schema_field_idx = insert_pos
            self._mode = MODE_SCHEMA
            self._render_schema()
            self._set_message("Done.")
            return

        if key == "backspace":
            self._input_buf = self._input_buf[:-1]
        elif event.character and event.character.isprintable():
            max_len = MAX_FIELD_NAME_LEN if action in (SCHEMA_ACTION_RENAME, SCHEMA_ACTION_INSERT) else 3
            if len(self._input_buf) < max_len:
                self._input_buf += event.character
        label = {
            SCHEMA_ACTION_RENAME: "Rename",
            SCHEMA_ACTION_MAXLEN: "Max len",
            SCHEMA_ACTION_INSERT: "Insert name",
        }.get(action, action)
        self._set_message(f"{label}: {self._input_buf}")

    def _render_schema(self) -> None:
        lines = ["[bold]Format Record (Schema)[/]\n", f"{'#':<4}{'Field Name':<14}{'Max Len':>8}\n"]
        for i, f in enumerate(self._db.fields):
            if i == self._schema_field_idx:
                lines.append(f"[reverse]{i + 1:<4}{f.name:<14}{f.max_len:>8}[/reverse]")
            else:
                lines.append(f"{i + 1:<4}{f.name:<14}{f.max_len:>8}")
        lines.append(f"\n[dim]{len(self._db.fields)}/{MAX_FIELDS} fields defined[/]")
        self._set_body("\n".join(lines))

    # ------------------------------------------------------------------
    # Data entry (new record)
    # ------------------------------------------------------------------

    def _key_data_entry(self, key: str, event) -> None:
        fi = self._entry_field_idx
        fdef = self._db.fields[fi]

        if key == "escape":
            self._set_message("Entry aborted.")
            self._enter_main()
            return

        # Early save
        if key in ("f10", "ctrl+s"):
            self._entry_record[fi] = self._input_buf
            self._mode = MODE_ENTER_CONFIRM
            self._set_message("Definitions complete? Y/N")
            self._set_help(" Y Save record  N Continue editing")
            return

        if key == "enter":
            self._entry_record[fi] = self._input_buf
            next_fi = fi + 1
            if next_fi >= len(self._db.fields):
                self._mode = MODE_ENTER_CONFIRM
                self._set_message("Definitions complete? Y/N")
                self._set_help(" Y Save record  N Continue editing")
            else:
                self._entry_field_idx = next_fi
                self._input_buf = self._entry_record[next_fi]
                self._render_entry_form()
                nf = self._db.fields[next_fi]
                self._set_message(f"Field {next_fi + 1}/{len(self._db.fields)}: {nf.name}")
        elif key == "backspace":
            self._input_buf = self._input_buf[:-1]
            self._render_entry_form()
        elif event.character and event.character.isprintable():
            if len(self._input_buf) < fdef.max_len:
                self._input_buf += event.character
                self._render_entry_form()

    def _key_data_entry_confirm(self, key: str, event) -> None:
        k = key.lower()
        if k == "y":
            if self._db.records_free <= 0:
                self._set_message("Database full.")
                self._enter_main()
                return
            if self._entry_record:
                self._db.records.append(list(self._entry_record))
                self._refresh_status()
                self._autosave()
                rec_num = len(self._db.records)
                self._set_message(f"Record {rec_num} saved. Enter another? Y/N")
                # Clear current entry to signify we are waiting for a loop choice
                self._entry_record = []
            else:
                # This is the second Y in the loop logic (after "Enter another?")
                self._enter_data_entry()
        elif k == "n":
            if self._entry_record: # If they were confirming a record, N goes back to editing it
                 last = len(self._db.fields) - 1
                 self._entry_field_idx = last
                 self._input_buf = self._entry_record[last]
                 self._mode = MODE_ENTER
                 self._render_entry_form()
                 self._set_message(f"Field {last + 1}/{len(self._db.fields)}: {self._db.fields[last].name}")
            else: # If they just saved and N means "don't enter another"
                 self._enter_main(preserve_message=True)

    def _render_entry_form(self) -> None:
        lines = [f"[bold]Enter Record {len(self._db.records) + 1}[/]\n"]
        for i, fdef in enumerate(self._db.fields):
            if i == self._entry_field_idx:
                val_display = f"[reverse]{self._input_buf}{'█'}[/reverse]"
            else:
                val_display = self._entry_record[i] or "[dim](empty)[/dim]"
            name = fdef.name.ljust(MAX_FIELD_NAME_LEN)
            lines.append(f"  {i + 1:>2}. {name}  {val_display}")
        self._set_body("\n".join(lines))

    # ------------------------------------------------------------------
    # Update / browse records
    # ------------------------------------------------------------------

    def _key_update(self, key: str, event) -> None:
        records = self._db.records
        if not records:
            self._enter_main()
            return

        total = len(records)
        idx = self._update_record_idx

        if key in ("pagedown", "n"):
            if idx < total - 1:
                self._update_record_idx += 1
                self._update_field_idx = 0
                self._render_update_record()
            else:
                self._set_message(f"Already on last record ({total} of {total}).  PgUp/P=previous  E=edit  Ctrl+D=delete  Esc=back")
        elif key in ("pageup", "p"):
            if idx > 0:
                self._update_record_idx -= 1
                self._update_field_idx = 0
                self._render_update_record()
            else:
                self._set_message("Already on first record.  PgDn/N=next  E=edit  Ctrl+D=delete  Esc=back")
        elif key == "up":
            self._update_field_idx = max(0, self._update_field_idx - 1)
            self._render_update_record()
        elif key == "down":
            self._update_field_idx = min(len(self._db.fields) - 1, self._update_field_idx + 1)
            self._render_update_record()
        elif key == "enter":
            # Edit just the highlighted field
            rec = records[self._update_record_idx]
            fi = self._update_field_idx
            self._mode = MODE_UPDATE_EDIT
            self._update_editing = True
            self._input_buf = rec[fi] if fi < len(rec) else ""
            self._render_update_edit()
            self._set_message(f"Edit field {fi + 1}: {self._db.fields[fi].name}  — Enter save, Esc cancel")
            self._set_help(" Enter Save field  Esc Cancel")
        elif key.lower() == "e":
            # Edit ALL fields sequentially starting from field 0
            self._mode = MODE_UPDATE_EDIT
            self._update_field_idx = 0
            self._update_editing = True
            rec = records[self._update_record_idx]
            self._input_buf = rec[0] if rec else ""
            self._render_update_edit()
            self._set_message(f"Edit field 1: {self._db.fields[0].name}  — Enter advance, Esc done")
            self._set_help(" Enter Next field  Esc Done")
        elif key == "ctrl+d":
            self._mode = MODE_UPDATE_DELETE
            self._set_message(f"Delete record {idx + 1}? Are you sure? Y/N")
            self._set_help(" Y Delete  N/Esc Cancel")
        elif key.lower() == "c":
            # Allow entering a new record from update mode
            self._enter_data_entry()
        elif key == "escape":
            self._enter_main()

    def _key_update_delete(self, key: str, event) -> None:
        k = key.lower()
        if k == "y":
            idx = self._update_record_idx
            self._db.records.pop(idx)
            self._refresh_status()
            self._autosave()
            if not self._db.records:
                self._set_message("All records deleted.")
                self._enter_main()
                return
            self._update_record_idx = min(idx, len(self._db.records) - 1)
            self._update_field_idx = 0
            self._mode = MODE_UPDATE
            self._render_update_record()
            self._set_message("Record deleted.")
        elif k == "n" or key == "escape":
            self._mode = MODE_UPDATE
            self._render_update_record()
            self._set_message("Deletion cancelled.")

    def _key_update_edit(self, key: str, event) -> None:
        rec = self._db.records[self._update_record_idx]
        fi = self._update_field_idx
        fdef = self._db.fields[fi]

        if key == "escape":
            self._mode = MODE_UPDATE
            self._update_editing = False
            self._render_update_record()
            self._set_message("Edit cancelled.")
            return

        if key == "enter":
            rec[fi] = self._input_buf
            next_fi = fi + 1
            if next_fi >= len(self._db.fields):
                self._mode = MODE_UPDATE
                self._update_editing = False
                self._autosave()
                self._render_update_record()
                self._set_message("Record updated and saved.")
            else:
                self._update_field_idx = next_fi
                self._input_buf = rec[next_fi] if next_fi < len(rec) else ""
                self._render_update_edit()
                self._set_message(f"Edit field {next_fi + 1}: {self._db.fields[next_fi].name}")
        elif key == "backspace":
            self._input_buf = self._input_buf[:-1]
            self._render_update_edit()
        elif event.character and event.character.isprintable():
            if len(self._input_buf) < fdef.max_len:
                self._input_buf += event.character
                self._render_update_edit()

    def _render_update_record(self) -> None:
        records = self._db.records
        idx = self._update_record_idx
        rec = records[idx]
        total = len(records)

        # Navigation hint at the top
        prev_hint = "[dim]PgUp/P=prev[/]" if idx > 0 else "[dim](first)[/]"
        next_hint = "[dim]PgDn/N=next[/]" if idx < total - 1 else "[dim](last)[/]"
        header = (
            f"[bold]Record {idx + 1} of {total}[/]   "
            f"{prev_hint}  ◄  [bold]#{idx + 1}[/]  ►  {next_hint}\n"
        )

        lines = [header]
        for i, fdef in enumerate(self._db.fields):
            val = rec[i] if i < len(rec) else ""
            name = fdef.name.ljust(MAX_FIELD_NAME_LEN)
            if i == self._update_field_idx:
                val_display = f"[reverse] {val or '(empty)'} [/reverse]"
            else:
                val_display = val or "[dim](empty)[/dim]"
            lines.append(f"  {i + 1:>2}. {name}  {val_display}")

        lines.append("\n[dim]↑↓=select field  Enter=edit field  E=edit all  C=new record  Ctrl+D=delete  Esc=back[/]")
        self._set_body("\n".join(lines))
        self._set_message(
            f"Record {idx + 1}/{total}  "
            + ("PgDn/N next  " if idx < total - 1 else "")
            + ("PgUp/P prev  " if idx > 0 else "")
            + "E=edit  Ctrl+D=delete  Esc=back"
        )
        self._set_help(
            f" {'PgDn/N Next' if idx < total-1 else '(last record)'}  "
            f"{'  PgUp/P Prev' if idx > 0 else '  (first record)'}  "
            f"  ↑↓ Field  Enter Edit  E Edit-all  C New  Ctrl+D Delete  Esc Back"
        )

    def _render_update_edit(self) -> None:
        rec = self._db.records[self._update_record_idx]
        idx = self._update_record_idx
        total = len(self._db.records)
        lines = [f"[bold]Edit Record {idx + 1} of {total}[/]\n"]
        for i, fdef in enumerate(self._db.fields):
            if i == self._update_field_idx:
                val_display = f"[reverse]{self._input_buf}█[/reverse]"
            else:
                val = rec[i] if i < len(rec) else ""
                val_display = val or "[dim](empty)[/dim]"
            name = fdef.name.ljust(MAX_FIELD_NAME_LEN)
            lines.append(f"  {i + 1:>2}. {name}  {val_display}")
        self._set_body("\n".join(lines))

    # ------------------------------------------------------------------
    # Build Subset
    # ------------------------------------------------------------------

    def _key_subset(self, key: str, event) -> None:
        if key == "escape":
            self._active_subset = None
            self._set_message("Subset cleared.")
            self._enter_main()
            return
        if key == "enter":
            val = self._input_buf.strip()
            if not val.isdigit() or not (1 <= int(val) <= len(self._db.fields)):
                self._set_message(f"Enter field number 1–{len(self._db.fields)}.")
                return
            self._subset_field_idx = int(val) - 1
            self._input_buf = ""
            self._mode = MODE_SUBSET_FIELD
            self._subset_entering = "low"
            self._render_subset()
            self._set_message(f"Field: {self._db.fields[self._subset_field_idx].name} — enter Low Value")
        elif key == "backspace":
            self._input_buf = self._input_buf[:-1]
            self._render_subset()
        elif event.character and event.character.isprintable():
            if len(self._input_buf) < 3:
                self._input_buf += event.character
                self._render_subset()

    def _key_subset_field(self, key: str, event) -> None:
        if key == "escape":
            self._enter_subset()
            return
        if key == "enter":
            if self._subset_entering == "low":
                self._subset_low = self._input_buf
                self._input_buf = ""
                self._subset_entering = "high"
                self._render_subset()
                fname = self._db.fields[self._subset_field_idx].name
                self._set_message(f"Field: {fname}  Low='{self._subset_low}' — enter High Value")
            elif self._subset_entering == "high":
                self._subset_high = self._input_buf
                results = self._db.apply_subset(
                    self._subset_field_idx, self._subset_low, self._subset_high
                )
                self._active_subset = results
                self._render_subset_results(results)
                self._set_message(f"Subset active: {len(results)} record(s) match. Esc to return to menu.")
                self._mode = MODE_MAIN
                self._enter_main()
                return
        elif key == "backspace":
            self._input_buf = self._input_buf[:-1]
            self._render_subset()
        elif event.character and event.character.isprintable():
            if len(self._input_buf) < MAX_FIELD_DATA_LEN:
                self._input_buf += event.character
                self._render_subset()

    def _render_subset(self) -> None:
        fname = (
            self._db.fields[self._subset_field_idx].name
            if self._mode == MODE_SUBSET_FIELD else "—"
        )
        lines = [
            "[bold]Build Subset (Filter)[/]\n",
            f"{'#':<4}{'Field Name':<16}{'Low Value':<22}{'High Value':<22}\n",
        ]
        for i, f in enumerate(self._db.fields):
            low = self._subset_low if (i == self._subset_field_idx and self._mode == MODE_SUBSET_FIELD) else ""
            high = self._subset_high if (i == self._subset_field_idx and self._mode == MODE_SUBSET_FIELD) else ""
            lines.append(f"  {i + 1:<4}{f.name:<16}{low:<22}{high:<22}")
        lines.append(f"\n[dim]Filter field:[/] {fname}")
        if self._mode == MODE_SUBSET:
            lines.append(f"\nField number: [reverse]{self._input_buf}[/reverse]")
        elif self._subset_entering == "low":
            lines.append(f"\nLow value: [reverse]{self._input_buf}[/reverse]")
        elif self._subset_entering == "high":
            lines.append(f"\nHigh value: [reverse]{self._input_buf}[/reverse]")
        self._set_body("\n".join(lines))

    def _render_subset_results(self, results: list[int]) -> None:
        lines = [f"[bold]Subset Results: {len(results)} record(s)[/]\n"]
        for ri in results[:20]:
            rec = self._db.records[ri]
            preview = " | ".join(v for v in rec[:3] if v)
            lines.append(f"  Record {ri + 1}: {preview}")
        if len(results) > 20:
            lines.append(f"  … and {len(results) - 20} more")
        self._set_body("\n".join(lines))

    # ------------------------------------------------------------------
    # Index (inline directory listing)
    # ------------------------------------------------------------------

    def _scan_index(self) -> None:
        self._index_entries = []
        try:
            items = sorted(
                self._index_directory.iterdir(),
                key=lambda p: (not p.is_dir(), p.name.lower()),
            )
        except OSError:
            self._index_entries = [("<error reading directory>", "", "")]
            return
        for item in items:
            try:
                name = item.name
                if item.is_dir():
                    self._index_entries.append((name, "---", "<DIR>"))
                else:
                    size = item.stat().st_size
                    sz = f"{size:,}"
                    suffix = item.suffix.upper()
                    self._index_entries.append((name, sz, suffix or "FILE"))
            except OSError:
                self._index_entries.append((item.name, "???", "???"))
        if not self._index_entries:
            self._index_entries = [("<empty>", "", "")]

    def _render_index(self) -> None:
        try:
            free = shutil.disk_usage(self._index_directory).free
            free_str = f"{free:,} bytes free"
        except OSError:
            free_str = "? bytes free"

        purpose_labels = {
            "load":   "Select file to LOAD (Enter=load, Esc=cancel)",
            "append": "Select file to APPEND (Enter=append, Esc=cancel)",
            "browse": "INDEX  (Enter=load, Esc=back)",
        }
        header = (
            f"[bold]INDEX: {self._index_directory}[/]\n"
            f"[dim]{free_str}[/]\n"
            f"{'NAME':<32} {'SIZE':>14}  {'TYPE'}\n"
        )
        lines = [header]
        for i, (name, size, ftype) in enumerate(self._index_entries):
            display = name[:30]
            line = f"  {display:<32} {size:>14}  {ftype}"
            if i == self._index_selected:
                line = f"[reverse]{line}[/reverse]"
            lines.append(line)

        self._set_body("\n".join(lines))
        self._set_message(purpose_labels.get(self._index_purpose, "Index"))
        self._set_help(" ↑↓ Select  Enter Load  Esc Back")

    def _key_index(self, key: str, event) -> None:
        entries = self._index_entries
        if key == "escape":
            self._enter_main()
            return
        if key == "up":
            if self._index_selected > 0:
                self._index_selected -= 1
                self._render_index()
        elif key == "down":
            if self._index_selected < len(entries) - 1:
                self._index_selected += 1
                self._render_index()
        elif key == "pageup":
            self._index_selected = max(0, self._index_selected - 10)
            self._render_index()
        elif key == "pagedown":
            self._index_selected = min(len(entries) - 1, self._index_selected + 10)
            self._render_index()
        elif key == "enter":
            if not entries or entries[0][0].startswith("<"):
                return
            name = entries[self._index_selected][0]
            full_path = self._index_directory / name
            if full_path.is_dir():
                self._index_directory = full_path
                self._index_selected = 0
                self._scan_index()
                self._render_index()
            else:
                filename = str(full_path)
                purpose = self._index_purpose
                if purpose == "load":
                    self._load_db(filename)
                elif purpose == "append":
                    self._append_db(filename)
                else:
                    self._load_db(filename)

    # ------------------------------------------------------------------
    # File operations
    # ------------------------------------------------------------------

    def _key_filename(self, key: str, event) -> None:
        mode = self._mode
        if key == "escape":
            self._enter_main()
            return
        if key == "1" and mode in (MODE_LOAD, MODE_APPEND):
            # Browse for file
            purpose = "load" if mode == MODE_LOAD else "append"
            self._enter_index(Path.cwd(), purpose)
            return
        if key == "enter":
            filename = self._input_buf.strip()
            if not filename:
                self._enter_main()
                return
            if mode == MODE_SAVE:
                self._save_db(filename)
            elif mode == MODE_LOAD:
                self._load_db(filename)
            elif mode == MODE_APPEND:
                self._append_db(filename)
        elif key == "backspace":
            self._input_buf = self._input_buf[:-1]
            self._update_filename_prompt()
        elif event.character and event.character.isprintable():
            self._input_buf += event.character
            self._update_filename_prompt()

    def _update_filename_prompt(self) -> None:
        labels = {MODE_SAVE: "Save to", MODE_LOAD: "Load from", MODE_APPEND: "Append from"}
        label = labels.get(self._mode, "File")
        self._set_body(f"{label} file:\n\n> {self._input_buf}")

    def _save_db(self, filename: str) -> None:
        try:
            save_mail_merge_db(self._db, Path(filename))
            self._db.filename = filename
            self._set_message(f"Saved {len(self._db.records)} records to '{filename}'.")
        except OSError as e:
            self._set_message(f"Save error: {e}")
        self._enter_main()

    def _load_db(self, filename: str) -> None:
        try:
            self._db = load_mail_merge_db(Path(filename))
            self._db.filename = filename
            self._app_state.mail_merge_db = self._db
            self._refresh_status()
            self._active_subset = None
            self._update_record_idx = 0
            self._set_message(f"Loaded {len(self._db.records)} records from '{filename}'.")
        except (OSError, ValueError) as e:
            self._set_message(f"Load error: {e}")
        self._enter_main()

    def _append_db(self, filename: str) -> None:
        try:
            other = load_mail_merge_db(Path(filename))
            if not self._db.schema_matches(other):
                self._set_message("Cannot append — schemas do not match (field count or lengths differ).")
                self._enter_main()
                return
            space = self._db.records_free
            to_add = other.records[:space]
            self._db.records.extend(to_add)
            self._refresh_status()
            self._autosave()
            self._set_message(f"Appended {len(to_add)} records (of {len(other.records)}).")
        except (OSError, ValueError) as e:
            self._set_message(f"Append error: {e}")
        self._enter_main()

    # ------------------------------------------------------------------
    # Print / Mail Merge
    # ------------------------------------------------------------------

    def _key_print(self, key: str, event) -> None:
        k = key.lower()
        if k == "y":
            self._do_print_merge()
        elif k == "n" or key == "escape":
            self._enter_main()

    def _do_print_merge(self) -> None:
        """Execute the mail merge: substitute @N fields and display result."""
        records = self._db.records
        if self._active_subset is not None:
            records = [records[i] for i in self._active_subset if i < len(records)]

        if not records:
            self._set_message("No records to merge. Load a database or clear the subset.")
            self._enter_main()
            return

        buf = self._app_state.buffer
        results: list[str] = []
        for rec in records:
            merged_buf = self._merge_record(buf, rec)
            results.append("\n".join(merged_buf))

        # Show a summary / preview in the body
        count = len(results)
        preview_lines = results[0].splitlines()[:8] if results else []
        preview = "\n".join(f"  {ln}" for ln in preview_lines)
        if len(results[0].splitlines()) > 8:
            preview += "\n  …"

        body = (
            f"[bold]Mail Merge Complete — {count} document(s)[/]\n\n"
            f"[dim]Preview of record 1:[/]\n"
            f"{preview}\n\n"
            f"[dim](Full print output would go to printer — not yet wired to print driver)[/]\n\n"
            "Press any key to return to menu."
        )
        self._set_body(body)
        self._set_message(f"Merged {count} records. Press any key.")
        self._set_help(" Any key  Return to menu")
        self._mode = MODE_MAIN  # next key press falls through to main handler then re-renders

        # Set a one-shot: next key returns to main
        self._print_preview_shown = True

    def _merge_record(self, buf: list[str], rec: list[str]) -> list[str]:
        out: list[str] = []
        for line in buf:
            result: list[str] = []
            i = 0
            while i < len(line):
                ch = line[i]
                if ch == "\x11":  # merge marker
                    i += 1
                    digits: list[str] = []
                    while i < len(line) and line[i].isdigit():
                        digits.append(line[i])
                        i += 1
                    if digits:
                        fn = int("".join(digits))
                        if 1 <= fn <= len(rec):
                            result.append(rec[fn - 1])
                        else:
                            result.append(f"@{fn}")
                    continue
                result.append(ch)
                i += 1
            out.append("".join(result))
        return out

    # ------------------------------------------------------------------
    # Auto-save helper
    # ------------------------------------------------------------------

    def _autosave(self) -> None:
        """Save to disk automatically if a filename is already set."""
        if self._db.filename:
            try:
                save_mail_merge_db(self._db, Path(self._db.filename))
            except OSError:
                pass  # silently fail; user can manually save

    # ------------------------------------------------------------------
    # Status / helpers
    # ------------------------------------------------------------------

    def _refresh_status(self) -> None:
        try:
            bytes_free = shutil.disk_usage(os.getcwd()).free
        except OSError:
            bytes_free = 0
        records_free = self._db.records_free
        self._status_text = f" {bytes_free:,} BYTES FREE   {records_free} RECORDS FREE"
        if self.is_mounted:
            self.query_one("#mm-status", Static).update(self._status_text)

    def _set_message(self, msg: str) -> None:
        self._message_text = f" {msg}"
        if self.is_mounted:
            self.query_one("#mm-message", Static).update(self._message_text)

    def _set_body(self, content: str) -> None:
        self._body_text = content
        if self.is_mounted:
            self.query_one("#mm-body", Static).update(self._body_text)

    def _set_help(self, text: str) -> None:
        self._help_text = text if "F1" in text else f"{text}  F1/? Help"
        if self.is_mounted:
            self.query_one("#mm-help", Static).update(self._help_text)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_show_help(self) -> None:
        self.app.push_screen(MailMergeHelpScreen())  # type: ignore[attr-defined]

    def action_exit_module(self) -> None:
        if self._mode != MODE_MAIN:
            self._enter_main()
        else:
            self.app.pop_screen()  # type: ignore[attr-defined]
