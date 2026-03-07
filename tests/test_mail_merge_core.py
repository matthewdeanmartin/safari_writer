"""Core unit tests for mail merge — model, validation, I/O, buffer merge.

No UI/screen mocking. Uses tmp_path for file tests.
"""

import json
import pytest

from safari_writer.mail_merge_db import (
    DEFAULT_FIELDS,
    FieldDef,
    MAX_FIELD_DATA_LEN,
    MAX_FIELD_NAME_LEN,
    MAX_FIELDS,
    MAX_RECORDS,
    MailMergeDB,
    apply_mail_merge_to_buffer,
    inspect_mail_merge_db,
    load_mail_merge_db,
    save_mail_merge_db,
    validate_mail_merge_data,
)
from safari_writer.screens.print_screen import (
    _apply_record,
    _buffer_has_merge_markers,
    _render_with_mail_merge,
    _render_document,
)
from safari_writer.screens.editor import CTRL_MERGE
from safari_writer.state import GlobalFormat
from safari_writer.export_md import export_markdown
from safari_writer.export_ps import export_postscript


# ── helpers ──────────────────────────────────────────────────────────


def _simple_db(fields: list[tuple[str, int]], records: list[list[str]]) -> MailMergeDB:
    db = MailMergeDB()
    db.fields = [FieldDef(n, m) for n, m in fields]
    db.records = [list(r) for r in records]
    return db


def _fmt(**kw) -> GlobalFormat:
    f = GlobalFormat()
    for k, v in kw.items():
        setattr(f, k, v)
    return f


MERGE = CTRL_MERGE  # "\x11"


# =====================================================================
# FieldDef
# =====================================================================


class TestFieldDef:
    def test_default_max_len(self):
        f = FieldDef("Name")
        assert f.max_len == MAX_FIELD_DATA_LEN

    def test_custom_max_len(self):
        f = FieldDef("Zip", 5)
        assert f.max_len == 5


# =====================================================================
# MailMergeDB — construction & properties
# =====================================================================


class TestMailMergeDBConstruction:
    def test_empty_db_has_default_fields(self):
        db = MailMergeDB()
        assert len(db.fields) == len(DEFAULT_FIELDS)
        for (expected_name, expected_len), actual in zip(DEFAULT_FIELDS, db.fields):
            assert actual.name == expected_name
            assert actual.max_len == expected_len

    def test_records_free_boundary(self):
        db = MailMergeDB()
        db.records = [db.new_record()] * MAX_RECORDS
        assert db.records_free == 0

    def test_new_record_matches_field_count(self):
        db = _simple_db([("A", 5), ("B", 10)], [])
        rec = db.new_record()
        assert rec == ["", ""]


# =====================================================================
# schema_matches
# =====================================================================


class TestSchemaMatches:
    def test_same_schema(self):
        a = _simple_db([("X", 10)], [])
        b = _simple_db([("X", 10)], [])
        assert a.schema_matches(b)

    def test_different_name(self):
        a = _simple_db([("X", 10)], [])
        b = _simple_db([("Y", 10)], [])
        assert not a.schema_matches(b)

    def test_different_max_len(self):
        a = _simple_db([("X", 10)], [])
        b = _simple_db([("X", 5)], [])
        assert not a.schema_matches(b)

    def test_different_field_count(self):
        a = _simple_db([("X", 10), ("Y", 10)], [])
        b = _simple_db([("X", 10)], [])
        assert not a.schema_matches(b)

    def test_empty_fields_match(self):
        """Two DBs with identical single-field schemas match."""
        a = _simple_db([("Only", 1)], [["a"]])
        b = _simple_db([("Only", 1)], [["b"], ["c"]])
        assert a.schema_matches(b)


# =====================================================================
# apply_subset
# =====================================================================


class TestApplySubset:
    def test_exact_match(self):
        db = _simple_db([("V", 10)], [["apple"], ["banana"], ["cherry"]])
        result = db.apply_subset(0, "banana", "banana")
        assert result == [1]

    def test_empty_low_matches_from_start(self):
        db = _simple_db([("V", 10)], [["apple"], ["banana"]])
        result = db.apply_subset(0, "", "az")
        assert result == [0]  # "apple" <= "az"

    def test_no_matches(self):
        db = _simple_db([("V", 10)], [["apple"], ["banana"]])
        result = db.apply_subset(0, "x", "z")
        assert result == []

    def test_all_match(self):
        db = _simple_db([("V", 10)], [["a"], ["b"], ["c"]])
        result = db.apply_subset(0, "", "zzz")
        assert result == [0, 1, 2]

    def test_case_insensitive(self):
        db = _simple_db([("V", 10)], [["Alpha"], ["BETA"]])
        result = db.apply_subset(0, "a", "c")
        assert set(result) == {0, 1}

    def test_second_field(self):
        db = _simple_db([("First", 10), ("Last", 10)], [
            ["Alice", "Smith"],
            ["Bob", "Jones"],
            ["Carol", "Adams"],
        ])
        result = db.apply_subset(1, "A", "K")
        vals = [db.records[i][1] for i in result]
        assert "Jones" in vals
        assert "Adams" in vals
        assert "Smith" not in vals

    def test_short_record_returns_empty_for_missing_field(self):
        db = _simple_db([("A", 5), ("B", 5)], [["x"]])  # record too short
        result = db.apply_subset(1, "", "zzz")
        assert result == [0]  # empty string is in range


# =====================================================================
# to_dict / from_dict round-trip
# =====================================================================


class TestSerialization:
    def test_roundtrip_empty(self):
        db = _simple_db([("Name", 10)], [])
        restored = MailMergeDB.from_dict(db.to_dict())
        assert len(restored.fields) == 1
        assert restored.fields[0].name == "Name"
        assert restored.records == []

    def test_roundtrip_with_records(self):
        db = _simple_db([("A", 5), ("B", 5)], [["hello", "world"], ["foo", "bar"]])
        restored = MailMergeDB.from_dict(db.to_dict())
        assert restored.records == db.records
        assert [f.name for f in restored.fields] == ["A", "B"]
        assert [f.max_len for f in restored.fields] == [5, 5]

    def test_roundtrip_preserves_max_len(self):
        db = _simple_db([("Zip", 5)], [["12345"]])
        restored = MailMergeDB.from_dict(db.to_dict())
        assert restored.fields[0].max_len == 5

    def test_from_dict_sets_empty_filename(self):
        db = _simple_db([("X", 5)], [])
        db.filename = "should_be_cleared"
        restored = MailMergeDB.from_dict(db.to_dict())
        assert restored.filename == ""

    def test_to_dict_structure(self):
        db = _simple_db([("Name", 10)], [["Alice"]])
        d = db.to_dict()
        assert "fields" in d
        assert "records" in d
        assert d["fields"] == [{"name": "Name", "max_len": 10}]
        assert d["records"] == [["Alice"]]


# =====================================================================
# validate_mail_merge_data
# =====================================================================


class TestValidation:
    def test_valid_data(self):
        data = {"fields": [{"name": "A", "max_len": 10}], "records": [["hello"]]}
        assert validate_mail_merge_data(data) == []

    def test_not_a_dict(self):
        errors = validate_mail_merge_data("not a dict")
        assert any("JSON object" in e for e in errors)

    def test_missing_fields_key(self):
        errors = validate_mail_merge_data({"records": []})
        assert any("'fields'" in e for e in errors)

    def test_missing_records_key(self):
        errors = validate_mail_merge_data({"fields": []})
        assert any("'records'" in e for e in errors)

    def test_fields_not_a_list(self):
        errors = validate_mail_merge_data({"fields": "bad", "records": []})
        assert any("'fields' must be a list" in e for e in errors)

    def test_records_not_a_list(self):
        errors = validate_mail_merge_data({"fields": [], "records": "bad"})
        assert any("'records' must be a list" in e for e in errors)

    def test_too_many_fields(self):
        fields = [{"name": f"F{i}", "max_len": 5} for i in range(MAX_FIELDS + 1)]
        errors = validate_mail_merge_data({"fields": fields, "records": []})
        assert any("field count" in e for e in errors)

    def test_zero_fields(self):
        errors = validate_mail_merge_data({"fields": [], "records": []})
        assert any("field count" in e for e in errors)

    def test_field_not_a_dict(self):
        errors = validate_mail_merge_data({"fields": ["bad"], "records": []})
        assert any("must be an object" in e for e in errors)

    def test_field_name_empty(self):
        errors = validate_mail_merge_data({"fields": [{"name": "", "max_len": 5}], "records": []})
        assert any("name must be a non-empty" in e for e in errors)

    def test_field_name_whitespace_only(self):
        errors = validate_mail_merge_data({"fields": [{"name": "   ", "max_len": 5}], "records": []})
        assert any("name must be a non-empty" in e for e in errors)

    def test_field_name_too_long(self):
        long_name = "X" * (MAX_FIELD_NAME_LEN + 1)
        errors = validate_mail_merge_data(
            {"fields": [{"name": long_name, "max_len": 5}], "records": []}
        )
        assert any("exceeds" in e for e in errors)

    def test_field_name_missing(self):
        errors = validate_mail_merge_data({"fields": [{"max_len": 5}], "records": []})
        assert any("name must be" in e for e in errors)

    def test_field_max_len_not_int(self):
        errors = validate_mail_merge_data(
            {"fields": [{"name": "A", "max_len": "five"}], "records": []}
        )
        assert any("max_len must be an integer" in e for e in errors)

    def test_field_max_len_zero(self):
        errors = validate_mail_merge_data(
            {"fields": [{"name": "A", "max_len": 0}], "records": []}
        )
        assert any("max_len must be between" in e for e in errors)

    def test_field_max_len_too_large(self):
        errors = validate_mail_merge_data(
            {"fields": [{"name": "A", "max_len": MAX_FIELD_DATA_LEN + 1}], "records": []}
        )
        assert any("max_len must be between" in e for e in errors)

    def test_too_many_records(self):
        fields = [{"name": "A", "max_len": 5}]
        records = [["x"]] * (MAX_RECORDS + 1)
        errors = validate_mail_merge_data({"fields": fields, "records": records})
        assert any("record count exceeds" in e for e in errors)

    def test_record_not_a_list(self):
        errors = validate_mail_merge_data(
            {"fields": [{"name": "A", "max_len": 5}], "records": ["bad"]}
        )
        assert any("must be a list" in e for e in errors)

    def test_record_wrong_field_count(self):
        errors = validate_mail_merge_data(
            {"fields": [{"name": "A", "max_len": 5}], "records": [["a", "b"]]}
        )
        assert any("must contain" in e for e in errors)

    def test_record_value_not_string(self):
        errors = validate_mail_merge_data(
            {"fields": [{"name": "A", "max_len": 5}], "records": [[123]]}
        )
        assert any("must be a string" in e for e in errors)

    def test_record_value_exceeds_max_len(self):
        errors = validate_mail_merge_data(
            {"fields": [{"name": "A", "max_len": 3}], "records": [["toolong"]]}
        )
        assert any("exceeds max_len" in e for e in errors)

    def test_from_dict_raises_on_invalid(self):
        with pytest.raises(ValueError):
            MailMergeDB.from_dict("not a dict")

    def test_from_dict_raises_with_joined_errors(self):
        with pytest.raises(ValueError, match="JSON object"):
            MailMergeDB.from_dict(42)


# =====================================================================
# File I/O — save_mail_merge_db / load_mail_merge_db
# =====================================================================


class TestFileIO:
    def test_save_creates_file(self, tmp_path):
        db = _simple_db([("Name", 10)], [["Alice"]])
        path = tmp_path / "test.mm"
        save_mail_merge_db(db, path)
        assert path.exists()

    def test_save_writes_valid_json(self, tmp_path):
        db = _simple_db([("Name", 10)], [["Alice"]])
        path = tmp_path / "test.mm"
        save_mail_merge_db(db, path)
        data = json.loads(path.read_text())
        assert data["records"] == [["Alice"]]

    def test_load_restores_data(self, tmp_path):
        db = _simple_db([("Name", 10), ("Age", 3)], [["Bob", "42"]])
        path = tmp_path / "test.mm"
        save_mail_merge_db(db, path)

        loaded = load_mail_merge_db(path)
        assert len(loaded.fields) == 2
        assert loaded.fields[0].name == "Name"
        assert loaded.fields[1].max_len == 3
        assert loaded.records == [["Bob", "42"]]

    def test_load_sets_filename(self, tmp_path):
        db = _simple_db([("X", 5)], [])
        path = tmp_path / "mydb.mm"
        save_mail_merge_db(db, path)
        loaded = load_mail_merge_db(path)
        assert loaded.filename == str(path)

    def test_load_nonexistent_raises(self, tmp_path):
        with pytest.raises(OSError):
            load_mail_merge_db(tmp_path / "nope.mm")

    def test_load_invalid_json_raises(self, tmp_path):
        path = tmp_path / "bad.mm"
        path.write_text("not json at all")
        with pytest.raises(Exception):  # json.JSONDecodeError
            load_mail_merge_db(path)

    def test_load_invalid_structure_raises(self, tmp_path):
        path = tmp_path / "bad.mm"
        path.write_text(json.dumps({"fields": "wrong", "records": []}))
        with pytest.raises(ValueError):
            load_mail_merge_db(path)

    def test_roundtrip_many_records(self, tmp_path):
        db = _simple_db([("V", 5)], [[f"r{i:03}"] for i in range(100)])
        path = tmp_path / "big.mm"
        save_mail_merge_db(db, path)
        loaded = load_mail_merge_db(path)
        assert len(loaded.records) == 100
        assert loaded.records[99] == ["r099"]

    def test_roundtrip_preserves_empty_strings(self, tmp_path):
        db = _simple_db([("A", 5), ("B", 5)], [["", ""], ["x", ""]])
        path = tmp_path / "blanks.mm"
        save_mail_merge_db(db, path)
        loaded = load_mail_merge_db(path)
        assert loaded.records[0] == ["", ""]
        assert loaded.records[1] == ["x", ""]


# =====================================================================
# inspect_mail_merge_db
# =====================================================================


class TestInspect:
    def test_basic_inspect(self):
        db = _simple_db([("Name", 10), ("City", 15)], [["A", "B"], ["C", "D"]])
        db.filename = "test.mm"
        info = inspect_mail_merge_db(db)
        assert info["filename"] == "test.mm"
        assert info["record_count"] == 2
        assert info["records_free"] == MAX_RECORDS - 2
        assert info["field_count"] == 2
        assert len(info["fields"]) == 2

    def test_inspect_field_info(self):
        db = _simple_db([("Zip", 5)], [])
        info = inspect_mail_merge_db(db)
        f = info["fields"][0]
        assert f["index"] == 1
        assert f["name"] == "Zip"
        assert f["max_len"] == 5

    def test_inspect_empty_db(self):
        db = MailMergeDB()
        info = inspect_mail_merge_db(db)
        assert info["record_count"] == 0
        assert info["records_free"] == MAX_RECORDS
        assert info["field_count"] == len(DEFAULT_FIELDS)


# =====================================================================
# apply_mail_merge_to_buffer
# =====================================================================


class TestApplyMailMergeToBuffer:
    def test_single_field_substitution(self):
        db = _simple_db([("Name", 10)], [["Alice"]])
        buf = [f"Hello {MERGE}1!"]
        result = apply_mail_merge_to_buffer(buf, db)
        assert result == ["Hello Alice!"]

    def test_multiple_fields(self):
        db = _simple_db([("First", 10), ("Last", 10)], [["Jane", "Doe"]])
        buf = [f"Dear {MERGE}1 {MERGE}2,"]
        result = apply_mail_merge_to_buffer(buf, db)
        assert result == ["Dear Jane Doe,"]

    def test_multi_digit_field(self):
        fields = [(f"F{i}", 10) for i in range(1, 16)]
        values = [f"v{i}" for i in range(1, 16)]
        db = _simple_db(fields, [values])
        buf = [f"Last={MERGE}15"]
        result = apply_mail_merge_to_buffer(buf, db)
        assert result == ["Last=v15"]

    def test_out_of_range_field(self):
        db = _simple_db([("A", 5)], [["x"]])
        buf = [f"Bad={MERGE}99"]
        result = apply_mail_merge_to_buffer(buf, db)
        assert result == ["Bad=<<@99>>"]

    def test_merge_marker_without_digits(self):
        db = _simple_db([("A", 5)], [["x"]])
        buf = [f"Bare{MERGE}end"]
        result = apply_mail_merge_to_buffer(buf, db)
        # \x11 with no digits following — the original char is emitted
        assert result == [f"Bare{MERGE}end"]

    def test_no_records_returns_copy(self):
        db = _simple_db([("A", 5)], [])
        buf = [f"Hello {MERGE}1"]
        result = apply_mail_merge_to_buffer(buf, db)
        assert result == buf
        assert result is not buf  # should be a copy

    def test_uses_first_record_only(self):
        db = _simple_db([("A", 10)], [["first"], ["second"]])
        buf = [f"Val={MERGE}1"]
        result = apply_mail_merge_to_buffer(buf, db)
        assert result == ["Val=first"]

    def test_plain_buffer_unchanged(self):
        db = _simple_db([("A", 5)], [["x"]])
        buf = ["No merge markers here", "Just plain text"]
        result = apply_mail_merge_to_buffer(buf, db)
        assert result == buf

    def test_empty_field_value(self):
        db = _simple_db([("A", 5)], [[""]])
        buf = [f"Before{MERGE}1After"]
        result = apply_mail_merge_to_buffer(buf, db)
        assert result == ["BeforeAfter"]

    def test_multiple_lines(self):
        db = _simple_db([("Name", 10)], [["World"]])
        buf = [f"Hello {MERGE}1", "plain line", f"Bye {MERGE}1"]
        result = apply_mail_merge_to_buffer(buf, db)
        assert result == ["Hello World", "plain line", "Bye World"]

    def test_adjacent_merge_markers(self):
        db = _simple_db([("A", 5), ("B", 5)], [["X", "Y"]])
        buf = [f"{MERGE}1{MERGE}2"]
        result = apply_mail_merge_to_buffer(buf, db)
        assert result == ["XY"]

    def test_field_zero_out_of_range(self):
        db = _simple_db([("A", 5)], [["x"]])
        buf = [f"Zero={MERGE}0"]
        result = apply_mail_merge_to_buffer(buf, db)
        assert result == ["Zero=<<@0>>"]


# =====================================================================
# _apply_record (print_screen helper)
# =====================================================================


class TestApplyRecord:
    def test_basic_substitution(self):
        buf = [f"Dear {MERGE}1,"]
        result = _apply_record(buf, ["Alice"])
        assert result == ["Dear Alice,"]

    def test_out_of_range(self):
        buf = [f"Bad {MERGE}5"]
        result = _apply_record(buf, ["only_one"])
        assert result == ["Bad <<@5>>"]

    def test_no_digits_after_marker(self):
        buf = [f"Bare{MERGE}text"]
        result = _apply_record(buf, ["x"])
        assert result == ["Bare<<@?>>text"]

    def test_preserves_non_merge_content(self):
        buf = ["Hello World", f"Name: {MERGE}1"]
        result = _apply_record(buf, ["Bob"])
        assert result[0] == "Hello World"
        assert result[1] == "Name: Bob"


# =====================================================================
# _buffer_has_merge_markers
# =====================================================================


class TestBufferHasMergeMarkers:
    def test_no_markers(self):
        assert not _buffer_has_merge_markers(["plain text", "more text"])

    def test_has_marker(self):
        assert _buffer_has_merge_markers([f"Hello {MERGE}1"])

    def test_empty_buffer(self):
        assert not _buffer_has_merge_markers([])

    def test_marker_alone(self):
        assert _buffer_has_merge_markers([MERGE])


# =====================================================================
# _render_with_mail_merge
# =====================================================================


class TestRenderWithMailMerge:
    def test_no_markers_no_db(self):
        buf = ["Hello"]
        lines = _render_with_mail_merge(buf, _fmt(), None)
        joined = "\n".join(lines)
        assert "Hello" in joined

    def test_markers_but_no_db(self):
        buf = [f"Dear {MERGE}1"]
        lines = _render_with_mail_merge(buf, _fmt(), None)
        joined = "\n".join(lines)
        assert "<<@1>>" in joined

    def test_markers_with_empty_db(self):
        db = _simple_db([("Name", 10)], [])
        buf = [f"Dear {MERGE}1"]
        lines = _render_with_mail_merge(buf, _fmt(), db)
        joined = "\n".join(lines)
        assert "<<@1>>" in joined

    def test_markers_with_one_record(self):
        db = _simple_db([("Name", 10)], [["Alice"]])
        buf = [f"Dear {MERGE}1"]
        lines = _render_with_mail_merge(buf, _fmt(), db)
        joined = "\n".join(lines)
        assert "Alice" in joined
        assert "<<@" not in joined

    def test_markers_with_two_records(self):
        db = _simple_db([("Name", 10)], [["Alice"], ["Bob"]])
        buf = [f"Dear {MERGE}1"]
        lines = _render_with_mail_merge(buf, _fmt(), db)
        joined = "\n".join(lines)
        assert "Alice" in joined
        assert "Bob" in joined
        assert "Record 2" in joined

    def test_no_markers_with_db_skips_merge(self):
        db = _simple_db([("Name", 10)], [["Alice"], ["Bob"]])
        buf = ["No merge here"]
        lines = _render_with_mail_merge(buf, _fmt(), db)
        joined = "\n".join(lines)
        assert "No merge here" in joined
        assert "Record 2" not in joined


# =====================================================================
# Markdown export with mail merge
# =====================================================================


class TestMarkdownMailMerge:
    def test_no_db_shows_placeholder(self):
        buf = [f"Dear {MERGE}1"]
        result = export_markdown(buf, _fmt())
        assert "{{field1}}" in result

    def test_with_db_substitutes(self):
        db = _simple_db([("Name", 10)], [["Alice"], ["Bob"]])
        buf = [f"Dear {MERGE}1"]
        result = export_markdown(buf, _fmt(), db)
        assert "Alice" in result
        assert "Bob" in result
        assert "---" in result  # separator between copies

    def test_single_record_no_separator(self):
        db = _simple_db([("Name", 10)], [["Alice"]])
        buf = [f"Dear {MERGE}1"]
        result = export_markdown(buf, _fmt(), db)
        assert "Alice" in result
        # The --- from page breaks shouldn't appear between records
        # when there's only one record
        lines = result.strip().split("\n")
        assert lines[0].strip() == "Dear Alice"

    def test_no_markers_db_ignored(self):
        db = _simple_db([("Name", 10)], [["Alice"]])
        buf = ["No merge"]
        result = export_markdown(buf, _fmt(), db)
        assert "No merge" in result
        assert "Alice" not in result

    def test_multi_digit_field_in_markdown(self):
        fields = [(f"F{i}", 10) for i in range(1, 12)]
        vals = [f"val{i}" for i in range(1, 12)]
        db = _simple_db(fields, [vals])
        buf = [f"Eleventh={MERGE}11"]
        result = export_markdown(buf, _fmt(), db)
        assert "val11" in result


# =====================================================================
# PostScript export with mail merge
# =====================================================================


class TestPostScriptMailMerge:
    def test_with_db_substitutes(self):
        db = _simple_db([("Name", 10)], [["Alice"], ["Bob"]])
        buf = [f"Dear {MERGE}1"]
        result = export_postscript(buf, _fmt(), db)
        assert "Alice" in result
        assert "Bob" in result

    def test_no_markers_db_ignored(self):
        db = _simple_db([("Name", 10)], [["Alice"]])
        buf = ["No merge"]
        result = export_postscript(buf, _fmt(), db)
        assert "No merge" in result
        assert "Alice" not in result

    def test_no_db_shows_placeholder(self):
        buf = [f"Dear {MERGE}3"]
        result = export_postscript(buf, _fmt())
        assert "<<@3>>" in result
