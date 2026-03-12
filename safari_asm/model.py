"""Core data models for Safari ASM."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

__all__ = [
    "Directive",
    "Instruction",
    "Operand",
    "Program",
    "SymbolDeclaration",
]


@dataclass(frozen=True, slots=True)
class Operand:
    """Parsed operand."""

    kind: str
    value: Any
    index: "Operand | None" = None


@dataclass(frozen=True, slots=True)
class SymbolDeclaration:
    """A declared variable or constant."""

    name: str
    kind: str
    value: Any = None
    line_no: int = 0


@dataclass(frozen=True, slots=True)
class Directive:
    """A non-executable directive preserved for diagnostics."""

    name: str
    args: tuple[Operand, ...] = ()
    label: str | None = None
    line_no: int = 0


@dataclass(frozen=True, slots=True)
class Instruction:
    """A normalized executable instruction."""

    opcode: str
    operands: tuple[Operand, ...] = ()
    line_no: int = 0
    raw: str = ""
    label: str | None = None


@dataclass(slots=True)
class Program:
    """Parsed Safari ASM program."""

    declarations: list[SymbolDeclaration] = field(default_factory=list)
    directives: list[Directive] = field(default_factory=list)
    instructions: list[Instruction] = field(default_factory=list)
    labels: dict[str, int] = field(default_factory=dict)
    entry_label: str | None = None
    source_name: str = "<memory>"
