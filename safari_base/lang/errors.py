"""Error types for the Safari Base dBASE language processor."""

from __future__ import annotations


class DBaseError(Exception):
    """Base class for all dBASE runtime errors."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "RUNTIME",
        line_number: int | None = None,
        command_text: str = "",
        program: str = "",
        work_area: str = "",
    ) -> None:
        super().__init__(message)
        self.code = code
        self.line_number = line_number
        self.command_text = command_text
        self.program = program
        self.work_area = work_area


class ParseError(DBaseError):
    """Raised when the parser encounters invalid syntax."""

    def __init__(
        self, message: str, *, line_number: int | None = None, command_text: str = ""
    ) -> None:
        super().__init__(
            message, code="PARSE", line_number=line_number, command_text=command_text
        )


class NoTableError(DBaseError):
    """Raised when a command requires an open table but none is active."""

    def __init__(
        self, message: str = "No table is open in the current work area"
    ) -> None:
        super().__init__(message, code="NO_TABLE")


class FieldNotFoundError(DBaseError):
    """Raised when a referenced field does not exist."""

    def __init__(self, field: str, table: str = "") -> None:
        msg = f"Field not found: {field}" + (f" in {table}" if table else "")
        super().__init__(msg, code="FIELD_NOT_FOUND")


class UnsafeCommandError(DBaseError):
    """Raised when a destructive command is used without unsafe mode."""

    def __init__(self, command: str) -> None:
        super().__init__(
            f"Unsafe command disabled: {command}. Enable unsafe=True to use.",
            code="UNSAFE",
        )
