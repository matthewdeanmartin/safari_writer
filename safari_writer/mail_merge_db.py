"""Reusable mail-merge data model and file helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import cast

from safari_writer.typed import MailMergeData, MailMergeFieldInfo, MailMergeInspectInfo

__all__ = [
    "DEFAULT_FIELDS",
    "FieldDef",
    "MAX_FIELD_DATA_LEN",
    "MAX_FIELD_NAME_LEN",
    "MAX_FIELDS",
    "MAX_RECORDS",
    "MailMergeDB",
    "apply_mail_merge_to_buffer",
    "inspect_mail_merge_db",
    "load_mail_merge_db",
    "save_mail_merge_db",
    "validate_mail_merge_data",
]

MAX_FIELDS = 15
MAX_RECORDS = 255
MAX_FIELD_NAME_LEN = 12
MAX_FIELD_DATA_LEN = 20

DEFAULT_FIELDS: list[tuple[str, int]] = [
    ("Last Name", 20),
    ("First Name", 20),
    ("Company", 20),
    ("Address", 20),
    ("City", 20),
    ("State", 10),
    ("Zipcode", 10),
    ("Phone", 15),
    ("Salutation", 20),
    ("Title", 20),
    ("Department", 20),
    ("Country", 20),
    ("Email", 20),
    ("Fax", 15),
    ("Notes", 20),
]


@dataclass
class FieldDef:
    name: str
    max_len: int = MAX_FIELD_DATA_LEN


@dataclass
class MailMergeDB:
    """In-memory mail merge database."""

    fields: list[FieldDef] = field(
        default_factory=lambda: [
            FieldDef(name, width) for name, width in DEFAULT_FIELDS
        ]
    )
    records: list[list[str]] = field(default_factory=list)
    filename: str = ""

    @property
    def records_free(self) -> int:
        return MAX_RECORDS - len(self.records)

    def new_record(self) -> list[str]:
        return [""] * len(self.fields)

    def to_dict(self) -> MailMergeData:
        return {
            "fields": [
                {"name": field.name, "max_len": field.max_len} for field in self.fields
            ],
            "records": self.records,
        }

    @classmethod
    def from_dict(cls, data: object) -> "MailMergeDB":
        errors = validate_mail_merge_data(data)
        if errors:
            raise ValueError("; ".join(errors))
        validated_data = cast(MailMergeData, data)
        db = cls.__new__(cls)
        db.fields = [
            FieldDef(item["name"], item["max_len"]) for item in validated_data["fields"]
        ]
        db.records = [list(record) for record in validated_data["records"]]
        db.filename = ""
        return db

    def schema_matches(self, other: "MailMergeDB") -> bool:
        if len(self.fields) != len(other.fields):
            return False
        return all(
            left.name == right.name and left.max_len == right.max_len
            for left, right in zip(self.fields, other.fields)
        )

    def apply_subset(self, field_idx: int, low: str, high: str) -> list[int]:
        results: list[int] = []
        for index, record in enumerate(self.records):
            value = record[field_idx] if field_idx < len(record) else ""
            if low.lower() <= value.lower() <= high.lower():
                results.append(index)
        return results


def validate_mail_merge_data(data: object) -> list[str]:
    """Return structural validation errors for mail-merge JSON data."""

    if not isinstance(data, dict):
        return ["database root must be a JSON object"]

    fields = data.get("fields")
    records = data.get("records")
    errors: list[str] = []

    if not isinstance(fields, list):
        errors.append("'fields' must be a list")
    if not isinstance(records, list):
        errors.append("'records' must be a list")
    if errors:
        return errors
    assert isinstance(fields, list)
    assert isinstance(records, list)

    if not 1 <= len(fields) <= MAX_FIELDS:
        errors.append(f"field count must be between 1 and {MAX_FIELDS}")

    normalized_fields: list[tuple[str, int]] = []
    for index, field_data in enumerate(fields, start=1):
        if not isinstance(field_data, dict):
            errors.append(f"field {index} must be an object")
            continue
        name = field_data.get("name")
        max_len = field_data.get("max_len")
        if not isinstance(name, str) or not name.strip():
            errors.append(f"field {index} name must be a non-empty string")
        elif len(name) > MAX_FIELD_NAME_LEN:
            errors.append(f"field {index} name exceeds {MAX_FIELD_NAME_LEN} characters")
        if not isinstance(max_len, int):
            errors.append(f"field {index} max_len must be an integer")
        elif not 1 <= max_len <= MAX_FIELD_DATA_LEN:
            errors.append(
                f"field {index} max_len must be between 1 and {MAX_FIELD_DATA_LEN}"
            )
        if isinstance(name, str) and isinstance(max_len, int):
            normalized_fields.append((name, max_len))

    if len(records) > MAX_RECORDS:
        errors.append(f"record count exceeds maximum of {MAX_RECORDS}")

    field_count = len(fields)
    for record_index, record in enumerate(records, start=1):
        if not isinstance(record, list):
            errors.append(f"record {record_index} must be a list")
            continue
        if len(record) != field_count:
            errors.append(f"record {record_index} must contain {field_count} values")
            continue
        for value_index, value in enumerate(record, start=1):
            if not isinstance(value, str):
                errors.append(
                    f"record {record_index} field {value_index} must be a string"
                )
                continue
            if value_index <= len(normalized_fields):
                _, max_len = normalized_fields[value_index - 1]
                if len(value) > max_len:
                    errors.append(
                        f"record {record_index} field {value_index} exceeds max_len {max_len}"
                    )

    return errors


def load_mail_merge_db(path: Path, encoding: str = "utf-8") -> MailMergeDB:
    """Load and validate a mail-merge database from JSON."""

    data = json.loads(path.read_text(encoding=encoding))
    db = MailMergeDB.from_dict(data)
    db.filename = str(path)
    return db


def save_mail_merge_db(db: MailMergeDB, path: Path, encoding: str = "utf-8") -> None:
    """Write a mail-merge database to disk."""

    path.write_text(json.dumps(db.to_dict(), indent=2), encoding=encoding)


def inspect_mail_merge_db(db: MailMergeDB) -> MailMergeInspectInfo:
    """Build a structured description of a database."""

    field_info: list[MailMergeFieldInfo] = [
        {"index": index, "name": field.name, "max_len": field.max_len}
        for index, field in enumerate(db.fields, start=1)
    ]
    return {
        "filename": db.filename,
        "record_count": len(db.records),
        "records_free": db.records_free,
        "field_count": len(db.fields),
        "fields": field_info,
    }


def apply_mail_merge_to_buffer(buffer: list[str], db: MailMergeDB) -> list[str]:
    """Resolve merge-field markers in a document buffer using the first DB record."""

    if not db.records:
        return list(buffer)
    record = db.records[0]
    merged: list[str] = []
    for line in buffer:
        out: list[str] = []
        index = 0
        while index < len(line):
            char = line[index]
            if char == "\x11":
                index += 1
                digits: list[str] = []
                while index < len(line) and line[index].isdigit():
                    digits.append(line[index])
                    index += 1
                if digits:
                    field_number = int("".join(digits))
                    if 1 <= field_number <= len(record):
                        out.append(record[field_number - 1])
                    else:
                        out.append(f"<<@{field_number}>>")
                    continue
                out.append(char)
                continue
            out.append(char)
            index += 1
        merged.append("".join(out))
    return merged
