"""Mail Merge screen — flat-file database for form letters."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Static
from textual import events

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

MAX_FIELDS   = 15
MAX_RECORDS  = 255
MAX_FIELD_NAME_LEN = 12
MAX_FIELD_DATA_LEN = 20

DEFAULT_FIELDS: list[tuple[str, int]] = [
    ("Last Name",    20),
    ("First Name",   20),
    ("Company",      20),
    ("Address",      20),
    ("City",         20),
    ("State",        10),
    ("Zipcode",      10),
    ("Phone",        15),
    ("Salutation",   20),
    ("Title",        20),
    ("Department",   20),
    ("Country",      20),
    ("Email",        20),
    ("Fax",          15),
    ("Notes",        20),
]


@dataclass
class FieldDef:
    name: str
    max_len: int = MAX_FIELD_DATA_LEN


@dataclass
class MailMergeDB:
    """In-memory mail merge database."""
    fields: list[FieldDef] = field(default_factory=lambda: [
        FieldDef(name, ml) for name, ml in DEFAULT_FIELDS
    ])
    records: list[list[str]] = field(default_factory=list)
    filename: str = ""

    @property
    def records_free(self) -> int:
        return MAX_RECORDS - len(self.records)

    def new_record(self) -> list[str]:
        return [""] * len(self.fields)

    def to_dict(self) -> dict:
        return {
            "fields": [{"name": f.name, "max_len": f.max_len} for f in self.fields],
            "records": self.records,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MailMergeDB":
        db = cls.__new__(cls)
        db.fields = [FieldDef(f["name"], f["max_len"]) for f in data["fields"]]
        db.records = data["records"]
        db.filename = ""
        return db

    def schema_matches(self, other: "MailMergeDB") -> bool:
        if len(self.fields) != len(other.fields):
            return False
        return all(
            a.max_len == b.max_len
            for a, b in zip(self.fields, other.fields)
        )

    def apply_subset(self, field_idx: int, low: str, high: str) -> list[int]:
        """Return indices of records where fields[field_idx] is in [low, high]."""
        results = []
        for i, rec in enumerate(self.records):
            val = rec[field_idx] if field_idx < len(rec) else ""
            if low.lower() <= val.lower() <= high.lower():
                results.append(i)
        return results


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
"""


# ---------------------------------------------------------------------------
# Screen
# ---------------------------------------------------------------------------

class MailMergeScreen(Screen):
    """Mail Merge database module."""

    CSS = MM_CSS

    BINDINGS = [
        Binding("escape", "exit_module", "Exit", show=False),
    ]

    def __init__(self, app_state) -> None:
        super().__init__()
        self._app_state = app_state
        # Each app gets one shared DB instance stored on app state
        if not hasattr(app_state, "mail_merge_db"):
            app_state.mail_merge_db = MailMergeDB()
        self._db: MailMergeDB = app_state.mail_merge_db

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

    # ------------------------------------------------------------------
    # Compose
    # ------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Static("", id="mm-message")
        yield Static("", id="mm-status")
        yield Static("", id="mm-body")
        yield Static("", id="mm-help")

    def on_mount(self) -> None:
        self._enter_main()

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
            "[dim]Esc  Return to Main Menu[/]"
        )
        self._set_message("Select an option.")
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
        key = event.key
        {
            MODE_MAIN:          self._key_main,
            MODE_SCHEMA:        self._key_schema,
            MODE_SCHEMA_EDIT:   self._key_schema_edit,
            MODE_ENTER:         self._key_enter,
            MODE_ENTER_CONFIRM: self._key_enter_confirm,
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

    def _key_enter(self, key: str, event) -> None:
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

    def _key_enter_confirm(self, key: str, event) -> None:
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
            Path(filename).write_text(json.dumps(self._db.to_dict(), indent=2))
            self._db.filename = filename
            self._set_message(f"Saved {len(self._db.records)} records to '{filename}'.")
        except OSError as e:
            self._set_message(f"Save error: {e}")
        self._enter_main()

    def _load_db(self, filename: str) -> None:
        try:
            data = json.loads(Path(filename).read_text())
            self._db = MailMergeDB.from_dict(data)
            self._db.filename = filename
            self._app_state.mail_merge_db = self._db
            self._refresh_status()
            self._set_message(f"Loaded {len(self._db.records)} records from '{filename}'.")
        except (OSError, json.JSONDecodeError, KeyError) as e:
            self._set_message(f"Load error: {e}")
        self._enter_main()

    def _append_db(self, filename: str) -> None:
        try:
            data = json.loads(Path(filename).read_text())
            other = MailMergeDB.from_dict(data)
            if not self._db.schema_matches(other):
                self._set_message("Cannot append — schemas do not match (field count or lengths differ).")
                self._enter_main()
                return
            space = self._db.records_free
            to_add = other.records[:space]
            self._db.records.extend(to_add)
            self._refresh_status()
            self._set_message(f"Appended {len(to_add)} records (of {len(other.records)}).")
        except (OSError, json.JSONDecodeError, KeyError) as e:
            self._set_message(f"Append error: {e}")
        self._enter_main()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _refresh_status(self) -> None:
        state = self._app_state
        bytes_free = state.bytes_free if hasattr(state, "bytes_free") else 0
        self._set_static(
            "#mm-status",
            f" Bytes Free: {bytes_free:,}   Records Free: {self._db.records_free}",
        )

    def _set_message(self, msg: str) -> None:
        self._set_static("#mm-message", f" {msg}")

    def _set_body(self, content: str) -> None:
        self._set_static("#mm-body", content)

    def _set_help(self, text: str) -> None:
        self._set_static("#mm-help", text)

    def _set_static(self, selector: str, content: str) -> None:
        if self.is_mounted:
            self.query_one(selector, Static).update(content)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_exit_module(self) -> None:
        self.app.pop_screen()  # type: ignore[attr-defined]
