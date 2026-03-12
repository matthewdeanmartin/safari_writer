"""Runtime interpreter for Safari ASM."""

from __future__ import annotations

import builtins
import importlib
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TextIO, cast

from safari_asm.model import Instruction, Operand, Program
from safari_asm.parser import parse_source

__all__ = [
    "ConditionState",
    "SafariAsmInterpreter",
    "SafariAsmRuntimeError",
    "run_source",
]


@dataclass(slots=True)
class ConditionState:
    """Branch-relevant condition state."""

    equal: bool = False
    less: bool = False
    greater: bool = False
    truthy: bool = False
    error: bool = False
    error_message: str | None = None
    last_value: Any = None


class SafariAsmRuntimeError(RuntimeError):
    """Raised when Safari ASM execution cannot continue."""


class SafariAsmInterpreter:
    """Execute Safari ASM programs directly on a Python runtime."""

    def __init__(
        self,
        *,
        argv: list[str] | None = None,
        stdin: TextIO | None = None,
        stdout: TextIO | None = None,
        stderr: TextIO | None = None,
    ) -> None:
        self.argv = list(argv or [])
        self.stdin = stdin or sys.stdin
        self.stdout = stdout or sys.stdout
        self.stderr = stderr or sys.stderr
        self.registers: dict[str, Any] = {"A": None, "X": None, "Y": None}
        self.variables: dict[str, Any] = {}
        self.constants: set[str] = set()
        self.stack: list[Any] = []
        self.call_stack: list[int] = []
        self.file_handles: dict[str, TextIO] = {}
        self.flags = ConditionState()
        self._halted = False

    def run(self, program: Program, *, entry_label: str | None = None) -> Any:
        """Run a parsed program and return register A."""

        self._reset_runtime()
        self._load_declarations(program)
        start_pc = self._entry_pc(program, entry_label)
        pc = start_pc

        while 0 <= pc < len(program.instructions) and not self._halted:
            instruction = program.instructions[pc]
            next_pc = pc + 1
            jump_target = self._execute_instruction(program, instruction, next_pc)
            pc = next_pc if jump_target is None else jump_target

        self._close_all_handles()
        return self.registers["A"]

    def run_source(
        self,
        source: str,
        *,
        source_name: str = "<memory>",
        entry_label: str | None = None,
    ) -> Any:
        """Parse and run a source string."""

        program = parse_source(source, source_name=source_name)
        return self.run(program, entry_label=entry_label)

    def _reset_runtime(self) -> None:
        self.registers = {"A": None, "X": None, "Y": None}
        self.variables = {}
        self.constants = set()
        self.stack = []
        self.call_stack = []
        self.file_handles = {}
        self.flags = ConditionState()
        self._halted = False

    def _load_declarations(self, program: Program) -> None:
        for declaration in program.declarations:
            self.variables[declaration.name] = declaration.value
            if declaration.kind == "CONST":
                self.constants.add(declaration.name)

    def _entry_pc(self, program: Program, entry_label: str | None) -> int:
        label = entry_label or program.entry_label
        if label is not None:
            normalized = label.upper()
            if normalized not in program.labels:
                raise SafariAsmRuntimeError(f"Unknown entry label: {normalized}")
            return program.labels[normalized]
        if not program.instructions:
            return 0
        return 0

    def _execute_instruction(
        self,
        program: Program,
        instruction: Instruction,
        next_pc: int,
    ) -> int | None:
        opcode = instruction.opcode
        ops = instruction.operands

        if opcode in {"LDA", "LDX", "LDY"}:
            self._set_register(opcode[-1], self._read_operand(ops[0]))
            return None
        if opcode in {"STA", "STX", "STY"}:
            self._write_target(ops[0], self.registers[opcode[-1]])
            self._set_result(self.registers[opcode[-1]])
            return None
        if opcode == "MOV":
            self._write_target(ops[0], self._read_operand(ops[1]))
            self._set_result(self._read_operand(ops[1]))
            return None
        if opcode == "TAX":
            self._set_register("X", self.registers["A"])
            return None
        if opcode == "TAY":
            self._set_register("Y", self.registers["A"])
            return None
        if opcode == "TXA":
            self._set_register("A", self.registers["X"])
            return None
        if opcode == "TYA":
            self._set_register("A", self.registers["Y"])
            return None
        if opcode in {"ADD", "SUB", "MUL", "DIV", "MOD"}:
            self._arithmetic(opcode, ops[0])
            return None
        if opcode in {"INC", "DEC"}:
            target = ops[0] if ops else Operand("register", "A")
            current = self._read_operand(target)
            delta = 1 if opcode == "INC" else -1
            self._write_target(target, (0 if current is None else current) + delta)
            self._set_result(self._read_operand(target))
            return None
        if opcode == "CMP":
            self._compare(self._read_operand(ops[0]), self._read_operand(ops[1]))
            return None
        if opcode == "TEST":
            self._set_result(self._read_operand(ops[0]))
            return None
        if opcode == "TYPE":
            value = self._read_operand(ops[0])
            self._set_register("A", type(value).__name__)
            return None
        if opcode in {"JMP", "BRA"}:
            return self._jump(program, ops[0])
        if opcode == "BEQ":
            return self._jump(program, ops[0]) if self.flags.equal else None
        if opcode == "BNE":
            return self._jump(program, ops[0]) if not self.flags.equal else None
        if opcode == "BGT":
            return self._jump(program, ops[0]) if self.flags.greater else None
        if opcode == "BLT":
            return self._jump(program, ops[0]) if self.flags.less else None
        if opcode == "BGE":
            return (
                self._jump(program, ops[0])
                if self.flags.greater or self.flags.equal
                else None
            )
        if opcode == "BLE":
            return (
                self._jump(program, ops[0])
                if self.flags.less or self.flags.equal
                else None
            )
        if opcode == "BERR":
            return self._jump(program, ops[0]) if self.flags.error else None
        if opcode == "JSR":
            self.call_stack.append(next_pc)
            return self._jump(program, ops[0])
        if opcode == "RTS":
            if not self.call_stack:
                raise SafariAsmRuntimeError(
                    f"RETURN with empty call stack at line {instruction.line_no}"
                )
            return self.call_stack.pop()
        if opcode == "PHA":
            self.stack.append(self.registers["A"])
            self._set_result(self.registers["A"])
            return None
        if opcode == "PLA":
            self._set_register("A", self._pop_stack("A"))
            return None
        if opcode == "PHX":
            self.stack.append(self.registers["X"])
            self._set_result(self.registers["X"])
            return None
        if opcode == "PLX":
            self._set_register("X", self._pop_stack("X"))
            return None
        if opcode == "PHY":
            self.stack.append(self.registers["Y"])
            self._set_result(self.registers["Y"])
            return None
        if opcode == "PLY":
            self._set_register("Y", self._pop_stack("Y"))
            return None
        if opcode == "PUSH":
            value = self._read_operand(ops[0]) if ops else self.registers["A"]
            self.stack.append(value)
            self._set_result(value)
            return None
        if opcode == "POP":
            target = ops[0] if ops else Operand("register", "A")
            value = self._pop_stack(self._target_name(target))
            self._write_target(target, value)
            self._set_result(value)
            return None
        if opcode == "CAT":
            self._write_target(
                ops[0],
                f"{self._stringify(self._read_operand(ops[0]))}{self._stringify(self._read_operand(ops[1]))}",
            )
            self._set_result(self._read_operand(ops[0]))
            return None
        if opcode == "LEN":
            if len(ops) == 1:
                target = Operand("register", "A")
                value = self._read_operand(ops[0])
            else:
                target = ops[0]
                value = self._read_operand(ops[1])
            try:
                result = len(value)
            except TypeError:
                result = len(self._stringify(value))
            self._write_target(target, result)
            self._set_result(result)
            return None
        if opcode in {"TRIM", "UPPER", "LOWER"}:
            target = ops[0]
            text = self._stringify(self._read_operand(target))
            transformed: object
            if opcode == "TRIM":
                transformed = text.strip()
            elif opcode == "UPPER":
                transformed = text.upper()
            else:
                transformed = text.lower()
            self._write_target(target, transformed)
            self._set_result(transformed)
            return None
        if opcode == "SPLIT":
            split_result: object = self._stringify(self._read_operand(ops[1])).split(
                self._stringify(self._read_operand(ops[2]))
            )
            self._write_target(ops[0], split_result)
            self._set_result(split_result)
            return None
        if opcode == "JOIN":
            sequence = self._read_operand(ops[1])
            if not isinstance(sequence, (list, tuple)):
                raise SafariAsmRuntimeError(
                    f"JOIN requires a list-like value at line {instruction.line_no}"
                )
            delimiter = self._stringify(self._read_operand(ops[2]))
            joined: object = delimiter.join(self._stringify(item) for item in sequence)
            self._write_target(ops[0], joined)
            self._set_result(joined)
            return None
        if opcode == "GET":
            self._get_value(ops[0], ops[1], ops[2])
            return None
        if opcode == "PUT":
            self._put_value(ops[0], ops[1], ops[2])
            return None
        if opcode == "MATCH":
            haystack = self._stringify(self._read_operand(ops[1]))
            pattern = self._stringify(self._read_operand(ops[2]))
            matched = self._match_text(haystack, pattern)
            self._write_target(ops[0], matched)
            self._set_result(matched)
            return None
        if opcode == "REPL":
            replaced: object = self._stringify(self._read_operand(ops[1])).replace(
                self._stringify(self._read_operand(ops[2])),
                self._stringify(self._read_operand(ops[3])),
            )
            self._write_target(ops[0], replaced)
            self._set_result(replaced)
            return None
        if opcode == "INP":
            target = ops[0]
            line = self.stdin.readline()
            if line == "":
                self._write_target(target, None)
                self._set_result(None)
            else:
                value = line.rstrip("\r\n")
                self._write_target(target, value)
                self._set_result(value)
            return None
        if opcode in {"OUT", "OUTLN", "ERR", "ERRLN"}:
            self._emit_output(opcode, self._read_operand(ops[0]))
            return None
        if opcode == "OPEN":
            self._open_handle(ops[0], ops[1], ops[2])
            return None
        if opcode == "READLN":
            self._read_handle_line(ops[0], ops[1])
            return None
        if opcode == "WRITELN":
            self._write_handle_line(ops[0], ops[1])
            return None
        if opcode == "CLOSE":
            self._close_handle(ops[0])
            return None
        if opcode == "ARGV":
            self._write_target(ops[0], list(self.argv))
            self._set_result(self.argv)
            return None
        if opcode == "ARG":
            index = int(self._read_operand(ops[1]))
            value = self.argv[index] if 0 <= index < len(self.argv) else None
            self._write_target(ops[0], value)
            self._set_result(value)
            return None
        if opcode == "ENV":
            key = self._stringify(self._read_operand(ops[1]))
            value = os.environ.get(key)
            self._write_target(ops[0], value)
            self._set_result(value)
            return None
        if opcode == "NOP":
            return None
        if opcode == "HALT":
            self._halted = True
            return None
        if opcode == "PYCALL":
            self._pycall(ops)
            return None
        if opcode == "ERRMSG":
            target = ops[0] if ops else Operand("register", "A")
            self._write_target(target, self.flags.error_message)
            self._set_result(self.flags.error_message)
            return None

        raise SafariAsmRuntimeError(
            f"Unknown opcode {opcode} at line {instruction.line_no}"
        )

    def _arithmetic(self, opcode: str, operand: Operand) -> None:
        value = self._read_operand(operand)
        left = self.registers["A"]
        if left is None:
            left = 0
        try:
            if opcode == "ADD":
                result = left + value
            elif opcode == "SUB":
                result = left - value
            elif opcode == "MUL":
                result = left * value
            elif opcode == "DIV":
                result = left / value
            else:
                result = left % value
        except Exception as exc:
            self._set_error(str(exc))
            return
        self._set_register("A", result)

    def _compare(self, left: Any, right: Any) -> None:
        try:
            less = left < right
            greater = left > right
        except TypeError:
            left_text = self._stringify(left)
            right_text = self._stringify(right)
            less = left_text < right_text
            greater = left_text > right_text
        self.flags = ConditionState(
            equal=left == right,
            less=less,
            greater=greater,
            truthy=bool(left == right),
            error=False,
            error_message=None,
            last_value=left,
        )

    def _jump(self, program: Program, operand: Operand) -> int:
        if operand.kind != "symbol":
            raise SafariAsmRuntimeError("branch targets must be labels")
        label = str(operand.value).upper()
        if label not in program.labels:
            raise SafariAsmRuntimeError(f"Unknown label: {label}")
        return program.labels[label]

    def _set_register(self, register: str, value: Any) -> None:
        self.registers[register] = value
        self._set_result(value)

    def _read_operand(self, operand: Operand) -> Any:
        if operand.kind in {"literal", "immediate"}:
            return operand.value
        if operand.kind == "register":
            return self.registers[operand.value]
        if operand.kind == "symbol":
            return self.variables.get(str(operand.value).upper())
        if operand.kind == "indexed":
            container = self.variables.get(str(operand.value).upper())
            index = (
                self._read_operand(operand.index) if operand.index is not None else None
            )
            return self._read_indexed(container, index)
        raise SafariAsmRuntimeError(f"Unsupported operand kind: {operand.kind}")

    def _write_target(self, operand: Operand, value: Any) -> None:
        if operand.kind == "register":
            self.registers[operand.value] = value
            return
        if operand.kind == "symbol":
            name = str(operand.value).upper()
            if name in self.constants:
                raise SafariAsmRuntimeError(f"Cannot assign constant {name}")
            self.variables[name] = value
            return
        if operand.kind == "indexed":
            name = str(operand.value).upper()
            container = self.variables.get(name)
            index = (
                self._read_operand(operand.index) if operand.index is not None else None
            )
            updated = self._write_indexed(container, index, value)
            self.variables[name] = updated
            return
        raise SafariAsmRuntimeError(f"Operand is not assignable: {operand.kind}")

    def _read_indexed(self, container: Any, index: Any) -> Any:
        try:
            return container[index]
        except Exception as exc:
            self._set_error(str(exc))
            return None

    def _write_indexed(self, container: Any, index: Any, value: Any) -> Any:
        if container is None:
            container = [] if isinstance(index, int) else {}
        if isinstance(container, list):
            if not isinstance(index, int):
                raise SafariAsmRuntimeError("List index must be an integer")
            while len(container) <= index:
                container.append(None)
            container[index] = value
            return container
        if isinstance(container, dict):
            container[index] = value
            return container
        raise SafariAsmRuntimeError("Indexed target must be a list or map")

    def _set_result(self, value: Any) -> None:
        self.flags = ConditionState(
            equal=not bool(value),
            less=False,
            greater=False,
            truthy=bool(value),
            error=False,
            error_message=None,
            last_value=value,
        )

    def _set_error(self, message: str) -> None:
        self.flags = ConditionState(
            equal=False,
            less=False,
            greater=False,
            truthy=False,
            error=True,
            error_message=message,
            last_value=None,
        )

    def _pop_stack(self, target_name: str) -> Any:
        if not self.stack:
            raise SafariAsmRuntimeError(
                f"Cannot POP into {target_name}: stack is empty"
            )
        return self.stack.pop()

    def _target_name(self, operand: Operand) -> str:
        if operand.kind in {"register", "symbol"}:
            return str(operand.value)
        return operand.kind

    def _stringify(self, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, bool):
            return "TRUE" if value else "FALSE"
        return str(value)

    def _get_value(
        self, target: Operand, source: Operand, key_operand: Operand
    ) -> None:
        container = self._read_operand(source)
        key = self._read_operand(key_operand)
        try:
            value = container[key]
        except Exception as exc:
            self._set_error(str(exc))
            self._write_target(target, None)
            return
        self._write_target(target, value)
        self._set_result(value)

    def _put_value(
        self, collection: Operand, key_operand: Operand, value_operand: Operand
    ) -> None:
        key = self._read_operand(key_operand)
        value = self._read_operand(value_operand)
        if collection.kind == "indexed":
            raise SafariAsmRuntimeError("PUT target cannot be doubly indexed")
        current = self._read_operand(collection)
        updated = self._write_indexed(current, key, value)
        self._write_target(collection, updated)
        self._set_result(updated)

    def _match_text(self, haystack: str, pattern: str) -> bool:
        try:
            return re.search(pattern, haystack) is not None
        except re.error:
            return pattern in haystack

    def _emit_output(self, opcode: str, value: Any) -> None:
        stream = self.stderr if opcode.startswith("ERR") else self.stdout
        suffix = "\n" if opcode.endswith("LN") else ""
        stream.write(f"{self._stringify(value)}{suffix}")
        stream.flush()
        self._set_result(value)

    def _handle_name(self, operand: Operand) -> str:
        if operand.kind == "symbol":
            return str(operand.value).upper()
        if operand.kind == "register":
            return self._stringify(self.registers[operand.value])
        return self._stringify(self._read_operand(operand))

    def _open_handle(
        self, handle_operand: Operand, path_operand: Operand, mode_operand: Operand
    ) -> None:
        handle_name = self._handle_name(handle_operand)
        path = Path(self._stringify(self._read_operand(path_operand)))
        mode = self._stringify(self._read_operand(mode_operand)) or "r"
        try:
            handle = cast(TextIO, path.open(mode, encoding="utf-8"))
        except OSError as exc:
            self._set_error(str(exc))
            return
        self.file_handles[handle_name] = handle
        self._set_result(handle_name)

    def _read_handle_line(self, target: Operand, handle_operand: Operand) -> None:
        handle_name = self._handle_name(handle_operand)
        handle = self.file_handles.get(handle_name)
        if handle is None:
            self._set_error(f"Unknown file handle {handle_name}")
            self._write_target(target, None)
            return
        line = handle.readline()
        value = None if line == "" else line.rstrip("\r\n")
        self._write_target(target, value)
        self._set_result(value)

    def _write_handle_line(
        self, handle_operand: Operand, value_operand: Operand
    ) -> None:
        handle_name = self._handle_name(handle_operand)
        handle = self.file_handles.get(handle_name)
        if handle is None:
            self._set_error(f"Unknown file handle {handle_name}")
            return
        handle.write(f"{self._stringify(self._read_operand(value_operand))}\n")
        handle.flush()
        self._set_result(True)

    def _close_handle(self, handle_operand: Operand) -> None:
        handle_name = self._handle_name(handle_operand)
        handle = self.file_handles.pop(handle_name, None)
        if handle is None:
            self._set_error(f"Unknown file handle {handle_name}")
            return
        handle.close()
        self._set_result(True)

    def _close_all_handles(self) -> None:
        for handle in list(self.file_handles.values()):
            handle.close()
        self.file_handles.clear()

    def _pycall(self, operands: tuple[Operand, ...]) -> None:
        target = operands[0]
        callable_name = self._stringify(self._read_operand(operands[1]))
        args = [self._read_operand(operand) for operand in operands[2:]]
        try:
            callable_obj = self._resolve_callable(callable_name)
            result = callable_obj(*args)
        except Exception as exc:
            self._set_error(str(exc))
            self._write_target(target, None)
            return
        self._write_target(target, result)
        self._set_result(result)

    def _resolve_callable(self, name: str) -> Any:
        if ":" in name:
            module_name, attr_name = name.split(":", 1)
            module = importlib.import_module(module_name)
            return getattr(module, attr_name)
        if hasattr(builtins, name):
            return getattr(builtins, name)
        if "." in name:
            module_name, attr_name = name.rsplit(".", 1)
            module = importlib.import_module(module_name)
            return getattr(module, attr_name)
        raise AttributeError(f"Unknown callable {name}")


def run_source(
    source: str,
    *,
    argv: list[str] | None = None,
    stdin: TextIO | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
    source_name: str = "<memory>",
    entry_label: str | None = None,
) -> Any:
    """Convenience helper for one-shot execution."""

    interpreter = SafariAsmInterpreter(
        argv=argv, stdin=stdin, stdout=stdout, stderr=stderr
    )
    return interpreter.run_source(
        source, source_name=source_name, entry_label=entry_label
    )
