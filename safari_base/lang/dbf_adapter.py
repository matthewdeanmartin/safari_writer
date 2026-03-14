"""Adapter wrapping the dbf library for table operations.

This isolates the dbf dependency so it can be swapped later.
"""

from __future__ import annotations

import datetime
import os
import shutil
from pathlib import Path
from typing import Any

import dbf  # type: ignore[import-untyped]

# Map single-char type codes to dbf field spec format
_TYPE_MAP = {
    "C": "C",  # Character
    "N": "N",  # Numeric
    "D": "D",  # Date
    "L": "L",  # Logical
    "M": "M",  # Memo
}


class TableHandle:
    """Wraps a single open dbf.Table with record-pointer semantics."""

    def __init__(self, table: dbf.Table, alias: str, exclusive: bool = False) -> None:
        self.table = table
        self.alias = alias
        self.exclusive = exclusive
        self._recno = 0  # 0-based internally
        self._eof = len(table) == 0
        self._bof = True
        self._filter_expr: Any | None = None
        self._deleted_on = False
        self._found = False
        self._locate_condition: Any | None = None  # stored for CONTINUE
        self._locate_recno = 0
        # In-memory index
        self._order: list[int] | None = None
        self._order_tag: str = ""

    @property
    def record_count(self) -> int:
        return len(self.table)

    @property
    def recno(self) -> int:
        """1-based record number (dBASE convention)."""
        return self._recno + 1

    @property
    def eof(self) -> bool:
        return self._eof

    @property
    def bof(self) -> bool:
        return self._bof

    @property
    def found(self) -> bool:
        return self._found

    def field_names(self) -> list[str]:
        return list(self.table.field_names)

    def field_info(self) -> list[tuple[str, str, int, int]]:
        """Return (name, type_char, width, decimals) for each field."""
        result = []
        for name in self.table.field_names:
            info = self.table.field_info(name)
            # dbf.field_info returns FieldInfo(type_int, size, decimal, class)
            # type_int is the ASCII code: 67=C, 78=N, 68=D, 76=L, 77=M
            type_char = chr(info[0]) if isinstance(info[0], int) else str(info[0])
            result.append((name, type_char, info[1], info[2]))
        return result

    def go_top(self) -> None:
        if self.record_count == 0:
            self._eof = True
            self._bof = True
            return
        self._recno = 0
        self._bof = True
        self._eof = False

    def go_bottom(self) -> None:
        if self.record_count == 0:
            self._eof = True
            self._bof = True
            return
        self._recno = self.record_count - 1
        self._bof = False
        self._eof = False

    def go_record(self, n: int) -> None:
        """Go to 1-based record number."""
        if n < 1 or n > self.record_count:
            from safari_base.lang.errors import DBaseError

            raise DBaseError(f"Record number {n} out of range (1-{self.record_count})")
        self._recno = n - 1
        self._bof = self._recno == 0
        self._eof = False

    def skip(self, count: int = 1) -> None:
        if self.record_count == 0:
            self._eof = True
            return
        new_pos = self._recno + count
        if new_pos >= self.record_count:
            self._recno = self.record_count - 1
            self._eof = True
        elif new_pos < 0:
            self._recno = 0
            self._bof = True
        else:
            self._recno = new_pos
            self._eof = False
            self._bof = new_pos == 0

    def current_record(self) -> dbf.Record | None:
        if self._eof or self.record_count == 0:
            return None
        return self.table[self._recno]

    def get_field(self, field_name: str) -> Any:
        """Get field value from current record."""
        rec = self.current_record()
        if rec is None:
            from safari_base.lang.errors import NoTableError

            raise NoTableError("No current record (EOF)")
        name_upper = field_name.upper()
        for fn in self.table.field_names:
            if fn.upper() == name_upper:
                val = rec[fn]
                # Normalize dbf types to Python types
                if isinstance(val, str):
                    return val
                if isinstance(val, (int, float)):
                    return val
                if isinstance(val, datetime.date):
                    return val
                if isinstance(val, bool):
                    return val
                if val is None:
                    return ""
                return str(val)
        from safari_base.lang.errors import FieldNotFoundError

        raise FieldNotFoundError(field_name, self.alias)

    def set_field(self, field_name: str, value: Any) -> None:
        """Set field value on current record."""
        rec = self.current_record()
        if rec is None:
            from safari_base.lang.errors import NoTableError

            raise NoTableError("No current record (EOF)")
        name_upper = field_name.upper()
        for fn in self.table.field_names:
            if fn.upper() == name_upper:
                dbf.write(rec, **{fn: value})
                return
        from safari_base.lang.errors import FieldNotFoundError

        raise FieldNotFoundError(field_name, self.alias)

    def has_field(self, field_name: str) -> bool:
        name_upper = field_name.upper()
        return any(fn.upper() == name_upper for fn in self.table.field_names)

    def append_blank(self) -> int:
        """Append a blank record, return 1-based recno."""
        self.table.append()
        self._recno = self.record_count - 1
        self._eof = False
        self._bof = self._recno == 0
        return self.recno

    def delete_current(self) -> None:
        rec = self.current_record()
        if rec is not None:
            dbf.delete(rec)

    def recall_current(self) -> None:
        rec = self.current_record()
        if rec is not None:
            dbf.undelete(rec)

    def is_deleted(self) -> bool:
        rec = self.current_record()
        if rec is None:
            return False
        return bool(dbf.is_deleted(rec))

    def pack(self) -> int:
        """Remove all deleted records. Returns count removed."""
        before = self.record_count
        self.table.pack()
        after = self.record_count
        if self._recno >= after:
            self._recno = max(0, after - 1)
        if after == 0:
            self._eof = True
        return before - after

    def zap(self) -> int:
        """Remove all records."""
        count = self.record_count
        self.table.zap()
        self._recno = 0
        self._eof = True
        self._bof = True
        return count

    def close(self) -> None:
        self.table.close()


def create_table(path: str, columns: list[tuple[str, str, int, int]]) -> dbf.Table:
    """Create a new DBF table.

    columns: list of (name, type_char, width, decimals)
    """
    field_specs = []
    for name, type_char, width, decimals in columns:
        tc = _TYPE_MAP.get(type_char.upper(), "C")
        if tc == "N":
            # dbf library always requires decimals for N fields
            field_specs.append(f"{name} {tc}({width},{decimals})")
        elif tc == "C":
            field_specs.append(f"{name} {tc}({width})")
        elif tc == "D":
            field_specs.append(f"{name} {tc}")
        elif tc == "L":
            field_specs.append(f"{name} {tc}")
        elif tc == "M":
            field_specs.append(f"{name} {tc}")
        else:
            field_specs.append(f"{name} C({width})")

    table = dbf.Table(path, "; ".join(field_specs), dbf_type="db3")
    table.open(dbf.READ_WRITE)
    return table


def open_table(path: str, exclusive: bool = False) -> dbf.Table:
    """Open an existing DBF table."""
    table = dbf.Table(path)
    table.open(dbf.READ_WRITE)
    return table


def copy_structure(
    source_handle: TableHandle, target_path: str, extended: bool = False
) -> dbf.Table:
    """Copy the structure of an open table to a new file."""
    if extended:
        # Create a structure-extended table (field definitions as records)
        cols = [
            ("FIELD_NAME", "C", 11, 0),
            ("FIELD_TYPE", "C", 1, 0),
            ("FIELD_LEN", "N", 3, 0),
            ("FIELD_DEC", "N", 3, 0),
        ]
        table = create_table(target_path, cols)
        handle = TableHandle(table, "struct")
        for name, type_char, width, decimals in source_handle.field_info():
            handle.append_blank()
            handle.set_field("FIELD_NAME", name)
            handle.set_field("FIELD_TYPE", type_char)
            handle.set_field("FIELD_LEN", width)
            handle.set_field("FIELD_DEC", decimals)
        return table
    else:
        # Copy just the structure (empty table)
        field_info = source_handle.field_info()
        cols = [(name, tc, w, d) for name, tc, w, d in field_info]
        return create_table(target_path, cols)
