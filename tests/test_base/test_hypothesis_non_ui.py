"""Property-based tests for non-UI Safari Base helpers."""

from __future__ import annotations

import sqlite3
import string

from hypothesis import given
from hypothesis import strategies as st

from safari_base.bridge import _fields_to_schema, _schema_for_columns
from safari_base.database import (
    DEFAULT_ADDRESS_SCHEMA,
    BaseSession,
    _quote_identifier,
    list_tables,
)
from safari_writer.mail_merge_db import FieldDef

IDENTIFIER_CHARS = string.ascii_letters + string.digits + "_"
IDENTIFIER_TEXT = st.text(alphabet=IDENTIFIER_CHARS, min_size=1, max_size=12).filter(
    lambda value: value.strip() != ""
    and not value.lower().startswith("sqlite_")
    and '"' not in value
)
FIELD_NAME_TEXT = st.text(
    alphabet=string.ascii_letters + string.digits + "_ ",
    min_size=1,
    max_size=12,
).filter(lambda value: value.strip() != "" and '"' not in value)


@st.composite
def unique_identifiers(draw: st.DrawFn) -> list[str]:
    names = draw(
        st.lists(IDENTIFIER_TEXT, min_size=1, max_size=8, unique_by=str.casefold)
    )
    return names


@st.composite
def field_defs(draw: st.DrawFn) -> list[FieldDef]:
    names = draw(
        st.lists(
            FIELD_NAME_TEXT,
            min_size=1,
            max_size=8,
            unique_by=lambda value: value.strip().casefold(),
        )
    )
    widths = draw(
        st.lists(
            st.integers(min_value=1, max_value=255),
            min_size=len(names),
            max_size=len(names),
        )
    )
    return [FieldDef(name.strip(), width) for name, width in zip(names, widths)]


def _mixed_case(text: str) -> str:
    return "".join(
        ch.upper() if index % 2 == 0 else ch.lower() for index, ch in enumerate(text)
    )


@given(unique_identifiers())
def test_list_tables_returns_user_tables_in_case_insensitive_order(
    names: list[str],
) -> None:
    connection = sqlite3.connect(":memory:")
    try:
        for index, name in enumerate(names):
            autoincrement = " PRIMARY KEY AUTOINCREMENT" if index == 0 else ""
            connection.execute(
                f"CREATE TABLE {_quote_identifier(name)} (id INTEGER{autoincrement})"
            )

        assert list_tables(connection) == sorted(names, key=str.casefold)
    finally:
        connection.close()


@given(unique_identifiers(), st.integers(min_value=0, max_value=7))
def test_resolve_table_name_is_case_insensitive(
    names: list[str], requested_index: int
) -> None:
    connection = sqlite3.connect(":memory:")
    try:
        for name in names:
            connection.execute(f"CREATE TABLE {_quote_identifier(name)} (value TEXT)")

        session = BaseSession(
            connection=connection, database_path=None, current_table=names[0]
        )
        requested_name = names[requested_index % len(names)]
        variant = f"  {_mixed_case(requested_name)}  "

        assert session.resolve_table_name(variant) == requested_name
    finally:
        connection.close()


@given(field_defs())
def test_fields_to_schema_preserves_widths_and_default_names(
    fields: list[FieldDef],
) -> None:
    schema = _fields_to_schema(fields, DEFAULT_ADDRESS_SCHEMA)

    assert len(schema) == len(fields)
    assert [width for _name, width in schema] == [field.max_len for field in fields]
    for index, (name, _width) in enumerate(schema):
        if index < len(DEFAULT_ADDRESS_SCHEMA):
            assert name == DEFAULT_ADDRESS_SCHEMA[index][0]
        else:
            assert name == fields[index].name.upper().replace(" ", "_")[:12]


@given(st.lists(IDENTIFIER_TEXT, min_size=1, max_size=12))
def test_schema_for_columns_preserves_order_and_assigns_widths(
    columns: list[str],
) -> None:
    normalized_columns = [
        column.strip().upper().replace(" ", "_")[:12] for column in columns
    ]
    schema = _schema_for_columns(normalized_columns, DEFAULT_ADDRESS_SCHEMA)
    width_map = dict(DEFAULT_ADDRESS_SCHEMA)

    assert [name for name, _width in schema] == normalized_columns
    for name, width in schema:
        assert width == width_map.get(name, 20)
