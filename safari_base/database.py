"""SQLite bootstrap and browse helpers for Safari Base."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from safari_writer.mail_merge_db import DEFAULT_FIELDS

__all__ = [
    "DEFAULT_ADDRESS_SCHEMA",
    "BaseSession",
    "ensure_database",
    "list_tables",
]

DEFAULT_ADDRESS_SCHEMA: list[tuple[str, int]] = [
    ("LAST", DEFAULT_FIELDS[0][1]),
    ("FIRST", DEFAULT_FIELDS[1][1]),
    ("COMPANY", DEFAULT_FIELDS[2][1]),
    ("ADDRESS", DEFAULT_FIELDS[3][1]),
    ("CITY", DEFAULT_FIELDS[4][1]),
    ("STATE", DEFAULT_FIELDS[5][1]),
    ("ZIP", DEFAULT_FIELDS[6][1]),
    ("PHONE", DEFAULT_FIELDS[7][1]),
    ("SALUTE", DEFAULT_FIELDS[8][1]),
    ("TITLE", DEFAULT_FIELDS[9][1]),
    ("DEPT", DEFAULT_FIELDS[10][1]),
    ("COUNTRY", DEFAULT_FIELDS[11][1]),
    ("EMAIL", DEFAULT_FIELDS[12][1]),
    ("FAX", DEFAULT_FIELDS[13][1]),
    ("NOTES", DEFAULT_FIELDS[14][1]),
]

DEFAULT_TABLE_NAME = "ADDRESS"


def _quote_identifier(identifier: str) -> str:
    return f'"{identifier.replace(chr(34), chr(34) * 2)}"'


def list_tables(connection: sqlite3.Connection) -> list[str]:
    """Return user tables in display order."""

    rows = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name COLLATE NOCASE
        """
    ).fetchall()
    return [str(name) for (name,) in rows]


def _create_default_table(connection: sqlite3.Connection) -> None:
    column_sql = ", ".join(
        f'{_quote_identifier(name)} TEXT NOT NULL DEFAULT ""'
        for name, _width in DEFAULT_ADDRESS_SCHEMA
    )
    connection.execute(
        f"CREATE TABLE IF NOT EXISTS {_quote_identifier(DEFAULT_TABLE_NAME)} ({column_sql})"
    )
    connection.commit()


@dataclass
class BaseSession:
    """Mutable SQLite session state for the current Safari Base app."""

    connection: sqlite3.Connection
    database_path: Path | None
    current_table: str

    def table_names(self) -> list[str]:
        return list_tables(self.connection)

    def resolve_table_name(self, table_name: str) -> str:
        """Resolve a table name case-insensitively against the open database."""

        normalized = table_name.strip()
        for existing_name in self.table_names():
            if existing_name.casefold() == normalized.casefold():
                return existing_name
        raise ValueError(f"Unknown table: {table_name}")

    def set_current_table(self, table_name: str) -> None:
        self.current_table = self.resolve_table_name(table_name)

    def current_columns(self) -> list[str]:
        rows = self.connection.execute(
            f"PRAGMA table_info({_quote_identifier(self.current_table)})"
        ).fetchall()
        return [str(row[1]) for row in rows]

    def record_count(self) -> int:
        row = self.connection.execute(
            f"SELECT COUNT(*) FROM {_quote_identifier(self.current_table)}"
        ).fetchone()
        return int(row[0]) if row is not None else 0

    def browse_rows(self, limit: int, offset: int) -> list[tuple[int, list[str]]]:
        rows = self.connection.execute(
            f"SELECT rowid, * FROM {_quote_identifier(self.current_table)} "
            "LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        return [(int(row[0]), [str(value) for value in row[1:]]) for row in rows]

    def append_blank_record(self) -> int:
        return self.append_record([""] * len(self.current_columns()))

    def append_record(self, values: list[str]) -> int:
        columns = self.current_columns()
        if len(values) != len(columns):
            raise ValueError(
                f"Expected {len(columns)} values for table {self.current_table}, got {len(values)}"
            )
        quoted_columns = ", ".join(_quote_identifier(name) for name in columns)
        placeholders = ", ".join("?" for _ in columns)
        cursor = self.connection.execute(
            f"INSERT INTO {_quote_identifier(self.current_table)} "
            f"({quoted_columns}) VALUES ({placeholders})",
            values,
        )
        self.connection.commit()
        rowid = cursor.lastrowid
        if rowid is None:
            raise RuntimeError("SQLite did not return a rowid for the appended record")
        return int(rowid)

    def structure_rows(self) -> list[tuple[str, str]]:
        pragma_rows = self.connection.execute(
            f"PRAGMA table_info({_quote_identifier(self.current_table)})"
        ).fetchall()
        widths = {name: width for name, width in DEFAULT_ADDRESS_SCHEMA}
        results: list[tuple[str, str]] = []
        for row in pragma_rows:
            name = str(row[1])
            col_type = str(row[2] or "TEXT")
            width = widths.get(name, max(8, len(name)))
            results.append((name, f"{col_type}({width})"))
        return results


def ensure_database(database_path: Path | None = None) -> BaseSession:
    """Open or create a Safari Base SQLite database."""

    if database_path is not None:
        database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(database_path)
    else:
        connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    tables = list_tables(connection)
    if not tables:
        _create_default_table(connection)
        tables = list_tables(connection)

    current_table = (
        DEFAULT_TABLE_NAME if DEFAULT_TABLE_NAME in tables else tables[0]
    )
    return BaseSession(
        connection=connection,
        database_path=database_path,
        current_table=current_table,
    )
