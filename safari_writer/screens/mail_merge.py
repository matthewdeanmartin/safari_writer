"""Mail Merge screen — flat-file database for form letters."""

from __future__ import annotations

from pathlib import Path
from textual.app import ComposeResult
from textual.binding import Binding
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

MODE_MAIN         = "main"          # top-level menu
MODE_SCHEMA       = "schema"        # edit field definitions
MODE_SCHEMA_EDIT  = "schema_edit"   # editing one field inline
MODE_ENTER        = "enter"         # entering data into a new record
MODE_ENTER_CONFIRM= "enter_confirm" # "Definitions Complete Y/N?"
MODE_UPDATE       = "update"        # browsing existing records
MODE_UPDATE_DELETE= "update_delete" # "Are You Sure? Y/N"
MODE_UPDATE_EDIT  = "update_edit"   # editing a field of an existing record
MODE_SUBSET       = "subset"        # build subset / filter
MODE_SUBSET_FIELD = "subset_field"  # entering low/high for a specific field
MODE_SAVE         = "save"          # prompt for filename to save
MODE_LOAD         = "load"          # prompt for filename to load
MODE_APPEND       = "append"        # prompt for filename to append

# Schema sub-actions
SCHEMA_ACTION_RENAME = "rename"
SCHEMA_ACTION_MAXLEN = "maxlen"
SCHEMA_ACTION_INSERT = "insert"
SCHEMA_ACTION_DELETE = "delete"


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

MM_CSS = """
MailMergeScreen {
    background: $surface;
    layout: vertical;
}
#mm-status {
    dock: top;
    height: 1;
    background: $secondary;
    color: $text;
    padding: 0 1;
}
#mm-message {
    dock: top;
    height: 1;
    background: $primary;
    color: $text;
    padding: 0 1;
}
#mm-body {
    height: 1fr;
    padding: 0 1;
}
#mm-help {
    dock: bottom;
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
MAIL MERGE OVERVIEW
  E  Enter / Edit Records      Add a new record one field at a time
  U  Update Records            Browse, edit, or delete existing records
  F  Format Record             Change field names and field lengths
  B  Build Subset              Filter records by a field range
  S  Save Database             Write the current database to disk
  L  Load Database             Load a database file from disk
  A  Append Database           Merge another file with the same schema

RECOMMENDED FLOW
  1. Start with F to review the record format.
  2. Use E to enter records.
  3. Use U to browse or correct records later.
  4. Use B before printing if you only want some records.
  5. Save with S when the database looks right.

FORMAT RECORD
  Up / Down    Select a field
  R            Rename the selected field
  M            Change the field max length (1-20)
  I            Insert a new field after the current one
  D            Delete the selected field

ENTER / UPDATE RECORDS
  Type text and press Enter to move to the next field.
  Empty fields are allowed.
  On the last field, Y saves the record and N keeps editing.
  In Update mode, Page Up / Page Down browse records.
  Ctrl+D deletes the current record after confirmation.

BUILD SUBSET
  Choose the field number to filter.
  Enter Low Value, then High Value.
  Matching records stay active until you clear the subset with Esc.

USING MERGE FIELDS IN A DOCUMENT
  In the editor, insert the merge marker (@) and type the field number
  after it, such as @1 for the first field or @3 for the third field.

OTHER
  F1 / ?       Show this help screen
  Esc          Return to the previous Mail Merge menu\
"""


# ---------------------------------------------------------------------------
# Screen
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


class MailMergeScreen(Screen):
    """Mail Merge database module."""

    CSS = MM_CSS

    BINDINGS = [
        Binding("escape", "exit_module", "Exit", show=False),
    ]

    def __init__(self, app_state: AppState, initial_mode: str = MODE_MAIN) -> None:
        super().__init__()
        self._app_state = app_state
        self._initial_mode = initial_mode
        # Each app gets one shared DB instance stored on app state
        if app_state.mail_merge_db is None:
            app_state.mail_merge_db = MailMergeDB()
        self._db = app_state.mail_merge_db

        self._mode = MODE_MAIN
        self._input_buf = ""

        # Schema editing
        self._schema_field_idx = 0       # which field is selected in schema view
        self._schema_action = ""         # what we're editing (rename/maxlen/insert/delete)

        # Data entry
        self._entry_record: list[str] = []
        self._entry_field_idx = 0

        # Update (browse) mode
        self._update_record_idx = 0
        self._update_field_idx = 0       # which field is being edited (if any)
        self._update_editing = False

        # Subset
        self._subset_field_idx = 0
        self._subset_low = ""
        self._subset_high = ""
        self._subset_entering = "field"  # "field" | "low" | "high"
        self._active_subset: list[int] | None = None  # None = all records
        self._message_text = ""
        self._status_text = ""
        self._body_text = ""
        self._help_text = ""
        self._enter_main()

    # ------------------------------------------------------------------
    # Compose
    # ------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Static(self._message_text, id="mm-message")
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
    # Mode entry
    # ------------------------------------------------------------------

    def _enter_main(self) -> None:
        self._mode = MODE_MAIN
        self._refresh_status()
        self._set_body(
            "[bold]*** MAIL MERGE ***[/]\n\n"
            "[bold]E[/]  Enter / Edit Records\n"
            "[bold]U[/]  Update Records (browse existing)\n"
            "[bold]F[/]  Format Record (edit schema)\n"
            "[bold]B[/]  Build Subset (filter)\n"
            "[bold]S[/]  Save Database to file\n"
            "[bold]L[/]  Load Database from file\n"
            "[bold]A[/]  Append database file\n"
            "\n"
            "[dim]F1/?  Help    Esc  Return to Main Menu[/]"
        )
        self._set_message("Select an option. F1 or ? for help.")
        self._set_help(" E Enter  U Update  F Format  B Subset  S Save  L Load  A Append  Esc Exit")

    def _enter_schema(self) -> None:
        self._mode = MODE_SCHEMA
        self._schema_field_idx = min(self._schema_field_idx, len(self._db.fields) - 1)
        self._render_schema()
        self._set_message("Schema editor: Up/Down select field, R Rename, M Max-len, I Insert, D Delete, Esc done")
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
        self._set_help(" Enter Next field  Esc Abort")

    def _enter_update(self) -> None:
        self._mode = MODE_UPDATE
        if not self._db.records:
            self._set_message("No records yet. Use E to enter data first.")
            self._enter_main()
            return
        self._update_record_idx = 0
        self._update_editing = False
        self._render_update_record()
        self._set_help(" PgUp/PgDn Browse  Ctrl+D Delete  E Edit field  Esc Back")

    def _enter_subset(self) -> None:
        self._mode = MODE_SUBSET
        self._subset_low = ""
        self._subset_high = ""
        self._subset_field_idx = 0
        self._subset_entering = "field"
        self._render_subset()
        self._set_message("Subset: enter field number (1–{}) to filter on".format(len(self._db.fields)))
        self._set_help(" Enter Confirm  Esc Cancel")

    # ------------------------------------------------------------------
    # Key handling dispatcher
    # ------------------------------------------------------------------

    def on_key(self, event: events.Key) -> None:
        if event.key == "f1" or event.character == "?":
            self.action_show_help()
            event.stop()
            return
        key = event.key
        {
            MODE_MAIN:          self._key_main,
            MODE_SCHEMA:        self._key_schema,
            MODE_SCHEMA_EDIT:   self._key_schema_edit,
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
        }.get(self._mode, lambda k, e: None)(key, event)
        event.stop()

    # ------------------------------------------------------------------
    # Main menu keys
    # ------------------------------------------------------------------

    def _key_main(self, key: str, event) -> None:
        k = key.lower()
        if k == "e":
            self._enter_data_entry()
        elif k == "u":
            self._enter_update()
        elif k == "f":
            self._enter_schema()
        elif k == "b":
            self._enter_subset()
        elif k == "s":
            self._mode = MODE_SAVE
            self._input_buf = self._db.filename
            self._set_body(f"Save database to file:\n\n> {self._input_buf}")
            self._set_message("Enter filename, Enter to confirm")
            self._set_help(" Enter Save  Esc Cancel")
        elif k == "l":
            self._mode = MODE_LOAD
            self._input_buf = ""
            self._set_body("Load database from file:\n\n> ")
            self._set_message("Enter filename, Enter to confirm")
            self._set_help(" Enter Load  Esc Cancel")
        elif k == "a":
            self._mode = MODE_APPEND
            self._input_buf = ""
            self._set_body("Append database file:\n\n> ")
            self._set_message("Enter filename, Enter to confirm")
            self._set_help(" Enter Append  Esc Cancel")
        elif key == "escape":
            self.action_exit_module()

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
            self._enter_main()

    def _key_schema_edit(self, key: str, event) -> None:
        action = self._schema_action
        idx = self._schema_field_idx

        if action == SCHEMA_ACTION_DELETE:
            if key.lower() == "y":
                # Wipe that field from all records first
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
                # Truncate existing data to new limit
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
        self._set_message(
            f"{'Rename' if action == SCHEMA_ACTION_RENAME else ('Max len' if action == SCHEMA_ACTION_MAXLEN else 'Insert name')}: {self._input_buf}"
        )

    def _render_schema(self) -> None:
        lines = ["[bold]Record Format (Schema)[/]\n", f"{'#':<4}{'Field Name':<14}{'Max Len':>8}\n"]
        for i, f in enumerate(self._db.fields):
            marker = "[reverse]" if i == self._schema_field_idx else ""
            end = "[/reverse]" if i == self._schema_field_idx else ""
            lines.append(f"{marker}{i + 1:<4}{f.name:<14}{f.max_len:>8}{end}")
        lines.append(f"\n[dim]{len(self._db.fields)}/{MAX_FIELDS} fields defined[/]")
        self._set_body("\n".join(lines))

    # ------------------------------------------------------------------
    # Data entry
    # ------------------------------------------------------------------

    def _key_data_entry(self, key: str, event) -> None:
        fi = self._entry_field_idx
        fdef = self._db.fields[fi]

        if key == "escape":
            self._set_message("Entry aborted.")
            self._enter_main()
            return

        if key == "enter":
            # Commit current field value
            self._entry_record[fi] = self._input_buf
            next_fi = fi + 1
            if next_fi >= len(self._db.fields):
                # Last field — confirm
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
            self._db.records.append(list(self._entry_record))
            self._refresh_status()
            self._set_message(f"Record {len(self._db.records)} saved. Enter another? E or Esc")
            self._mode = MODE_MAIN
            self._enter_main()
        elif k == "n":
            # Go back to editing last field
            last = len(self._db.fields) - 1
            self._entry_field_idx = last
            self._input_buf = self._entry_record[last]
            self._mode = MODE_ENTER
            self._render_entry_form()
            self._set_message(f"Field {last + 1}/{len(self._db.fields)}: {self._db.fields[last].name}")

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

        if key == "pagedown":
            self._update_record_idx = min(len(records) - 1, self._update_record_idx + 1)
            self._render_update_record()
        elif key == "pageup":
            self._update_record_idx = max(0, self._update_record_idx - 1)
            self._render_update_record()
        elif key == "ctrl+d":
            self._mode = MODE_UPDATE_DELETE
            rec_num = self._update_record_idx + 1
            self._set_message(f"Delete record {rec_num}? Are you sure? Y/N")
            self._set_help(" Y Delete  N Cancel")
        elif key.lower() == "e":
            self._mode = MODE_UPDATE_EDIT
            self._update_field_idx = 0
            self._update_editing = True
            self._input_buf = records[self._update_record_idx][0]
            self._render_update_edit()
            self._set_message(f"Edit field 1: {self._db.fields[0].name}")
            self._set_help(" Enter Next field  Esc Done")
        elif key == "escape":
            self._enter_main()

    def _key_update_delete(self, key: str, event) -> None:
        k = key.lower()
        if k == "y":
            idx = self._update_record_idx
            self._db.records.pop(idx)
            self._refresh_status()
            if not self._db.records:
                self._set_message("All records deleted.")
                self._enter_main()
                return
            self._update_record_idx = min(idx, len(self._db.records) - 1)
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
            self._render_update_record()
            self._set_message("Edit cancelled.")
            return

        if key == "enter":
            rec[fi] = self._input_buf
            next_fi = fi + 1
            if next_fi >= len(self._db.fields):
                self._mode = MODE_UPDATE
                self._render_update_record()
                self._set_message("Record updated.")
            else:
                self._update_field_idx = next_fi
                self._input_buf = rec[next_fi]
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
        lines = [f"[bold]Record {idx + 1} of {len(records)}[/]\n"]
        for i, fdef in enumerate(self._db.fields):
            val = rec[i] if i < len(rec) else ""
            name = fdef.name.ljust(MAX_FIELD_NAME_LEN)
            lines.append(f"  {i + 1:>2}. {name}  {val or '[dim](empty)[/dim]'}")
        self._set_body("\n".join(lines))
        self._set_message(f"Record {idx + 1}/{len(records)}  PgUp/PgDn browse  E edit  Ctrl+D delete  Esc back")

    def _render_update_edit(self) -> None:
        rec = self._db.records[self._update_record_idx]
        idx = self._update_record_idx
        lines = [f"[bold]Edit Record {idx + 1}[/]\n"]
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
                # Apply filter
                results = self._db.apply_subset(
                    self._subset_field_idx, self._subset_low, self._subset_high
                )
                self._active_subset = results
                self._render_subset_results(results)
                self._set_message(f"Subset active: {len(results)} record(s) match. Esc to clear.")
                self._mode = MODE_MAIN
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
    # File operations (Save / Load / Append)
    # ------------------------------------------------------------------

    def _key_filename(self, key: str, event) -> None:
        mode = self._mode
        if key == "escape":
            self._enter_main()
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
        verb = {"save": "Save to", "load": "Load from", "append": "Append from"}
        label = verb.get(self._mode.split("_")[0], "File")  # "save"/"load"/"append"
        # Actually mode strings are "save", "load", "append" directly
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
            self._set_message(f"Appended {len(to_add)} records (of {len(other.records)}).")
        except (OSError, ValueError) as e:
            self._set_message(f"Append error: {e}")
        self._enter_main()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _refresh_status(self) -> None:
        state = self._app_state
        bytes_free = state.bytes_free if hasattr(state, "bytes_free") else 0
        self._status_text = f" Bytes Free: {bytes_free:,}   Records Free: {self._db.records_free}"
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

    def _set_static(self, selector: str, content: str) -> None:
        if self.is_mounted:
            self.query_one(selector, Static).update(content)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_show_help(self) -> None:
        self.app.push_screen(MailMergeHelpScreen())  # type: ignore[attr-defined]

    def action_exit_module(self) -> None:
        self.app.pop_screen()  # type: ignore[attr-defined]
