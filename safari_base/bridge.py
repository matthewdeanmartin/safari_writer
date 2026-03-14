"""Data bridge between Safari Writer mail-merge (JSON) and Safari Base (SQLite)."""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from safari_base.database import BaseSession
    from safari_writer.mail_merge_db import FieldDef, MailMergeDB

__all__ = [
    "mail_merge_to_session",
    "session_to_mail_merge",
]


def mail_merge_to_session(db: MailMergeDB) -> BaseSession:
    """Convert an in-memory MailMergeDB into a BaseSession backed by SQLite.

    The resulting session uses an in-memory SQLite database populated with
    the mail-merge schema and records.
    """
    from safari_base.database import (
        DEFAULT_ADDRESS_SCHEMA,
        DEFAULT_TABLE_NAME,
        BaseSession,
        _quote_identifier,
    )

    connection = sqlite3.connect(":memory:")

    # Build schema from mail-merge fields
    schema = _fields_to_schema(db.fields, DEFAULT_ADDRESS_SCHEMA)
    column_sql = ", ".join(
        f'{_quote_identifier(name)} TEXT NOT NULL DEFAULT ""' for name, _width in schema
    )
    connection.execute(
        f"CREATE TABLE {_quote_identifier(DEFAULT_TABLE_NAME)} ({column_sql})"
    )

    # Insert records
    columns = [name for name, _width in schema]
    if db.records:
        quoted_columns = ", ".join(_quote_identifier(c) for c in columns)
        placeholders = ", ".join("?" for _ in columns)
        for record in db.records:
            # Pad or truncate to match column count
            padded = list(record) + [""] * max(0, len(columns) - len(record))
            connection.execute(
                f"INSERT INTO {_quote_identifier(DEFAULT_TABLE_NAME)} "
                f"({quoted_columns}) VALUES ({placeholders})",
                padded[: len(columns)],
            )
        connection.commit()

    return BaseSession(
        connection=connection,
        database_path=None,
        current_table=DEFAULT_TABLE_NAME,
    )


def session_to_mail_merge(
    session: BaseSession, original: MailMergeDB | None = None
) -> MailMergeDB:
    """Convert the current table of a BaseSession back into a MailMergeDB.

    If *original* is provided, field names are preserved from the original
    where the schema columns match by position.  Otherwise, column names
    from the SQLite table are used directly.
    """
    from safari_base.database import DEFAULT_ADDRESS_SCHEMA
    from safari_writer.mail_merge_db import FieldDef, MailMergeDB

    columns = session.current_columns()
    schema = _schema_for_columns(columns, DEFAULT_ADDRESS_SCHEMA)

    # Build field definitions — prefer original names when available
    fields: list[FieldDef] = []
    for idx, (col_name, width) in enumerate(schema):
        if original and idx < len(original.fields):
            fields.append(
                FieldDef(original.fields[idx].name, original.fields[idx].max_len)
            )
        else:
            fields.append(FieldDef(col_name, width))

    # Read all records
    count = session.record_count()
    rows = session.browse_rows(limit=count, offset=0)
    records = [values for _rowid, values in rows]

    db = MailMergeDB(fields=fields, records=records)
    if original:
        db.filename = original.filename
    return db


def _fields_to_schema(
    fields: list[FieldDef],
    default_schema: list[tuple[str, int]],
) -> list[tuple[str, int]]:
    """Map MailMergeDB fields to Safari Base column schema."""
    schema: list[tuple[str, int]] = []
    for idx, fdef in enumerate(fields):
        if idx < len(default_schema):
            col_name = default_schema[idx][0]
        else:
            col_name = fdef.name.upper().replace(" ", "_")[:12]
        schema.append((col_name, fdef.max_len))
    return schema


def _schema_for_columns(
    columns: list[str],
    default_schema: list[tuple[str, int]],
) -> list[tuple[str, int]]:
    """Build a schema with widths from default_schema where available."""
    width_map = dict(default_schema)
    return [(col, width_map.get(col, 20)) for col in columns]
