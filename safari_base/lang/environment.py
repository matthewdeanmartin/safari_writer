"""Interpreter state: work areas, variables, settings."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from safari_base.lang.dbf_adapter import TableHandle
from safari_base.lang.errors import DBaseError, NoTableError


class Environment:
    """Holds all interpreter state for a dBASE session."""

    MAX_WORK_AREAS = 10

    def __init__(
        self,
        *,
        work_dir: str | Path | None = None,
        default_dir: str | Path | None = None,
        sandbox: str | Path | None = None,
        unsafe: bool = False,
    ) -> None:
        self.work_dir = Path(work_dir or os.getcwd()).resolve()
        self.default_dir = Path(default_dir or self.work_dir).resolve()
        self.sandbox = Path(sandbox).resolve() if sandbox else None
        self.unsafe = unsafe

        # Work areas (1-based, 0 is unused)
        self._work_areas: dict[int, TableHandle | None] = {}
        self._aliases: dict[str, int] = {}
        self._active_area: int = 1

        # Memory variables
        self.variables: dict[str, Any] = {}

        # User-defined functions/procedures (name -> AST node)
        self._user_funcs: dict[str, Any] = {}

        # Settings
        self.deleted_on: bool = False  # SET DELETED OFF by default

        # Output buffer (for ? and LIST etc.)
        self.output: list[str] = []

        # Program call stack
        self._call_stack: list[str] = []

    # -- Work area management ------------------------------------------------

    def current_work_area(self) -> TableHandle | None:
        return self._work_areas.get(self._active_area)

    def require_work_area(self) -> TableHandle:
        wa = self.current_work_area()
        if wa is None:
            raise NoTableError()
        return wa

    @property
    def active_area(self) -> int:
        return self._active_area

    def select_area(self, area: int | str) -> None:
        if isinstance(area, str):
            # Lookup by alias
            alias_upper = area.upper()
            if alias_upper in self._aliases:
                self._active_area = self._aliases[alias_upper]
                return
            # Try as number
            try:
                area = int(area)
            except ValueError:
                raise DBaseError(f"Unknown work area or alias: {alias_upper}")
        if area < 1 or area > self.MAX_WORK_AREAS:
            raise DBaseError(f"Work area {area} out of range (1-{self.MAX_WORK_AREAS})")
        self._active_area = area

    def open_table(self, handle: TableHandle) -> None:
        """Open a table in the current work area."""
        # Close existing table in this area
        existing = self._work_areas.get(self._active_area)
        if existing is not None:
            self._close_area(self._active_area)
        self._work_areas[self._active_area] = handle
        if handle.alias:
            self._aliases[handle.alias.upper()] = self._active_area

    def close_current(self) -> None:
        self._close_area(self._active_area)

    def close_all(self) -> None:
        for area_num in list(self._work_areas.keys()):
            self._close_area(area_num)

    def _close_area(self, area: int) -> None:
        handle = self._work_areas.get(area)
        if handle is not None:
            # Remove alias
            alias_upper = handle.alias.upper() if handle.alias else ""
            if alias_upper and alias_upper in self._aliases:
                del self._aliases[alias_upper]
            handle.close()
            del self._work_areas[area]

    def get_area_by_alias(self, alias: str) -> TableHandle | None:
        area_num = self._aliases.get(alias.upper())
        if area_num is not None:
            return self._work_areas.get(area_num)
        return None

    # -- Path resolution -----------------------------------------------------

    def resolve_dbf_path(self, name: str) -> str:
        """Resolve a table name to a full .dbf path."""
        if os.path.isabs(name):
            p = Path(name)
        else:
            p = self.default_dir / name

        if not p.suffix:
            p = p.with_suffix(".dbf")

        resolved = p.resolve()
        self._check_sandbox(resolved)
        return str(resolved)

    def resolve_path(self, name: str) -> Path:
        """Resolve a general file path."""
        if os.path.isabs(name):
            p = Path(name)
        else:
            p = self.work_dir / name
        resolved = p.resolve()
        self._check_sandbox(resolved)
        return resolved

    def _check_sandbox(self, path: Path) -> None:
        if self.sandbox is not None:
            try:
                path.relative_to(self.sandbox)
            except ValueError:
                raise DBaseError(
                    f"Path {path} is outside sandbox {self.sandbox}",
                    code="SANDBOX",
                )

    # -- Variable access -----------------------------------------------------

    def get_var(self, name: str) -> Any:
        upper = name.upper()
        if upper in self.variables:
            return self.variables[upper]
        raise DBaseError(f"Variable not found: {name}", code="VAR_NOT_FOUND")

    def set_var(self, name: str, value: Any) -> None:
        self.variables[name.upper()] = value

    # -- User-defined functions -----------------------------------------------

    def define_user_func(self, name: str, defn: Any) -> None:
        """Register a user-defined function or procedure."""
        self._user_funcs[name.upper()] = defn

    def get_user_func(self, name: str) -> Any | None:
        """Look up a user-defined function by name. Returns None if not found."""
        return self._user_funcs.get(name.upper())

    # -- Output --------------------------------------------------------------

    def emit(self, text: str) -> None:
        """Add output text (for ? command and LIST)."""
        self.output.append(text)

    def flush_output(self) -> str:
        """Return and clear accumulated output."""
        result = "\n".join(self.output)
        self.output.clear()
        return result

    # -- Call stack -----------------------------------------------------------

    def push_program(self, name: str) -> None:
        self._call_stack.append(name)

    def pop_program(self) -> str | None:
        return self._call_stack.pop() if self._call_stack else None

    @property
    def current_program(self) -> str:
        return self._call_stack[-1] if self._call_stack else ""
