"""End-to-end tests for mail merge: create DB, add records, merge into document,
preview (ANSI), and export (Markdown, PostScript).

Two test levels:
  1. Non-UI: exercise the underlying objects directly — MailMergeDB, _apply_record,
     _render_with_mail_merge, export_markdown, export_postscript.
  2. UI: exercise the MailMergeScreen state machine to create a database and
     enter records through the same code paths as a real user, then feed the
     resulting DB into the export pipeline.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from safari_writer.export_md import export_markdown
from safari_writer.export_ps import export_postscript
from safari_writer.mail_merge_db import (
    FieldDef,
    MailMergeDB,
    apply_mail_merge_to_buffer,
    load_mail_merge_db,
    save_mail_merge_db,
)
from safari_writer.screens.editor import CTRL_MERGE
from safari_writer.screens.mail_merge import (
    MODE_ENTER,
    MODE_ENTER_CONFIRM,
    MODE_LOAD,
    MODE_MAIN,
    MODE_SAVE,
    MODE_UPDATE,
    MailMergeScreen,
)
from safari_writer.screens.print_screen import (
    _apply_record,
    _buffer_has_merge_markers,
    _render_with_mail_merge,
)
from safari_writer.state import AppState, GlobalFormat

MERGE = CTRL_MERGE  # "\x11"


# ── helpers ──────────────────────────────────────────────────────────


def _make_db(
    fields: list[tuple[str, int]],
    records: list[list[str]],
) -> MailMergeDB:
    """Build a MailMergeDB from compact specs."""
    db = MailMergeDB()
    db.fields = [FieldDef(n, m) for n, m in fields]
    db.records = [list(r) for r in records]
    return db


def _fmt(**kw) -> GlobalFormat:
    f = GlobalFormat()
    for k, v in kw.items():
        setattr(f, k, v)
    return f


LETTER_FIELDS = [("First", 10), ("Last", 10), ("City", 15)]

LETTER_RECORDS = [
    ["Alice", "Smith", "Portland"],
    ["Bob", "Jones", "Seattle"],
    ["Carol", "Adams", "Denver"],
]

LETTER_BUFFER = [
    f"Dear {MERGE}1 {MERGE}2,",
    "",
    f"Welcome to our {MERGE}3 office.",
    "",
    "Sincerely,",
    "The Team",
]


# =====================================================================
# LEVEL 1 — Non-UI end-to-end: objects only
# =====================================================================


class TestE2ENonUI:
    """Full pipeline with no UI: create DB → merge → preview → export."""

    # ── create DB and verify structure ──

    def test_create_db_with_records(self):
        db = _make_db(LETTER_FIELDS, LETTER_RECORDS)
        assert len(db.fields) == 3
        assert len(db.records) == 3
        assert db.records_free == 252

    # ── save / load round-trip ──

    def test_save_load_roundtrip(self, tmp_path: Path):
        db = _make_db(LETTER_FIELDS, LETTER_RECORDS)
        path = tmp_path / "letters.mm"
        save_mail_merge_db(db, path)
        loaded = load_mail_merge_db(path)
        assert len(loaded.records) == 3
        assert loaded.records[0] == ["Alice", "Smith", "Portland"]
        assert loaded.records[2][2] == "Denver"
        assert loaded.filename == str(path)

    # ── buffer has merge markers ──

    def test_letter_buffer_has_merge_markers(self):
        assert _buffer_has_merge_markers(LETTER_BUFFER)

    # ── per-record substitution ──

    def test_apply_record_substitutes_all_fields(self):
        merged = _apply_record(LETTER_BUFFER, LETTER_RECORDS[0])
        assert merged[0] == "Dear Alice Smith,"
        assert merged[2] == "Welcome to our Portland office."
        # Non-merge lines untouched
        assert merged[4] == "Sincerely,"
        assert merged[5] == "The Team"

    def test_apply_record_each_record_different(self):
        results = [_apply_record(LETTER_BUFFER, rec) for rec in LETTER_RECORDS]
        assert results[0][0] == "Dear Alice Smith,"
        assert results[1][0] == "Dear Bob Jones,"
        assert results[2][0] == "Dear Carol Adams,"

    # ── first-record-only helper ──

    def test_apply_mail_merge_to_buffer_uses_first(self):
        db = _make_db(LETTER_FIELDS, LETTER_RECORDS)
        merged = apply_mail_merge_to_buffer(LETTER_BUFFER, db)
        assert merged[0] == "Dear Alice Smith,"
        assert merged[2] == "Welcome to our Portland office."

    # ── ANSI preview: all records rendered ──

    def test_ansi_preview_contains_all_records(self):
        db = _make_db(LETTER_FIELDS, LETTER_RECORDS)
        fmt = _fmt()
        lines = _render_with_mail_merge(LETTER_BUFFER, fmt, db)
        joined = "\n".join(lines)
        assert "Alice" in joined
        assert "Bob" in joined
        assert "Carol" in joined
        # Record separators for records 2 and 3
        assert "Record 2" in joined
        assert "Record 3" in joined

    def test_ansi_preview_record_count(self):
        db = _make_db(LETTER_FIELDS, LETTER_RECORDS)
        fmt = _fmt()
        lines = _render_with_mail_merge(LETTER_BUFFER, fmt, db)
        joined = "\n".join(lines)
        # Count "Record N" separators (records 2..N get a separator)
        separator_count = sum(1 for ln in lines if "═" in ln and "Record" in ln)
        assert separator_count == 2  # separators before record 2 and 3

    def test_ansi_preview_no_placeholders(self):
        """Merged output should have no <<@N>> placeholders."""
        db = _make_db(LETTER_FIELDS, LETTER_RECORDS)
        fmt = _fmt()
        lines = _render_with_mail_merge(LETTER_BUFFER, fmt, db)
        joined = "\n".join(lines)
        assert "<<@" not in joined

    # ── Markdown export: one copy per record ──

    def test_markdown_export_all_records(self):
        db = _make_db(LETTER_FIELDS, LETTER_RECORDS)
        md = export_markdown(LETTER_BUFFER, _fmt(), db)
        assert "Dear Alice Smith," in md
        assert "Dear Bob Jones," in md
        assert "Dear Carol Adams," in md

    def test_markdown_export_separators(self):
        db = _make_db(LETTER_FIELDS, LETTER_RECORDS)
        md = export_markdown(LETTER_BUFFER, _fmt(), db)
        # Separator "---" appears between copies (2 separators for 3 records)
        sep_count = md.count("\n---\n")
        assert sep_count == 2

    def test_markdown_export_no_placeholders(self):
        db = _make_db(LETTER_FIELDS, LETTER_RECORDS)
        md = export_markdown(LETTER_BUFFER, _fmt(), db)
        assert "{{field" not in md
        assert "<<@" not in md

    def test_markdown_export_preserves_static_text(self):
        db = _make_db(LETTER_FIELDS, LETTER_RECORDS)
        md = export_markdown(LETTER_BUFFER, _fmt(), db)
        assert "Sincerely," in md
        assert "The Team" in md

    # ── PostScript export: one copy per record ──

    def test_postscript_export_all_records(self):
        db = _make_db(LETTER_FIELDS, LETTER_RECORDS)
        ps = export_postscript(LETTER_BUFFER, _fmt(), db)
        assert "Alice" in ps
        assert "Bob" in ps
        assert "Carol" in ps

    def test_postscript_export_no_placeholders(self):
        db = _make_db(LETTER_FIELDS, LETTER_RECORDS)
        ps = export_postscript(LETTER_BUFFER, _fmt(), db)
        assert "<<@" not in ps

    def test_postscript_export_valid_structure(self):
        db = _make_db(LETTER_FIELDS, LETTER_RECORDS)
        ps = export_postscript(LETTER_BUFFER, _fmt(), db)
        assert ps.startswith("%!PS-Adobe-3.0")
        assert "%%EOF" in ps
        # Multiple showpage directives — one per page per record copy
        showpage_count = ps.count("showpage")
        assert showpage_count >= 3  # at least one page per record

    def test_postscript_export_page_count(self):
        db = _make_db(LETTER_FIELDS, LETTER_RECORDS)
        ps = export_postscript(LETTER_BUFFER, _fmt(), db)
        # Each record gets at least 1 %%Page directive
        page_directives = [ln for ln in ps.splitlines() if ln.startswith("%%Page:")]
        assert len(page_directives) >= 3

    # ── Full pipeline with save/load ──

    def test_full_pipeline_save_load_export(self, tmp_path: Path):
        """Create DB → save → load → merge → export Markdown → verify N copies."""
        db = _make_db(LETTER_FIELDS, LETTER_RECORDS)
        path = tmp_path / "e2e.mm"
        save_mail_merge_db(db, path)

        loaded = load_mail_merge_db(path)
        md = export_markdown(LETTER_BUFFER, _fmt(), loaded)
        for rec in LETTER_RECORDS:
            assert rec[0] in md  # first name
            assert rec[2] in md  # city

        ps = export_postscript(LETTER_BUFFER, _fmt(), loaded)
        for rec in LETTER_RECORDS:
            assert rec[0] in ps

    # ── Edge: single record ──

    def test_single_record_no_separator_in_preview(self):
        db = _make_db(LETTER_FIELDS, [LETTER_RECORDS[0]])
        lines = _render_with_mail_merge(LETTER_BUFFER, _fmt(), db)
        joined = "\n".join(lines)
        assert "Alice" in joined
        assert "Record 2" not in joined

    def test_single_record_no_separator_in_markdown(self):
        db = _make_db(LETTER_FIELDS, [LETTER_RECORDS[0]])
        md = export_markdown(LETTER_BUFFER, _fmt(), db)
        assert "Alice" in md
        assert "\n---\n" not in md

    # ── Edge: many records ──

    def test_many_records_export(self):
        """Export with 20 records produces 20 copies."""
        fields = [("Name", 10)]
        records = [[f"Person{i:02d}"] for i in range(20)]
        db = _make_db(fields, records)
        buf = [f"Hello {MERGE}1"]

        md = export_markdown(buf, _fmt(), db)
        for i in range(20):
            assert f"Person{i:02d}" in md

        sep_count = md.count("\n---\n")
        assert sep_count == 19  # separators between 20 copies

    # ── Edge: subset filtering before export ──

    def test_subset_filtering_then_export(self):
        """Simulate subset: filter records, build sub-DB, export only matching."""
        db = _make_db(LETTER_FIELDS, LETTER_RECORDS)
        # Filter by city starting with "P" to "Q"
        matching_indices = db.apply_subset(2, "P", "Q")
        assert len(matching_indices) == 1  # only Portland

        # Build subset DB
        subset_db = _make_db(LETTER_FIELDS, [db.records[i] for i in matching_indices])
        md = export_markdown(LETTER_BUFFER, _fmt(), subset_db)
        assert "Alice" in md  # Portland record
        assert "Bob" not in md  # Seattle filtered out
        assert "Carol" not in md  # Denver filtered out

    # ── Multi-field merge markers ──

    def test_all_fields_substituted(self):
        """Every field in the schema can be referenced and substituted."""
        n = 5
        fields = [(f"F{i}", 10) for i in range(1, n + 1)]
        values = [f"val{i}" for i in range(1, n + 1)]
        db = _make_db(fields, [values])
        buf = [" ".join(f"{MERGE}{i}" for i in range(1, n + 1))]
        merged = _apply_record(buf, values)
        assert merged[0] == "val1 val2 val3 val4 val5"


# =====================================================================
# LEVEL 2 — UI-driven: exercise MailMergeScreen state machine
# =====================================================================


def _make_screen(db: MailMergeDB | None = None) -> MailMergeScreen:
    """Build a MailMergeScreen with stubbed widget methods (no Textual app)."""
    state = AppState()
    if db is not None:
        state.mail_merge_db = db
    with patch("textual.screen.Screen.__init__", return_value=None):
        screen = MailMergeScreen.__new__(MailMergeScreen)
        screen._app_state = state
        if state.mail_merge_db is None:
            state.mail_merge_db = MailMergeDB()
        screen._db = state.mail_merge_db
        screen._mode = MODE_MAIN
        screen._input_buf = ""
        screen._schema_field_idx = 0
        screen._schema_action = ""
        screen._entry_record = []
        screen._entry_field_idx = 0
        screen._update_record_idx = 0
        screen._update_field_idx = 0
        screen._update_editing = False
        screen._subset_field_idx = 0
        screen._subset_low = ""
        screen._subset_high = ""
        screen._subset_entering = "field"
        screen._active_subset = None
        screen._message_text = ""
        screen._status_text = ""
        screen._body_text = ""
        screen._help_text = ""
        screen._selected_index = 0
        screen._from_correct = False
    screen._set_message = MagicMock()
    screen._set_body = MagicMock()
    screen._set_help = MagicMock()
    screen._set_static = MagicMock()
    screen._refresh_status = MagicMock()
    screen._render_schema = MagicMock()
    screen._render_entry_form = MagicMock()
    screen._render_update_record = MagicMock()
    screen._render_update_edit = MagicMock()
    return screen


def _make_key(key: str, character: str | None = None):
    ev = MagicMock()
    ev.key = key
    ev.character = (
        character if character is not None else (key if len(key) == 1 else None)
    )
    ev.stop = MagicMock()
    return ev


def _type_string(screen: MailMergeScreen, text: str) -> None:
    """Simulate typing each character of text into the screen."""
    for ch in text:
        screen.on_key(_make_key(ch))


def _press(screen: MailMergeScreen, key: str, character: str | None = None) -> None:
    """Simulate pressing a special key."""
    screen.on_key(_make_key(key, character))


def _enter_record_via_ui(
    screen: MailMergeScreen,
    values: list[str],
) -> None:
    """Enter a full record through the data-entry flow.

    Assumes screen is in MODE_MAIN and database has fields matching len(values).
    Types each field value, presses Enter to advance, then confirms with 'y'.

    The MailMergeScreen key map:
      - 'n' from main menu → enter data entry (new record)
      - type chars → fill field (capped at max_len)
      - Enter → advance to next field
      - after last field → MODE_ENTER_CONFIRM
      - 'y' → save record → "Enter another? Y/N"
      - 'n' → return to main menu
    """
    # 'n' = new record entry from main menu
    _press(screen, "n")
    assert screen._mode == MODE_ENTER, f"Expected MODE_ENTER, got {screen._mode}"

    for i, val in enumerate(values):
        _type_string(screen, val)
        _press(screen, "enter")

    # After last field, should be in MODE_ENTER_CONFIRM
    assert (
        screen._mode == MODE_ENTER_CONFIRM
    ), f"Expected MODE_ENTER_CONFIRM after last field, got {screen._mode}"
    # Confirm with 'y' to save the record
    _press(screen, "y")
    # Now in "Enter another? Y/N" state (still MODE_ENTER_CONFIRM but
    # _entry_record is cleared)
    assert screen._mode == MODE_ENTER_CONFIRM
    # Press 'n' to decline entering another and return to main menu
    _press(screen, "n")
    assert (
        screen._mode == MODE_MAIN
    ), f"Expected MODE_MAIN after declining another, got {screen._mode}"


class TestE2EUI:
    """Enter records via the MailMergeScreen, then run them through the
    export pipeline to verify the full workflow."""

    def test_create_db_enter_records_export_markdown(self):
        """UI flow: start with empty DB, enter 3 records, export to Markdown."""
        # Use a simple 3-field schema
        db = _make_db(LETTER_FIELDS, [])
        screen = _make_screen(db)

        # Enter 3 records through the UI
        for rec in LETTER_RECORDS:
            _enter_record_via_ui(screen, rec)

        # Verify records were added to the DB
        assert len(screen._db.records) == 3
        assert screen._db.records[0] == ["Alice", "Smith", "Portland"]
        assert screen._db.records[1] == ["Bob", "Jones", "Seattle"]
        assert screen._db.records[2] == ["Carol", "Adams", "Denver"]

        # Now export — same DB that the screen just populated
        md = export_markdown(LETTER_BUFFER, _fmt(), screen._db)
        assert "Dear Alice Smith," in md
        assert "Dear Bob Jones," in md
        assert "Dear Carol Adams," in md
        sep_count = md.count("\n---\n")
        assert sep_count == 2

    def test_create_db_enter_records_export_postscript(self):
        """UI flow: enter records, export to PostScript."""
        db = _make_db(LETTER_FIELDS, [])
        screen = _make_screen(db)

        for rec in LETTER_RECORDS:
            _enter_record_via_ui(screen, rec)

        ps = export_postscript(LETTER_BUFFER, _fmt(), screen._db)
        assert ps.startswith("%!PS-Adobe-3.0")
        for rec in LETTER_RECORDS:
            assert rec[0] in ps
        assert "%%EOF" in ps

    def test_create_db_enter_records_ansi_preview(self):
        """UI flow: enter records, render ANSI preview."""
        db = _make_db(LETTER_FIELDS, [])
        screen = _make_screen(db)

        for rec in LETTER_RECORDS:
            _enter_record_via_ui(screen, rec)

        lines = _render_with_mail_merge(LETTER_BUFFER, _fmt(), screen._db)
        joined = "\n".join(lines)
        assert "Alice" in joined
        assert "Bob" in joined
        assert "Carol" in joined
        assert "<<@" not in joined

    def test_enter_records_with_max_length_truncation(self):
        """Fields are capped at max_len during data entry."""
        db = _make_db([("Name", 5)], [])
        screen = _make_screen(db)

        _press(screen, "n")  # enter data entry (new record)
        _type_string(screen, "TooLongName")  # exceeds max_len of 5
        _press(screen, "enter")
        _press(screen, "y")  # confirm
        _press(screen, "n")  # don't enter another

        # Value should be truncated to max_len
        assert len(screen._db.records[0][0]) <= 5

    def test_enter_record_then_browse(self):
        """Enter records via UI, then browse them in update mode."""
        db = _make_db(LETTER_FIELDS, [])
        screen = _make_screen(db)

        for rec in LETTER_RECORDS:
            _enter_record_via_ui(screen, rec)

        # Enter update mode ('e' = Edit/Update existing records)
        _press(screen, "e")
        assert screen._mode == MODE_UPDATE
        assert screen._update_record_idx == 0

        # Navigate to next record
        _press(screen, "pagedown")
        assert screen._update_record_idx == 1

        _press(screen, "pagedown")
        assert screen._update_record_idx == 2

        # Can't go past last record
        _press(screen, "pagedown")
        assert screen._update_record_idx == 2

    def test_enter_and_delete_record(self):
        """Enter 3 records, delete one, export should have only 2."""
        db = _make_db(LETTER_FIELDS, [])
        screen = _make_screen(db)

        for rec in LETTER_RECORDS:
            _enter_record_via_ui(screen, rec)

        assert len(screen._db.records) == 3

        # Enter update mode and delete record 0 (Alice)
        _press(screen, "e")
        assert screen._mode == MODE_UPDATE
        _press(screen, "ctrl+d")  # delete
        _press(screen, "y")  # confirm

        assert len(screen._db.records) == 2

        # Export should not contain Alice
        md = export_markdown(LETTER_BUFFER, _fmt(), screen._db)
        assert "Alice" not in md
        assert "Bob" in md
        assert "Carol" in md

    def test_save_and_load_via_screen(self, tmp_path: Path):
        """Enter records via UI, save to disk, load into new screen, export."""
        db = _make_db(LETTER_FIELDS, [])
        screen = _make_screen(db)

        for rec in LETTER_RECORDS:
            _enter_record_via_ui(screen, rec)

        # Save the DB directly (simulating the save action)
        path = tmp_path / "ui_test.mm"
        save_mail_merge_db(screen._db, path)

        # Load into a fresh DB
        loaded = load_mail_merge_db(path)
        assert len(loaded.records) == 3

        # Export from the loaded DB
        md = export_markdown(LETTER_BUFFER, _fmt(), loaded)
        assert "Dear Alice Smith," in md
        assert "Dear Bob Jones," in md
        assert "Dear Carol Adams," in md

    def test_enter_records_then_subset_and_export(self):
        """Enter records via UI, filter via subset, export only matching."""
        db = _make_db(LETTER_FIELDS, [])
        screen = _make_screen(db)

        for rec in LETTER_RECORDS:
            _enter_record_via_ui(screen, rec)

        # Apply subset on field 2 (City), range "S" to "T" → only Seattle
        matching = screen._db.apply_subset(2, "S", "T")
        assert matching == [1]  # Bob in Seattle

        subset_db = _make_db(
            LETTER_FIELDS,
            [screen._db.records[i] for i in matching],
        )
        md = export_markdown(LETTER_BUFFER, _fmt(), subset_db)
        assert "Bob" in md
        assert "Alice" not in md
        assert "Carol" not in md

    def test_appstate_integration(self):
        """Verify the DB created via screen is properly on AppState."""
        db = _make_db(LETTER_FIELDS, [])
        screen = _make_screen(db)

        for rec in LETTER_RECORDS:
            _enter_record_via_ui(screen, rec)

        # The screen's _db and the AppState's mail_merge_db should be the same object
        assert screen._app_state.mail_merge_db is screen._db
        assert len(screen._app_state.mail_merge_db.records) == 3

        # Simulate what PrintPreviewScreen.on_mount does:
        state = screen._app_state
        lines = _render_with_mail_merge(state.buffer, state.fmt, state.mail_merge_db)
        # With default empty buffer, no merge markers → renders as-is
        assert isinstance(lines, list)

        # Now set a buffer with merge markers on the state
        state.buffer = list(LETTER_BUFFER)
        lines = _render_with_mail_merge(state.buffer, state.fmt, state.mail_merge_db)
        joined = "\n".join(lines)
        assert "Alice" in joined
        assert "Bob" in joined

    def test_full_workflow_create_enter_save_load_preview_export(self, tmp_path: Path):
        """Complete user workflow from scratch through all output formats."""
        # 1. Create DB with custom fields
        fields = [("Name", 15), ("Email", 20)]
        db = _make_db(fields, [])
        screen = _make_screen(db)

        # 2. Enter records
        records = [
            ["John Doe", "john@example.com"],
            ["Jane Roe", "jane@example.com"],
        ]
        for rec in records:
            _enter_record_via_ui(screen, rec)

        assert len(screen._db.records) == 2

        # 3. Save
        path = tmp_path / "workflow.mm"
        save_mail_merge_db(screen._db, path)

        # 4. Load into fresh state
        loaded = load_mail_merge_db(path)

        # 5. Create document buffer with merge markers
        doc_buffer = [
            f"To: {MERGE}1",
            f"Email: {MERGE}2",
            "",
            f"Hello {MERGE}1,",
            "This is a test.",
        ]

        # 6. ANSI preview
        fmt = _fmt()
        preview_lines = _render_with_mail_merge(doc_buffer, fmt, loaded)
        preview_text = "\n".join(preview_lines)
        assert "John Doe" in preview_text
        assert "Jane Roe" in preview_text
        assert "john@example.com" in preview_text
        assert "jane@example.com" in preview_text
        assert "<<@" not in preview_text
        assert "Record 2" in preview_text

        # 7. Markdown export
        md = export_markdown(doc_buffer, fmt, loaded)
        assert "To: John Doe" in md
        assert "To: Jane Roe" in md
        assert "Email: john@example.com" in md
        assert "Email: jane@example.com" in md
        assert md.count("\n---\n") == 1  # 1 separator for 2 records
        assert "{{field" not in md

        # 8. PostScript export
        ps = export_postscript(doc_buffer, fmt, loaded)
        assert ps.startswith("%!PS-Adobe-3.0")
        assert "John Doe" in ps
        assert "Jane Roe" in ps
        assert "%%EOF" in ps
        pages = [ln for ln in ps.splitlines() if ln.startswith("%%Page:")]
        assert len(pages) >= 2


class TestE2EEdgeCases:
    """Edge-case end-to-end scenarios."""

    def test_empty_db_export_shows_placeholders(self):
        """Export with empty DB leaves merge placeholders in output."""
        db = _make_db(LETTER_FIELDS, [])
        md = export_markdown(LETTER_BUFFER, _fmt(), db)
        # No records → no merge performed → {{fieldN}} placeholders
        assert "{{field1}}" in md
        assert "{{field2}}" in md

    def test_no_db_export_shows_placeholders(self):
        """Export with no DB at all shows placeholders."""
        md = export_markdown(LETTER_BUFFER, _fmt(), None)
        assert "{{field1}}" in md

    def test_no_merge_markers_db_ignored(self):
        """If document has no merge markers, DB records are not iterated."""
        db = _make_db(LETTER_FIELDS, LETTER_RECORDS)
        plain_buffer = ["Hello World", "No merge markers here"]
        md = export_markdown(plain_buffer, _fmt(), db)
        assert "Hello World" in md
        assert "Alice" not in md
        # Only one copy of the document
        assert "\n---\n" not in md

    def test_record_with_empty_fields(self):
        """Records with empty field values are handled gracefully."""
        db = _make_db(LETTER_FIELDS, [["", "", ""]])
        buf = [f"Name: {MERGE}1 {MERGE}2, City: {MERGE}3"]
        md = export_markdown(buf, _fmt(), db)
        assert "Name:  , City: " in md

    def test_fifteen_field_schema(self):
        """Maximum 15 fields all get merged correctly."""
        fields = [(f"F{i}", 10) for i in range(1, 16)]
        values = [f"v{i}" for i in range(1, 16)]
        db = _make_db(fields, [values])
        # Reference all 15 fields
        buf = [" ".join(f"{MERGE}{i}" for i in range(1, 16))]
        merged = _apply_record(buf, values)
        expected = " ".join(f"v{i}" for i in range(1, 16))
        assert merged[0] == expected

    def test_multi_digit_field_15(self):
        """Field 15 (two digits) is correctly parsed and substituted."""
        fields = [(f"F{i}", 10) for i in range(1, 16)]
        values = [f"v{i}" for i in range(1, 16)]
        db = _make_db(fields, [values])
        buf = [f"F15={MERGE}15"]
        md = export_markdown(buf, _fmt(), db)
        assert "v15" in md

    def test_255_records_export(self):
        """Max records (255) all appear in export output."""
        fields = [("ID", 5)]
        records = [[f"R{i:03d}"] for i in range(255)]
        db = _make_db(fields, records)
        buf = [f"ID: {MERGE}1"]
        md = export_markdown(buf, _fmt(), db)
        # Spot-check first, last, and middle
        assert "R000" in md
        assert "R127" in md
        assert "R254" in md
        sep_count = md.count("\n---\n")
        assert sep_count == 254

    def test_mixed_merge_and_plain_lines(self):
        """Only lines with merge markers get field substitution."""
        db = _make_db([("Name", 10)], [["Alice"], ["Bob"]])
        buf = [
            "Static header line",
            f"Dear {MERGE}1,",
            "Static body text.",
            f"Goodbye {MERGE}1.",
        ]
        md = export_markdown(buf, _fmt(), db)
        # Both records present
        assert "Dear Alice," in md
        assert "Dear Bob," in md
        assert "Goodbye Alice." in md
        assert "Goodbye Bob." in md
        # Static text present in both copies
        assert md.count("Static header line") == 2
        assert md.count("Static body text.") == 2
