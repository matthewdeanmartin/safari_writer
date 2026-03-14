"""Parser for Safari ASM."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from safari_asm.model import (Directive, Instruction, Operand, Program,
                              SymbolDeclaration)

__all__ = ["SafariAsmParseError", "parse_source"]


_MNEMONIC_ALIASES = {
    "LOADA": "LDA",
    "LOADX": "LDX",
    "LOADY": "LDY",
    "STOREA": "STA",
    "STOREX": "STX",
    "STOREY": "STY",
    "MOVE": "MOV",
    "JUMP": "JMP",
    "CALL": "JSR",
    "RETURN": "RTS",
    "COMPARE": "CMP",
    "PRINT": "OUT",
    "PRINTLN": "OUTLN",
    "INPUT": "INP",
    "EPRINT": "ERR",
    "EPRINTLN": "ERRLN",
    "STOP": "HALT",
    "BRANCH": "BRA",
    "CONCAT": "CAT",
    "INCREMENT": "INC",
    "DECREMENT": "DEC",
}

_REGISTER_NAMES = {"A", "X", "Y"}
_SECTION_DIRECTIVES = {".DATA", ".TEXT", ".PROC", ".ENDPROC"}
_DECL_DIRECTIVES = {".VAR", ".CONST", ".LIST", ".MAP", ".BYTE", ".WORD"}


class SafariAsmParseError(ValueError):
    """Raised when Safari ASM source cannot be parsed."""

    def __init__(self, message: str, *, line_no: int, source_line: str) -> None:
        super().__init__(f"Line {line_no}: {message}: {source_line}")
        self.line_no = line_no
        self.source_line = source_line


@dataclass(slots=True)
class _SplitLine:
    label: str | None
    body: str


def parse_source(source: str, *, source_name: str = "<memory>") -> Program:
    """Parse Safari ASM source into a normalized program."""

    program = Program(source_name=source_name)
    pending_labels: list[str] = []

    for line_no, original in enumerate(source.splitlines(), start=1):
        line = _strip_comment(original).strip()
        if not line:
            continue
        split = _split_label(line, line_no)
        label = split.label
        body = split.body.strip()
        if label is not None:
            pending_labels.append(label)
        if not body:
            continue
        if body.startswith("."):
            _parse_directive(program, pending_labels, body, line_no, original)
            continue

        opcode_text, operand_text = _split_opcode(body)
        opcode = _MNEMONIC_ALIASES.get(opcode_text.upper(), opcode_text.upper())
        operands = tuple(
            _parse_operand(token, line_no, original)
            for token in _split_operands(operand_text)
        )
        attached_label = pending_labels[0] if pending_labels else None
        for pending in pending_labels:
            program.labels[pending] = len(program.instructions)
        pending_labels.clear()
        program.instructions.append(
            Instruction(
                opcode=opcode,
                operands=operands,
                line_no=line_no,
                raw=original.rstrip(),
                label=attached_label,
            )
        )

    if pending_labels:
        raise SafariAsmParseError(
            "label has no following directive or instruction",
            line_no=line_no if source.splitlines() else 1,
            source_line=source.splitlines()[-1] if source.splitlines() else "",
        )

    return program


def _parse_directive(
    program: Program,
    pending_labels: list[str],
    body: str,
    line_no: int,
    original: str,
) -> None:
    directive_text, operand_text = _split_opcode(body)
    directive = directive_text.upper()
    operands = tuple(
        _parse_operand(token, line_no, original)
        for token in _split_operands(operand_text)
    )

    if directive == ".ENTRY":
        if len(operands) != 1 or operands[0].kind != "symbol":
            raise SafariAsmParseError(
                ".ENTRY requires a single label name",
                line_no=line_no,
                source_line=original,
            )
        program.entry_label = str(operands[0].value).upper()
        program.directives.append(Directive(directive, operands, line_no=line_no))
        pending_labels.clear()
        return

    label = pending_labels[0] if pending_labels else None
    if directive in _SECTION_DIRECTIVES:
        for pending in pending_labels:
            program.labels[pending] = len(program.instructions)
        program.directives.append(
            Directive(directive, operands, label=label, line_no=line_no)
        )
        pending_labels.clear()
        return

    if directive in _DECL_DIRECTIVES:
        if label is None:
            raise SafariAsmParseError(
                f"{directive} requires a label name",
                line_no=line_no,
                source_line=original,
            )
        if len(pending_labels) != 1:
            raise SafariAsmParseError(
                f"{directive} only supports one label",
                line_no=line_no,
                source_line=original,
            )
        try:
            value = _declaration_value(directive, operands)
        except ValueError as exc:
            raise SafariAsmParseError(
                str(exc),
                line_no=line_no,
                source_line=original,
            ) from exc
        program.declarations.append(
            SymbolDeclaration(
                name=label, kind=directive[1:], value=value, line_no=line_no
            )
        )
        program.directives.append(
            Directive(directive, operands, label=label, line_no=line_no)
        )
        pending_labels.clear()
        return

    raise SafariAsmParseError(
        f"unknown directive {directive}",
        line_no=line_no,
        source_line=original,
    )


def _declaration_value(directive: str, operands: Iterable[Operand]) -> object:
    values = [_literal_from_operand(operand) for operand in operands]
    if directive == ".VAR":
        return values[0] if values else None
    if directive == ".CONST":
        if len(values) != 1:
            raise ValueError(".CONST requires exactly one value")
        return values[0]
    if directive in {".LIST", ".BYTE", ".WORD"}:
        return list(values)
    if directive == ".MAP":
        if len(values) % 2 != 0:
            raise ValueError(".MAP requires key/value pairs")
        return {values[index]: values[index + 1] for index in range(0, len(values), 2)}
    raise ValueError(f"unsupported declaration directive {directive}")


def _literal_from_operand(operand: Operand) -> object:
    if operand.kind in {"literal", "immediate"}:
        return operand.value
    if operand.kind == "symbol":
        return operand.value
    raise ValueError(f"directive values must be literal-like, got {operand.kind}")


def _split_label(line: str, line_no: int) -> _SplitLine:
    in_string = False
    for index, char in enumerate(line):
        if char == '"':
            in_string = not in_string
        elif char == ":" and not in_string:
            label = line[:index].strip()
            if not label:
                raise SafariAsmParseError(
                    "empty label", line_no=line_no, source_line=line
                )
            return _SplitLine(label=label.upper(), body=line[index + 1 :])
    return _SplitLine(label=None, body=line)


def _strip_comment(line: str) -> str:
    in_string = False
    escaped = False
    chars: list[str] = []
    for char in line:
        if escaped:
            chars.append(char)
            escaped = False
            continue
        if char == "\\" and in_string:
            chars.append(char)
            escaped = True
            continue
        if char == '"':
            in_string = not in_string
            chars.append(char)
            continue
        if char == ";" and not in_string:
            break
        chars.append(char)
    return "".join(chars)


def _split_opcode(body: str) -> tuple[str, str]:
    parts = body.split(None, 1)
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], parts[1]


def _split_operands(text: str) -> list[str]:
    if not text.strip():
        return []
    parts: list[str] = []
    current: list[str] = []
    in_string = False
    for index, char in enumerate(text):
        if char == '"':
            in_string = not in_string
            current.append(char)
            continue
        next_char = text[index + 1] if index + 1 < len(text) else ""
        if char == "," and not in_string and next_char.isspace():
            token = "".join(current).strip()
            if token:
                parts.append(token)
            current = []
            continue
        current.append(char)
    token = "".join(current).strip()
    if token:
        parts.append(token)
    return parts


def _parse_operand(token: str, line_no: int, original: str) -> Operand:
    token = token.strip()
    if not token:
        raise SafariAsmParseError(
            "empty operand", line_no=line_no, source_line=original
        )
    if token.startswith("#"):
        return Operand("immediate", _parse_literal(token[1:], line_no, original))
    if token.startswith('"'):
        return Operand("literal", _parse_literal(token, line_no, original))
    if "," in token:
        base_text, index_text = token.split(",", 1)
        return Operand(
            "indexed",
            base_text.strip().upper(),
            _parse_operand(index_text.strip(), line_no, original),
        )

    upper = token.upper()
    if upper in _REGISTER_NAMES:
        return Operand("register", upper)
    literal = _maybe_parse_scalar(upper, token)
    if literal is not _UNSET:
        return Operand("literal", literal)
    return Operand("symbol", upper)


_UNSET = object()


def _maybe_parse_scalar(upper: str, original: str) -> object:
    if upper == "TRUE":
        return True
    if upper == "FALSE":
        return False
    if upper in {"NULL", "NONE", "NIL"}:
        return None
    try:
        if original.startswith(("0X", "0x")):
            return int(original, 16)
        if any(char in original for char in ".eE"):
            return float(original)
        return int(original)
    except ValueError:
        return _UNSET


def _parse_literal(text: str, line_no: int, original: str) -> object:
    text = text.strip()
    scalar = _maybe_parse_scalar(text.upper(), text)
    if scalar is not _UNSET:
        return scalar
    if len(text) >= 2 and text.startswith('"') and text.endswith('"'):
        inner = text[1:-1]
        return bytes(inner, "utf-8").decode("unicode_escape")
    raise SafariAsmParseError(
        f"invalid literal {text}",
        line_no=line_no,
        source_line=original,
    )
