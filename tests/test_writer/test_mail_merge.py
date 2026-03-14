"""Unit tests for the Mail Merge module."""

import asyncio
import json
from unittest.mock import MagicMock, PropertyMock, patch

from textual.widgets import Static

from safari_writer.app import SafariWriterApp
from safari_writer.screens.mail_merge import (DEFAULT_FIELDS,
                                              MAX_FIELD_NAME_LEN, MAX_FIELDS,
                                              MAX_RECORDS, MM_CSS, MODE_APPEND,
                                              MODE_ENTER, MODE_ENTER_CONFIRM,
                                              MODE_LOAD, MODE_MAIN, MODE_SAVE,
                                              MODE_SCHEMA, MODE_SCHEMA_EDIT,
                                              MODE_SUBSET, MODE_SUBSET_FIELD,
                                              MODE_UPDATE, MODE_UPDATE_DELETE,
                                              MODE_UPDATE_EDIT,
                                              SCHEMA_ACTION_DELETE,
                                              SCHEMA_ACTION_INSERT,
                                              SCHEMA_ACTION_MAXLEN,
                                              SCHEMA_ACTION_RENAME, FieldDef,
                                              MailMergeDB, MailMergeHelpScreen,
                                              MailMergeScreen)
from safari_writer.state import AppState

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_db(n_records: int = 0) -> MailMergeDB:
    db = MailMergeDB()
    for i in range(n_records):
        rec = [f"val{i}_{j}" for j in range(len(db.fields))]
        # Trim to max_len per field
        rec = [v[: db.fields[j].max_len] for j, v in enumerate(rec)]
        db.records.append(rec)
    return db


def make_screen(db: MailMergeDB | None = None) -> MailMergeScreen:
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
        screen._from_correct = False
    # Stub widget methods
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


def make_key(key: str, character: str | None = None):
    ev = MagicMock()
    ev.key = key
    ev.character = (
        character if character is not None else (key if len(key) == 1 else None)
    )
    ev.stop = MagicMock()
    return ev


# ---------------------------------------------------------------------------
# Mounting / help
# ---------------------------------------------------------------------------


class TestMailMergeMountBehavior:
    def test_menu_is_seeded_before_mount(self):
        screen = MailMergeScreen(AppState())
        assert "Create File" in screen._body_text
        assert "SELECT ITEM" in screen._message_text
        assert "F1/? Help" in screen._help_text
        assert "RECORDS FREE" in screen._status_text

    def test_menu_is_visible_after_mount(self):
        async def run():
            app = SafariWriterApp()
            async with app.run_test() as pilot:
                app.push_screen(MailMergeScreen(app.state))
                await pilot.pause()
                screen = app.screen
                assert (
                    screen.query_one("#mm-title", Static).content
                    == "*** MAIL MERGE ***"
                )
                assert "Create File" in screen._body_text
                assert "SELECT ITEM" in screen._message_text
                assert "F1/? Help" in screen._help_text
                assert "RECORDS FREE" in screen._status_text

        asyncio.run(run())


class TestMailMergeHelp:
    def test_show_help_pushes_modal(self):
        screen = make_screen()
        app = MagicMock()
        with patch.object(
            MailMergeScreen, "app", new_callable=PropertyMock
        ) as app_prop:
            app_prop.return_value = app
            screen.action_show_help()

        pushed = app.push_screen.call_args.args[0]
        assert isinstance(pushed, MailMergeHelpScreen)

    def test_help_key_opens_modal(self):
        screen = make_screen()
        event = make_key("f1", None)
        app = MagicMock()

        with patch.object(
            MailMergeScreen, "app", new_callable=PropertyMock
        ) as app_prop:
            app_prop.return_value = app
            screen.on_key(event)

        pushed = app.push_screen.call_args.args[0]
        assert isinstance(pushed, MailMergeHelpScreen)
        event.stop.assert_called_once()

    def test_status_bar_is_docked(self):
        assert "#mm-outer {" in MM_CSS
        assert "border: solid $accent;" in MM_CSS
        assert "#mm-title {" in MM_CSS


# ---------------------------------------------------------------------------
# MailMergeDB model
# ---------------------------------------------------------------------------


class TestMailMergeDB:
    def test_default_fields_count(self):
        db = MailMergeDB()
        assert len(db.fields) == len(DEFAULT_FIELDS)

    def test_default_fields_names(self):
        db = MailMergeDB()
        expected_names = [name for name, _ in DEFAULT_FIELDS]
        assert [f.name for f in db.fields] == expected_names

    def test_records_free_empty(self):
        db = MailMergeDB()
        assert db.records_free == MAX_RECORDS

    def test_records_free_with_records(self):
        db = make_db(5)
        assert db.records_free == MAX_RECORDS - 5

    def test_new_record_length(self):
        db = MailMergeDB()
        rec = db.new_record()
        assert len(rec) == len(db.fields)
        assert all(v == "" for v in rec)

    def test_schema_matches_same(self):
        a = MailMergeDB()
        b = MailMergeDB()
        assert a.schema_matches(b)

    def test_schema_matches_different_count(self):
        a = MailMergeDB()
        b = MailMergeDB()
        b.fields.pop()
        assert not a.schema_matches(b)

    def test_schema_matches_different_maxlen(self):
        a = MailMergeDB()
        b = MailMergeDB()
        b.fields[0].max_len = 5
        assert not a.schema_matches(b)

    def test_to_dict_roundtrip(self):
        db = make_db(3)
        data = db.to_dict()
        restored = MailMergeDB.from_dict(data)
        assert len(restored.fields) == len(db.fields)
        assert restored.records == db.records

    def test_apply_subset_range(self):
        db = MailMergeDB()
        db.fields = [FieldDef("State", 10)]
        db.records = [["AL"], ["TX"], ["AK"], ["CA"], ["AZ"]]
        # "A" to "B" → AL, AK, AZ
        result = db.apply_subset(0, "A", "B")
        vals = [db.records[i][0] for i in result]
        assert "AL" in vals
        assert "AK" in vals
        assert "AZ" in vals
        assert "TX" not in vals
        assert "CA" not in vals

    def test_apply_subset_case_insensitive(self):
        db = MailMergeDB()
        db.fields = [FieldDef("State", 10)]
        db.records = [["al"], ["TX"]]
        result = db.apply_subset(0, "A", "B")
        assert 0 in result

    def test_apply_subset_all(self):
        db = make_db(3)
        result = db.apply_subset(0, "", "zzzzz")
        assert len(result) == 3


# ---------------------------------------------------------------------------
# Schema editing
# ---------------------------------------------------------------------------


class TestSchemaEditing:
    def test_rename_field(self):
        screen = make_screen()
        screen._schema_field_idx = 0
        screen._schema_action = SCHEMA_ACTION_RENAME
        screen._input_buf = "Surname"
        screen._mode = MODE_SCHEMA_EDIT
        screen._key_schema_edit("enter", make_key("enter"))
        assert screen._db.fields[0].name == "Surname"
        assert screen._mode == MODE_SCHEMA

    def test_rename_truncated_to_12(self):
        screen = make_screen()
        screen._schema_field_idx = 0
        screen._schema_action = SCHEMA_ACTION_RENAME
        screen._input_buf = "A" * 20
        screen._mode = MODE_SCHEMA_EDIT
        screen._key_schema_edit("enter", make_key("enter"))
        assert len(screen._db.fields[0].name) == MAX_FIELD_NAME_LEN

    def test_rename_empty_rejected(self):
        screen = make_screen()
        original = screen._db.fields[0].name
        screen._schema_field_idx = 0
        screen._schema_action = SCHEMA_ACTION_RENAME
        screen._input_buf = ""
        screen._mode = MODE_SCHEMA_EDIT
        screen._key_schema_edit("enter", make_key("enter"))
        assert screen._db.fields[0].name == original
        assert screen._mode == MODE_SCHEMA_EDIT  # still editing

    def test_set_maxlen(self):
        screen = make_screen()
        screen._schema_field_idx = 0
        screen._schema_action = SCHEMA_ACTION_MAXLEN
        screen._input_buf = "10"
        screen._mode = MODE_SCHEMA_EDIT
        screen._key_schema_edit("enter", make_key("enter"))
        assert screen._db.fields[0].max_len == 10

    def test_set_maxlen_invalid_rejected(self):
        screen = make_screen()
        original = screen._db.fields[0].max_len
        screen._schema_field_idx = 0
        screen._schema_action = SCHEMA_ACTION_MAXLEN
        screen._input_buf = "99"  # above MAX_FIELD_DATA_LEN (20)
        screen._mode = MODE_SCHEMA_EDIT
        screen._key_schema_edit("enter", make_key("enter"))
        assert screen._db.fields[0].max_len == original

    def test_set_maxlen_truncates_existing_data(self):
        db = make_db(1)
        db.records[0][0] = "A" * 20
        screen = make_screen(db)
        screen._schema_field_idx = 0
        screen._schema_action = SCHEMA_ACTION_MAXLEN
        screen._input_buf = "5"
        screen._mode = MODE_SCHEMA_EDIT
        screen._key_schema_edit("enter", make_key("enter"))
        assert len(db.records[0][0]) <= 5

    def test_insert_field(self):
        screen = make_screen()
        original_count = len(screen._db.fields)
        screen._schema_field_idx = 0
        screen._schema_action = SCHEMA_ACTION_INSERT
        screen._input_buf = "Twitter"
        screen._mode = MODE_SCHEMA_EDIT
        screen._key_schema_edit("enter", make_key("enter"))
        assert len(screen._db.fields) == original_count + 1
        assert screen._db.fields[1].name == "Twitter"

    def test_insert_field_adds_blank_to_records(self):
        db = make_db(2)
        screen = make_screen(db)
        screen._schema_field_idx = 0
        screen._schema_action = SCHEMA_ACTION_INSERT
        screen._input_buf = "NewField"
        screen._mode = MODE_SCHEMA_EDIT
        screen._key_schema_edit("enter", make_key("enter"))
        assert len(db.records[0]) == len(db.fields)
        assert db.records[0][1] == ""

    def test_insert_rejected_at_max_fields(self):
        db = MailMergeDB()
        while len(db.fields) < MAX_FIELDS:
            db.fields.append(FieldDef(f"Extra{len(db.fields)}"))
        screen = make_screen(db)
        screen._schema_field_idx = 0
        screen._key_schema("i", make_key("i"))
        # Should not enter edit mode
        assert screen._mode != MODE_SCHEMA_EDIT

    def test_delete_field(self):
        screen = make_screen()
        original_count = len(screen._db.fields)
        screen._schema_field_idx = 0
        screen._schema_action = SCHEMA_ACTION_DELETE
        screen._mode = MODE_SCHEMA_EDIT
        screen._key_schema_edit("y", make_key("y"))
        assert len(screen._db.fields) == original_count - 1

    def test_delete_field_removes_from_records(self):
        db = make_db(2)
        original_field_count = len(db.fields)
        screen = make_screen(db)
        screen._schema_field_idx = 0
        screen._schema_action = SCHEMA_ACTION_DELETE
        screen._mode = MODE_SCHEMA_EDIT
        screen._key_schema_edit("y", make_key("y"))
        assert len(db.records[0]) == original_field_count - 1

    def test_delete_last_field_rejected(self):
        db = MailMergeDB()
        db.fields = [FieldDef("Only")]
        screen = make_screen(db)
        screen._schema_field_idx = 0
        screen._key_schema("d", make_key("d"))
        assert len(screen._db.fields) == 1

    def test_delete_cancelled_on_n(self):
        screen = make_screen()
        original_count = len(screen._db.fields)
        screen._schema_field_idx = 0
        screen._schema_action = SCHEMA_ACTION_DELETE
        screen._mode = MODE_SCHEMA_EDIT
        screen._key_schema_edit("n", make_key("n"))
        assert len(screen._db.fields) == original_count


# ---------------------------------------------------------------------------
# Data entry
# ---------------------------------------------------------------------------


class TestDataEntry:
    def test_enter_advances_field(self):
        screen = make_screen()
        screen._mode = MODE_ENTER
        screen._entry_record = screen._db.new_record()
        screen._entry_field_idx = 0
        screen._input_buf = "Smith"
        screen._key_data_entry("enter", make_key("enter"))
        assert screen._entry_record[0] == "Smith"
        assert screen._entry_field_idx == 1

    def test_enter_on_last_field_triggers_confirm(self):
        screen = make_screen()
        screen._mode = MODE_ENTER
        screen._entry_record = screen._db.new_record()
        screen._entry_field_idx = len(screen._db.fields) - 1
        screen._input_buf = "Some note"
        screen._key_data_entry("enter", make_key("enter"))
        assert screen._mode == MODE_ENTER_CONFIRM

    def test_backspace_removes_char(self):
        screen = make_screen()
        screen._mode = MODE_ENTER
        screen._entry_record = screen._db.new_record()
        screen._entry_field_idx = 0
        screen._input_buf = "ab"
        screen._key_data_entry("backspace", make_key("backspace"))
        assert screen._input_buf == "a"

    def test_typing_adds_char(self):
        screen = make_screen()
        screen._mode = MODE_ENTER
        screen._entry_record = screen._db.new_record()
        screen._entry_field_idx = 0
        screen._input_buf = ""
        ev = make_key("a", "a")
        screen._key_data_entry("a", ev)
        assert screen._input_buf == "a"

    def test_typing_respects_max_len(self):
        screen = make_screen()
        screen._mode = MODE_ENTER
        screen._entry_record = screen._db.new_record()
        screen._entry_field_idx = 0
        fmax = screen._db.fields[0].max_len
        screen._input_buf = "X" * fmax
        ev = make_key("z", "z")
        screen._key_data_entry("z", ev)
        assert len(screen._input_buf) == fmax

    def test_confirm_y_saves_record(self):
        screen = make_screen()
        screen._mode = MODE_ENTER_CONFIRM
        screen._entry_record = ["Smith"] + [""] * (len(screen._db.fields) - 1)
        screen._enter_main = MagicMock()
        screen._key_data_entry_confirm("y", make_key("y"))
        assert len(screen._db.records) == 1
        assert screen._db.records[0][0] == "Smith"

    def test_confirm_n_returns_to_last_field(self):
        screen = make_screen()
        screen._mode = MODE_ENTER_CONFIRM
        screen._entry_record = screen._db.new_record()
        screen._key_data_entry_confirm("n", make_key("n"))
        assert screen._mode == MODE_ENTER
        assert screen._entry_field_idx == len(screen._db.fields) - 1

    def test_full_database_rejects_new_record(self):
        db = make_db(MAX_RECORDS)
        screen = make_screen(db)
        screen._enter_main = MagicMock()
        screen._enter_data_entry()
        screen._enter_main.assert_called()

    def test_empty_fields_allowed(self):
        screen = make_screen()
        screen._mode = MODE_ENTER_CONFIRM
        screen._entry_record = screen._db.new_record()  # all empty
        screen._enter_main = MagicMock()
        screen._key_data_entry_confirm("y", make_key("y"))
        assert len(screen._db.records) == 1
        assert all(v == "" for v in screen._db.records[0])


# ---------------------------------------------------------------------------
# Update / browse
# ---------------------------------------------------------------------------


class TestUpdateMode:
    def test_pagedown_advances_record(self):
        db = make_db(3)
        screen = make_screen(db)
        screen._mode = MODE_UPDATE
        screen._update_record_idx = 0
        screen._key_update("pagedown", make_key("pagedown"))
        assert screen._update_record_idx == 1

    def test_pageup_goes_back(self):
        db = make_db(3)
        screen = make_screen(db)
        screen._mode = MODE_UPDATE
        screen._update_record_idx = 2
        screen._key_update("pageup", make_key("pageup"))
        assert screen._update_record_idx == 1

    def test_pageup_at_start_stays(self):
        db = make_db(3)
        screen = make_screen(db)
        screen._mode = MODE_UPDATE
        screen._update_record_idx = 0
        screen._key_update("pageup", make_key("pageup"))
        assert screen._update_record_idx == 0

    def test_pagedown_at_end_stays(self):
        db = make_db(3)
        screen = make_screen(db)
        screen._mode = MODE_UPDATE
        screen._update_record_idx = 2
        screen._key_update("pagedown", make_key("pagedown"))
        assert screen._update_record_idx == 2

    def test_ctrl_d_enters_delete_confirm(self):
        db = make_db(2)
        screen = make_screen(db)
        screen._mode = MODE_UPDATE
        screen._key_update("ctrl+d", make_key("ctrl+d"))
        assert screen._mode == MODE_UPDATE_DELETE

    def test_delete_confirm_y_removes_record(self):
        db = make_db(3)
        screen = make_screen(db)
        screen._mode = MODE_UPDATE_DELETE
        screen._update_record_idx = 1
        screen._key_update_delete("y", make_key("y"))
        assert len(db.records) == 2
        assert screen._mode == MODE_UPDATE

    def test_delete_confirm_n_cancels(self):
        db = make_db(3)
        screen = make_screen(db)
        screen._mode = MODE_UPDATE_DELETE
        screen._update_record_idx = 1
        screen._key_update_delete("n", make_key("n"))
        assert len(db.records) == 3
        assert screen._mode == MODE_UPDATE

    def test_delete_last_record_returns_to_main(self):
        db = make_db(1)
        screen = make_screen(db)
        screen._mode = MODE_UPDATE_DELETE
        screen._update_record_idx = 0
        screen._enter_main = MagicMock()
        screen._key_update_delete("y", make_key("y"))
        screen._enter_main.assert_called()

    def test_edit_mode_enter_advances_field(self):
        db = make_db(1)
        screen = make_screen(db)
        screen._mode = MODE_UPDATE_EDIT
        screen._update_record_idx = 0
        screen._update_field_idx = 0
        screen._input_buf = "NewValue"
        screen._key_update_edit("enter", make_key("enter"))
        assert db.records[0][0] == "NewValue"
        assert screen._update_field_idx == 1

    def test_edit_mode_saves_on_last_field(self):
        db = make_db(1)
        screen = make_screen(db)
        screen._mode = MODE_UPDATE_EDIT
        screen._update_record_idx = 0
        screen._update_field_idx = len(db.fields) - 1
        screen._input_buf = "FinalValue"
        screen._key_update_edit("enter", make_key("enter"))
        assert db.records[0][-1] == "FinalValue"
        assert screen._mode == MODE_UPDATE

    def test_update_empty_db_goes_to_main(self):
        screen = make_screen()
        screen._enter_main = MagicMock()
        screen._enter_update()
        screen._enter_main.assert_called()


# ---------------------------------------------------------------------------
# Build Subset
# ---------------------------------------------------------------------------


class TestBuildSubset:
    def test_apply_subset_stores_result(self):
        db = MailMergeDB()
        db.fields = [FieldDef("State", 10)]
        db.records = [["AL"], ["TX"], ["AK"]]
        result = db.apply_subset(0, "A", "B")
        assert set(result) == {0, 2}  # AL, AK

    def test_subset_field_number_validation(self):
        screen = make_screen()
        screen._mode = MODE_SUBSET
        screen._input_buf = "99"  # out of range
        screen._key_subset("enter", make_key("enter"))
        assert screen._mode == MODE_SUBSET  # stays in subset

    def test_subset_valid_field_advances(self):
        screen = make_screen()
        screen._mode = MODE_SUBSET
        screen._input_buf = "1"
        screen._render_subset = MagicMock()
        screen._key_subset("enter", make_key("enter"))
        assert screen._mode == MODE_SUBSET_FIELD
        assert screen._subset_field_idx == 0

    def test_subset_low_high_applies(self):
        db = MailMergeDB()
        db.fields = [FieldDef("State", 10)]
        db.records = [["AL"], ["TX"], ["AK"]]
        screen = make_screen(db)
        screen._mode = MODE_SUBSET_FIELD
        screen._subset_field_idx = 0
        screen._subset_entering = "low"
        screen._input_buf = "A"
        screen._render_subset = MagicMock()

        # Enter low
        screen._key_subset_field("enter", make_key("enter"))
        assert screen._subset_low == "A"
        assert screen._subset_entering == "high"

        # Enter high
        screen._input_buf = "B"
        screen._render_subset_results = MagicMock()
        screen._key_subset_field("enter", make_key("enter"))
        assert screen._active_subset is not None
        # AL and AK are in range A-B
        assert len(screen._active_subset) == 2


# ---------------------------------------------------------------------------
# File operations
# ---------------------------------------------------------------------------


class TestFileOperations:
    def test_save_and_load_roundtrip(self, tmp_path):
        db = make_db(3)
        db.records[0][0] = "Doe"
        screen = make_screen(db)
        filename = str(tmp_path / "test.mm")
        screen._enter_main = MagicMock()
        screen._save_db(filename)

        screen2 = make_screen()
        screen2._enter_main = MagicMock()
        screen2._load_db(filename)
        assert len(screen2._db.records) == 3
        assert screen2._db.records[0][0] == "Doe"

    def test_load_nonexistent_file(self):
        screen = make_screen()
        screen._enter_main = MagicMock()
        screen._load_db("/nonexistent/path/file.mm")
        screen._set_message.assert_called()
        screen._enter_main.assert_called()

    def test_append_matching_schema(self, tmp_path):
        db_a = make_db(2)
        db_b = make_db(2)
        db_b.records[0][0] = "Extra"
        # Save db_b
        path = tmp_path / "extra.mm"
        path.write_text(json.dumps(db_b.to_dict()))

        screen = make_screen(db_a)
        screen._enter_main = MagicMock()
        screen._append_db(str(path))
        assert len(db_a.records) == 4

    def test_append_mismatched_schema_rejected(self, tmp_path):
        db_a = MailMergeDB()
        db_b = MailMergeDB()
        db_b.fields.pop()  # different field count

        path = tmp_path / "mismatch.mm"
        path.write_text(json.dumps(db_b.to_dict()))

        screen = make_screen(db_a)
        screen._enter_main = MagicMock()
        screen._append_db(str(path))
        assert len(db_a.records) == 0  # nothing added

    def test_append_respects_max_records(self, tmp_path):
        db_a = make_db(MAX_RECORDS - 1)
        db_b = make_db(5)  # only 1 slot left

        path = tmp_path / "more.mm"
        path.write_text(json.dumps(db_b.to_dict()))

        screen = make_screen(db_a)
        screen._enter_main = MagicMock()
        screen._append_db(str(path))
        assert len(db_a.records) == MAX_RECORDS

    def test_save_updates_filename(self, tmp_path):
        screen = make_screen()
        screen._enter_main = MagicMock()
        filename = str(tmp_path / "db.mm")
        screen._save_db(filename)
        assert screen._db.filename == filename


# ---------------------------------------------------------------------------
# Key routing
# ---------------------------------------------------------------------------


class TestKeyRouting:
    def test_main_e_enters_update(self):
        # E = Edit File (browse/update records) in the classic AtariWriter layout
        db = make_db(1)
        screen = make_screen(db)
        screen._mode = MODE_MAIN
        screen._enter_update = MagicMock()
        screen._key_main("e", make_key("e"))
        screen._enter_update.assert_called_once()

    def test_main_c_enters_schema(self):
        # C = Create File — resets DB and enters schema mode
        screen = make_screen()
        screen._mode = MODE_MAIN
        screen._key_main("c", make_key("c"))
        assert screen._mode == MODE_SCHEMA

    def test_main_f_enters_schema(self):
        screen = make_screen()
        screen._mode = MODE_MAIN
        screen._enter_schema = MagicMock()
        screen._key_main("f", make_key("f"))
        screen._enter_schema.assert_called_once()

    def test_main_b_enters_subset(self):
        screen = make_screen()
        screen._mode = MODE_MAIN
        screen._enter_subset = MagicMock()
        screen._key_main("b", make_key("b"))
        screen._enter_subset.assert_called_once()

    def test_main_s_enters_save(self):
        screen = make_screen()
        screen._mode = MODE_MAIN
        screen._key_main("s", make_key("s"))
        assert screen._mode == MODE_SAVE

    def test_main_l_enters_load(self):
        screen = make_screen()
        screen._mode = MODE_MAIN
        screen._key_main("l", make_key("l"))
        assert screen._mode == MODE_LOAD

    def test_main_a_enters_append(self):
        screen = make_screen()
        screen._mode = MODE_MAIN
        screen._key_main("a", make_key("a"))
        assert screen._mode == MODE_APPEND

    def test_exit_pops_screen(self):
        screen = make_screen()
        mock_app = MagicMock()
        with patch.object(
            type(screen), "app", new_callable=lambda: property(lambda self: mock_app)
        ):
            screen.action_exit_module()
        mock_app.pop_screen.assert_called_once()
