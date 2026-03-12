"""AST nodes and value types for the dBASE language processor."""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


# ---------------------------------------------------------------------------
# Tokens
# ---------------------------------------------------------------------------

class TokenType(Enum):
    # Literals
    NUMBER = auto()
    STRING = auto()
    LOGICAL = auto()
    # Identifiers & keywords
    IDENT = auto()
    KEYWORD = auto()
    # Operators
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    CARET = auto()
    EQ = auto()
    EQEQ = auto()
    NEQ = auto()
    BANGEQ = auto()
    LT = auto()
    LE = auto()
    GT = auto()
    GE = auto()
    DOT_AND = auto()
    DOT_OR = auto()
    DOT_NOT = auto()
    # Punctuation
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()   # {
    RBRACE = auto()   # }
    COMMA = auto()
    SEMI = auto()  # line continuation
    ARROW = auto()  # ->
    # Special
    AMPAMP = auto()  # && inline comment (consumed by lexer)
    NEWLINE = auto()
    EOF = auto()


@dataclass
class Token:
    type: TokenType
    value: str
    line: int = 0


# ---------------------------------------------------------------------------
# AST Expression nodes
# ---------------------------------------------------------------------------

@dataclass
class Expr:
    """Base expression node."""


@dataclass
class NumberLit(Expr):
    value: float


@dataclass
class StringLit(Expr):
    value: str


@dataclass
class LogicalLit(Expr):
    value: bool


@dataclass
class Ident(Expr):
    name: str


@dataclass
class FieldRef(Expr):
    """alias->field qualified reference."""
    alias: str
    field_name: str  # renamed from 'field' to avoid shadowing


@dataclass
class FuncCall(Expr):
    name: str
    args: list[Expr]


@dataclass
class BinOp(Expr):
    op: str
    left: Expr
    right: Expr


@dataclass
class UnaryOp(Expr):
    op: str
    operand: Expr


# ---------------------------------------------------------------------------
# AST Statement nodes
# ---------------------------------------------------------------------------

@dataclass
class Stmt:
    """Base statement node."""
    line: int = 0


@dataclass
class UseStmt(Stmt):
    table: str = ""
    alias: str = ""
    exclusive: bool = False


@dataclass
class SelectStmt(Stmt):
    area: str | int = 1


@dataclass
class CloseStmt(Stmt):
    pass


@dataclass
class GoStmt(Stmt):
    target: str | Expr = "TOP"  # "TOP", "BOTTOM", or an expression


@dataclass
class SkipStmt(Stmt):
    count: Expr | None = None


@dataclass
class StoreStmt(Stmt):
    expr: Expr = field(default_factory=lambda: NumberLit(0))
    var: str = ""


@dataclass
class AssignStmt(Stmt):
    var: str = ""
    expr: Expr = field(default_factory=lambda: NumberLit(0))


@dataclass
class ReplaceStmt(Stmt):
    assignments: list[tuple[str, Expr]] = field(default_factory=list)
    scope: str = ""  # "", "ALL"
    condition: Expr | None = None


@dataclass
class AppendBlankStmt(Stmt):
    pass


@dataclass
class AppendFromStmt(Stmt):
    source: str = ""


@dataclass
class DeleteStmt(Stmt):
    scope: str = ""
    condition: Expr | None = None


@dataclass
class RecallStmt(Stmt):
    scope: str = ""
    condition: Expr | None = None


@dataclass
class PackStmt(Stmt):
    pass


@dataclass
class ZapStmt(Stmt):
    pass


@dataclass
class LocateStmt(Stmt):
    condition: Expr = field(default_factory=lambda: LogicalLit(True))


@dataclass
class ContinueStmt(Stmt):
    pass


@dataclass
class SeekStmt(Stmt):
    expr: Expr = field(default_factory=lambda: NumberLit(0))


@dataclass
class SetStmt(Stmt):
    setting: str = ""
    value: str = ""


@dataclass
class CreateTableStmt(Stmt):
    table: str = ""
    columns: list[tuple[str, str, int, int]] = field(default_factory=list)
    # (name, type_char, width, decimals)


@dataclass
class CopyStructureStmt(Stmt):
    target: str = ""
    extended: bool = False


@dataclass
class CreateFromStmt(Stmt):
    table: str = ""
    source: str = ""


@dataclass
class IndexOnStmt(Stmt):
    expr: Expr = field(default_factory=lambda: NumberLit(0))
    tag: str = ""


@dataclass
class ListStmt(Stmt):
    fields: list[str] = field(default_factory=list)
    scope: str = ""
    condition: Expr | None = None


@dataclass
class DisplayStructureStmt(Stmt):
    pass


@dataclass
class CountStmt(Stmt):
    condition: Expr | None = None
    to_var: str = ""


@dataclass
class SumStmt(Stmt):
    expr: Expr = field(default_factory=lambda: NumberLit(0))
    to_var: str = ""
    condition: Expr | None = None


@dataclass
class AverageStmt(Stmt):
    expr: Expr = field(default_factory=lambda: NumberLit(0))
    to_var: str = ""
    condition: Expr | None = None


@dataclass
class PrintStmt(Stmt):
    """The ? command."""
    exprs: list[Expr] = field(default_factory=list)


@dataclass
class IfStmt(Stmt):
    condition: Expr = field(default_factory=lambda: LogicalLit(True))
    then_body: list[Stmt] = field(default_factory=list)
    elseif_clauses: list[tuple[Expr, list[Stmt]]] = field(default_factory=list)
    else_body: list[Stmt] = field(default_factory=list)


@dataclass
class DoCaseStmt(Stmt):
    cases: list[tuple[Expr, list[Stmt]]] = field(default_factory=list)
    otherwise: list[Stmt] = field(default_factory=list)


@dataclass
class DoWhileStmt(Stmt):
    condition: Expr = field(default_factory=lambda: LogicalLit(True))
    body: list[Stmt] = field(default_factory=list)


@dataclass
class ForStmt(Stmt):
    var: str = ""
    start: Expr = field(default_factory=lambda: NumberLit(0))
    end: Expr = field(default_factory=lambda: NumberLit(0))
    step: Expr | None = None
    body: list[Stmt] = field(default_factory=list)


@dataclass
class ScanStmt(Stmt):
    condition: Expr | None = None
    body: list[Stmt] = field(default_factory=list)


@dataclass
class DoProgramStmt(Stmt):
    program: str = ""
    args: list[Expr] = field(default_factory=list)


@dataclass
class ReturnStmt(Stmt):
    expr: Expr | None = None


@dataclass
class ExitStmt(Stmt):
    pass


@dataclass
class LoopStmt(Stmt):
    pass


@dataclass
class SetFilterStmt(Stmt):
    condition: Expr | None = None


@dataclass
class SetDeletedStmt(Stmt):
    on: bool = True


@dataclass
class SetDefaultStmt(Stmt):
    path: str = ""


# OS commands
@dataclass
class DirStmt(Stmt):
    pattern: str = ""


@dataclass
class CdStmt(Stmt):
    path: str = ""


@dataclass
class RenameStmt(Stmt):
    old: str = ""
    new: str = ""


@dataclass
class CopyFileStmt(Stmt):
    source: str = ""
    target: str = ""


@dataclass
class EraseStmt(Stmt):
    filename: str = ""


@dataclass
class MdStmt(Stmt):
    dirname: str = ""


@dataclass
class RdStmt(Stmt):
    dirname: str = ""


@dataclass
class QuitStmt(Stmt):
    pass


@dataclass
class CommentStmt(Stmt):
    text: str = ""


@dataclass
class SetOrderStmt(Stmt):
    tag: str = ""


# ---------------------------------------------------------------------------
# User-defined functions and procedures (Safari BASIC extensions)
# ---------------------------------------------------------------------------

@dataclass
class FuncDefStmt(Stmt):
    """FUNC name(params) ... END FUNC"""
    name: str = ""
    params: list[str] = field(default_factory=list)
    body: list[Stmt] = field(default_factory=list)


@dataclass
class ProcDefStmt(Stmt):
    """PROC name(params) ... END PROC"""
    name: str = ""
    params: list[str] = field(default_factory=list)
    body: list[Stmt] = field(default_factory=list)


@dataclass
class DefFnStmt(Stmt):
    """DEF FN name(params) = expr  (one-liner function)"""
    name: str = ""
    params: list[str] = field(default_factory=list)
    expr: Expr = field(default_factory=lambda: NumberLit(0))


@dataclass
class ProcCallStmt(Stmt):
    """A procedure call used as a statement: DOBOX(1)"""
    name: str = ""
    args: list[Expr] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Hashmaps (Safari BASIC extensions)
# ---------------------------------------------------------------------------

@dataclass
class DimHashStmt(Stmt):
    """DIM FOO{} — declare an empty hashmap."""
    name: str = ""


@dataclass
class HashAssignStmt(Stmt):
    """FOO("key") = expr — assign a value to a hashmap key."""
    name: str = ""
    key: Expr = field(default_factory=lambda: StringLit(""))
    expr: Expr = field(default_factory=lambda: NumberLit(0))


@dataclass
class ForEachStmt(Stmt):
    """FOR EACH K$ IN PRICES ... NEXT"""
    var: str = ""
    hashmap: str = ""
    body: list[Stmt] = field(default_factory=list)


@dataclass
class HashAccessExpr(Expr):
    """FOO("key") as an expression — hashmap key lookup."""
    name: str = ""
    key: Expr = field(default_factory=lambda: StringLit(""))


# ---------------------------------------------------------------------------
# Command result
# ---------------------------------------------------------------------------

@dataclass
class CommandResult:
    """Structured result from executing a command."""
    success: bool = True
    message: str = ""
    data: Any = None
    rows_affected: int = 0
