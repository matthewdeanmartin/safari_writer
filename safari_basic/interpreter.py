import io
import math
import random
import re
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, TextIO, Tuple, Union


class BasicError(Exception):
    """Custom exception for runtime errors in the Safari Basic interpreter."""

    pass


@dataclass
class ForFrame:
    var_name: str
    end_value: float
    step: float
    line_number: int
    stmt_index: int


@dataclass
class GosubFrame:
    line_number: int
    stmt_index: int


class Scanner:
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.length = len(text)

    def remaining(self) -> str:
        return self.text[self.pos :]

    def peek(self) -> str:
        if self.pos < self.length:
            return self.text[self.pos]
        return ""

    def advance(self, count: int = 1):
        self.pos = min(self.pos + count, self.length)

    def skip_spaces(self):
        while self.pos < self.length and self.text[self.pos] in (" ", "\t"):
            self.pos += 1

    def match_keyword(self, keyword: str) -> bool:
        rem = self.remaining()
        if not rem.upper().startswith(keyword.upper()):
            return False
        end_idx = len(keyword)
        if end_idx >= len(rem):
            return True
        char_after = rem[end_idx]
        if char_after.isalnum() or char_after in ("_", "$"):
            return False
        return True

    def consume_keyword(self, keyword: str) -> bool:
        if self.match_keyword(keyword):
            self.advance(len(keyword))
            return True
        return False


class SafariBasic:
    def __init__(
        self, out_stream: Optional[TextIO] = None, in_stream: Optional[TextIO] = None
    ):
        self.out_stream = out_stream or sys.stdout
        self.in_stream = in_stream or sys.stdin
        self.files: Dict[int, TextIO] = {}
        self.tracing = False
        self.trace_vars = False
        self.reset()

    def reset(self):
        """Clears the entire program, variables, and state (NEW command)."""
        self.lines: Dict[int, str] = {}
        self.line_order: List[int] = []
        self._clear_vars()
        self.halted = False
        self.stopped = False
        self.pc_idx = -1
        self.stmt_idx = 0
        self._undo_stack: List[Dict[int, str]] = []
        self._redo_stack: List[Dict[int, str]] = []

    def _save_undo(self):
        self._undo_stack.append(self.lines.copy())
        self._redo_stack.clear()
        if len(self._undo_stack) > 100:
            self._undo_stack.pop(0)

    def undo(self) -> bool:
        if not self._undo_stack:
            return False
        self._redo_stack.append(self.lines.copy())
        self.lines = self._undo_stack.pop()
        self.line_order = sorted(self.lines.keys())
        return True

    def redo(self) -> bool:
        if not self._redo_stack:
            return False
        self._undo_stack.append(self.lines.copy())
        self.lines = self._redo_stack.pop()
        self.line_order = sorted(self.lines.keys())
        return True

    def renumber(self, start: int = 10, step: int = 10, from_line: int = 0) -> int:
        self._save_undo()
        old_to_new = {}
        new_lines = {}
        current_new = start
        for num in self.line_order:
            if num >= from_line:
                old_to_new[num] = current_new
                current_new += step
            else:
                new_lines[num] = self.lines[num]
                old_to_new[num] = num
        keywords = ["GOTO", "GOSUB", "THEN", "RESTORE", "TRAP"]
        kw_pattern = r"\b(" + "|".join(keywords) + r")\s+(\d+)\b"

        def replace_ref(match):
            kw = match.group(1)
            old_num = int(match.group(2))
            if old_num in old_to_new:
                return f"{kw} {old_to_new[old_num]}"
            return match.group(0)

        for old_num in self.line_order:
            if old_num >= from_line:
                source = self.lines[old_num]
                new_source = re.sub(
                    kw_pattern, replace_ref, source, flags=re.IGNORECASE
                )
                new_lines[old_to_new[old_num]] = new_source
        self.lines = new_lines
        self.line_order = sorted(self.lines.keys())
        return len(old_to_new)

    def _clear_vars(self):
        self.vars: Dict[str, Union[float, str]] = {}
        self.arrays: Dict[str, List[float]] = {}
        self.string_caps: Dict[str, int] = {}
        self.for_stack: List[ForFrame] = []
        self.gosub_stack: List[GosubFrame] = []

    def print_out(self, text: str, end: str = "\n"):
        self.out_stream.write(text + end)
        self.out_stream.flush()

    def _error(self, message: str):
        raise BasicError(message)

    def _split_statements(self, text: str) -> List[str]:
        stmts = []
        current = []
        in_string = False
        i = 0
        while i < len(text):
            char = text[i]
            if char == '"':
                in_string = not in_string
                current.append(char)
            elif char == ":" and not in_string:
                stmts.append("".join(current))
                current = []
            else:
                current.append(char)
                upper_tail = "".join(current).strip().upper()
                if not in_string and (
                    upper_tail.endswith("REM") or upper_tail.endswith("'")
                ):
                    if upper_tail.endswith("REM"):
                        if len(upper_tail) == 3 or not upper_tail[-4].isalnum():
                            current.extend(text[i + 1 :])
                            break
                    elif upper_tail.endswith("'"):
                        current.extend(text[i + 1 :])
                        break
            i += 1
        stmts.append("".join(current))
        return stmts

    def run_program(self, start_line: Optional[int] = None):
        if start_line is not None:
            if start_line not in self.lines:
                self._error(f"Line {start_line} not found")
            self.pc_idx = self.line_order.index(start_line)
        else:
            self.pc_idx = 0
        self.stmt_idx = 0
        self.halted = False
        self.stopped = False
        self._run_loop()

    def _run_loop(self):
        try:
            while (
                not self.halted
                and not self.stopped
                and 0 <= self.pc_idx < len(self.line_order)
            ):
                line_num = self.line_order[self.pc_idx]
                if self.tracing:
                    self.print_out(f"[{line_num}] ", end="")
                text = self.lines[line_num]
                statements = self._split_statements(text)
                jumped = False
                while self.stmt_idx < len(statements):
                    stmt = statements[self.stmt_idx].strip()
                    if stmt:
                        vars_before = dict(self.vars) if self.trace_vars else None
                        jumped = self._execute_statement(stmt)
                        if self.trace_vars and vars_before is not None:
                            for k, v in self.vars.items():
                                if k not in vars_before or vars_before[k] != v:
                                    val_str = (
                                        f'"{v}"'
                                        if isinstance(v, str)
                                        else (
                                            str(int(v))
                                            if isinstance(v, float) and v == int(v)
                                            else str(v)
                                        )
                                    )
                                    self.print_out(f"  {k} = {val_str}")
                        if self.halted or self.stopped or jumped:
                            break
                    self.stmt_idx += 1
                if not jumped and not self.halted and not self.stopped:
                    self.pc_idx += 1
                    self.stmt_idx = 0
        except BasicError as e:
            line_str = (
                self.line_order[self.pc_idx]
                if 0 <= self.pc_idx < len(self.line_order)
                else "IMMEDIATE"
            )
            self.print_out(f"ERROR: {e} AT LINE {line_str}")
            raise e

    def add_program_line(self, raw_line: str):
        line = raw_line.strip()
        if not line:
            return
        match = re.match(r"^(\d+)\s*(.*)", line)
        if match:
            num = int(match.group(1))
            text = match.group(2).strip()
            if not text:
                if num in self.lines:
                    del self.lines[num]
            else:
                self.lines[num] = text
            self.line_order = sorted(self.lines.keys())
        else:
            self.execute_immediate(line)

    def execute_repl_line(self, raw_line: str):
        self.add_program_line(raw_line)

    def execute_code(self, code: str):
        self.reset()
        for line in code.splitlines():
            self.add_program_line(line.strip())
        self.run_program()

    def run_and_capture(self, code: str) -> str:
        buf = io.StringIO()
        old_out = self.out_stream
        self.out_stream = buf
        try:
            self.execute_code(code)
        finally:
            self.out_stream = old_out
        return buf.getvalue()

    def execute_immediate(self, raw_line: str):
        stmts = self._split_statements(raw_line.strip())
        saved_pc, saved_stmt = self.pc_idx, self.stmt_idx
        self.pc_idx, self.stmt_idx = -1, 0
        jumped = False
        try:
            while self.stmt_idx < len(stmts):
                stmt = stmts[self.stmt_idx].strip()
                if stmt:
                    jumped = self._execute_statement(stmt)
                    if jumped:
                        self._run_loop()
                        break
                    if self.halted or self.stopped:
                        break
                self.stmt_idx += 1
        finally:
            if not jumped:
                self.pc_idx, self.stmt_idx = saved_pc, saved_stmt

    def _execute_statement(self, stmt: str) -> bool:
        scanner = Scanner(stmt)
        scanner.skip_spaces()
        if scanner.consume_keyword("REM") or scanner.peek() == "'":
            self.stmt_idx = 9999
            return False

        # Core Commands as Statements
        if scanner.consume_keyword("RUN"):
            start_line = None
            scanner.skip_spaces()
            if re.match(r"^\d+", scanner.remaining()):
                start_line = int(self._eval_expr(scanner))
            self.run_program(start_line)
            return True
        if scanner.consume_keyword("LIST"):
            self._stmt_list(scanner)
            return False
        if scanner.consume_keyword("NEW"):
            self.reset()
            return True
        if scanner.consume_keyword("CLR"):
            self._clear_vars()
            return False
        if scanner.consume_keyword("CONT"):
            if self.stopped and self.pc_idx >= 0:
                self.stopped = False
                self._run_loop()
                return True
            self._error("Cannot continue")
        if scanner.consume_keyword("RENUMBER") or scanner.consume_keyword("REN"):
            self.renumber()  # Default
            return False
        if scanner.consume_keyword("UNDO"):
            self.undo()
            return False
        if scanner.consume_keyword("REDO"):
            self.redo()
            return False

        if scanner.consume_keyword("PRINT") or scanner.consume_keyword("?"):
            self._stmt_print(scanner)
            return False
        if scanner.consume_keyword("INPUT"):
            self._stmt_input(scanner)
            return False
        if scanner.consume_keyword("LET"):
            self._stmt_let(scanner)
            return False
        if scanner.consume_keyword("GOTO"):
            return self._stmt_goto(scanner)
        if scanner.consume_keyword("GOSUB"):
            return self._stmt_gosub(scanner)
        if scanner.consume_keyword("RETURN"):
            return self._stmt_return(scanner)
        if scanner.consume_keyword("IF"):
            return self._stmt_if(scanner)
        if scanner.consume_keyword("FOR"):
            self._stmt_for(scanner)
            return False
        if scanner.consume_keyword("NEXT"):
            return self._stmt_next(scanner)
        if scanner.consume_keyword("DIM"):
            self._stmt_dim(scanner)
            return False
        if scanner.consume_keyword("END"):
            self.halted = True
            return False
        if scanner.consume_keyword("STOP"):
            self.stopped = True
            return False
        if scanner.consume_keyword("TRON"):
            scanner.skip_spaces()
            if scanner.consume_keyword("VARS"):
                self.trace_vars = True
            self.tracing = True
            return False
        if scanner.consume_keyword("TROFF"):
            self.tracing = False
            self.trace_vars = False
            return False
        if scanner.consume_keyword("OPEN"):
            self._stmt_open(scanner)
            return False
        if scanner.consume_keyword("CLOSE"):
            self._stmt_close(scanner)
            return False
        if re.match(r"^[A-Za-z]", scanner.remaining()):
            self._stmt_let(scanner)
            return False
        self._error("Syntax error")
        return False

    def _stmt_list(self, scanner: Scanner):
        scanner.skip_spaces()
        start = 0
        end = float("inf")
        if scanner.remaining():
            try:
                start = int(self._eval_expr(scanner))
                end = start
                scanner.skip_spaces()
                if scanner.peek() == ",":
                    scanner.advance()
                    end = int(self._eval_expr(scanner))
            except (ValueError, BasicError):
                pass
        for num in self.line_order:
            if start <= num <= end:
                self.print_out(f"{num} {self.lines[num]}")

    def _get_var_ref(self, scanner: Scanner) -> Tuple[str, bool, Optional[int]]:
        scanner.skip_spaces()
        match = re.match(r"^[A-Za-z][A-Za-z0-9_]*\$?", scanner.remaining())
        if not match:
            self._error("Expected variable")
        assert match is not None
        raw_name = match.group(0)
        name, is_string = raw_name.upper(), raw_name.endswith("$")
        scanner.advance(len(raw_name))
        idx = None
        scanner.skip_spaces()
        if scanner.peek() == "(":
            scanner.advance()
            idx = int(self._eval_expr(scanner))
            if idx < 0:
                self._error("Negative array index")
            scanner.skip_spaces()
            if scanner.peek() != ")":
                self._error("Missing ')'")
            scanner.advance()
        return name, is_string, idx

    def _set_var(
        self, name: str, is_string: bool, idx: Optional[int], val: Union[float, str]
    ):
        if is_string:
            if not isinstance(val, str):
                self._error("Type mismatch")
            if name not in self.string_caps:
                self._error("String not dimensioned")
            if len(val) > self.string_caps[name]:
                self._error("String too long")
            self.vars[name] = val
        else:
            if isinstance(val, str):
                self._error("Type mismatch")
            if idx is not None:
                if name not in self.arrays:
                    self._error("Use of undimensioned array")
                if idx >= len(self.arrays[name]):
                    self._error("Array index out of bounds")
                self.arrays[name][idx] = val
            else:
                self.vars[name] = val

    def _stmt_print(self, scanner: Scanner):
        file_out = self.out_stream
        scanner.skip_spaces()
        if scanner.peek() == "#":
            scanner.advance()
            fd = int(self._eval_expr(scanner))
            if fd not in self.files:
                self._error(f"File not open: {fd}")
            file_out = self.files[fd]
            scanner.skip_spaces()
            if scanner.peek() == ",":
                scanner.advance()
        newline = True
        while scanner.remaining():
            scanner.skip_spaces()
            char = scanner.peek()
            if not char:
                break
            if char == ";":
                newline = False
                scanner.advance()
                continue
            elif char == ",":
                newline = False
                scanner.advance()
                file_out.write("\t")
                continue
            val = self._eval_expr(scanner)
            out_str = (
                str(val)
                if isinstance(val, str)
                else (str(int(val)) if val == int(val) else str(val))
            )
            file_out.write(out_str)
            newline = True
        if newline:
            file_out.write("\n")
        file_out.flush()

    def _stmt_input(self, scanner: Scanner):
        file_in, prompt = self.in_stream, "? "
        scanner.skip_spaces()
        if scanner.peek() == "#":
            scanner.advance()
            fd = int(self._eval_expr(scanner))
            if fd not in self.files:
                self._error(f"File not open: {fd}")
            file_in, prompt = self.files[fd], ""
            scanner.skip_spaces()
            if scanner.peek() == ",":
                scanner.advance()
        else:
            if scanner.peek() == '"':
                prompt = str(self._eval_factor(scanner))
                scanner.skip_spaces()
                if scanner.peek() in (";", ","):
                    scanner.advance()
        while True:
            name, is_string, idx = self._get_var_ref(scanner)
            if file_in == self.in_stream:
                self.out_stream.write(prompt)
                self.out_stream.flush()
            raw_in = file_in.readline()
            if not raw_in and file_in != self.in_stream:
                self._error("EOF")
            raw_in = raw_in.rstrip("\r\n")
            if is_string:
                self._set_var(name, is_string, idx, raw_in)
            else:
                try:
                    val = float(raw_in)
                except ValueError:
                    self._error("Input conversion failure")
                    val = 0.0
                self._set_var(name, is_string, idx, val)
            scanner.skip_spaces()
            if scanner.peek() == ",":
                scanner.advance()
                prompt = "? "
                continue
            break

    def _stmt_let(self, scanner: Scanner):
        name, is_string, idx = self._get_var_ref(scanner)
        scanner.skip_spaces()
        if scanner.peek() != "=":
            self._error("Expected '='")
        scanner.advance()
        self._set_var(name, is_string, idx, self._eval_expr(scanner))

    def _stmt_goto(self, scanner: Scanner) -> bool:
        target = int(self._eval_expr(scanner))
        if target not in self.lines:
            self._error(f"Undefined line target {target}")
        self.pc_idx, self.stmt_idx = self.line_order.index(target), 0
        return True

    def _stmt_gosub(self, scanner: Scanner) -> bool:
        target = int(self._eval_expr(scanner))
        if target not in self.lines:
            self._error("Undefined line target")
        self.gosub_stack.append(GosubFrame(self.pc_idx, self.stmt_idx + 1))
        self.pc_idx, self.stmt_idx = self.line_order.index(target), 0
        return True

    def _stmt_return(self, scanner: Scanner) -> bool:
        if not self.gosub_stack:
            self._error("RETURN without GOSUB")
        frame = self.gosub_stack.pop()
        self.pc_idx, self.stmt_idx = frame.line_number, frame.stmt_index
        return True

    def _stmt_if(self, scanner: Scanner) -> bool:
        cond = self._eval_expr(scanner)
        scanner.skip_spaces()
        if not scanner.consume_keyword("THEN"):
            self._error("Expected THEN")
        if (len(cond) > 0) if isinstance(cond, str) else (cond != 0.0):
            scanner.skip_spaces()
            if re.match(r"^\d+", scanner.remaining()):
                return self._stmt_goto(scanner)
            rem = scanner.remaining().strip()
            if rem:
                return self._execute_statement(rem)
            return False
        self.stmt_idx = 9999
        return False

    def _stmt_for(self, scanner: Scanner):
        name, is_string, idx = self._get_var_ref(scanner)
        if is_string or idx is not None:
            self._error("FOR variable must be scalar numeric")
        scanner.skip_spaces()
        if scanner.peek() != "=":
            self._error("Expected '='")
        scanner.advance()
        start_val = self._eval_expr(scanner)
        scanner.skip_spaces()
        if not scanner.consume_keyword("TO"):
            self._error("Expected TO")
        end_val = self._eval_expr(scanner)
        step_val = 1.0
        scanner.skip_spaces()
        if scanner.consume_keyword("STEP"):
            step_val = self._eval_expr(scanner)
        if not all(isinstance(x, float) for x in (start_val, end_val, step_val)):
            self._error("Type mismatch")
        self.vars[name] = start_val
        self.for_stack.append(
            ForFrame(name, end_val, step_val, self.pc_idx, self.stmt_idx)
        )

    def _stmt_next(self, scanner: Scanner) -> bool:
        if not self.for_stack:
            self._error("NEXT without FOR")
        scanner.skip_spaces()
        var_name = (
            self._get_var_ref(scanner)[0]
            if re.match(r"^[A-Za-z]", scanner.remaining())
            else None
        )
        frame_idx = -1
        if var_name:
            for i in range(len(self.for_stack) - 1, -1, -1):
                if self.for_stack[i].var_name == var_name:
                    frame_idx = i
                    break
            if frame_idx == -1:
                self._error("NEXT variable mismatch")
        else:
            frame_idx = len(self.for_stack) - 1
        frame = self.for_stack[frame_idx]
        self.for_stack = self.for_stack[: frame_idx + 1]
        val = self.vars.get(frame.var_name, 0.0) + frame.step
        self.vars[frame.var_name] = val
        if (frame.step >= 0 and val <= frame.end_value) or (
            frame.step < 0 and val >= frame.end_value
        ):
            self.pc_idx, self.stmt_idx = frame.line_number, frame.stmt_index + 1
            return True
        self.for_stack.pop()
        return False

    def _stmt_dim(self, scanner: Scanner):
        while scanner.remaining():
            scanner.skip_spaces()
            name, is_string, idx = self._get_var_ref(scanner)
            if idx is None:
                self._error("DIM requires size")
            if is_string:
                self.string_caps[name], self.vars[name] = idx, ""
            else:
                self.arrays[name] = [0.0] * (idx + 1)
            scanner.skip_spaces()
            if scanner.peek() == ",":
                scanner.advance()
                continue
            break

    def _stmt_open(self, scanner: Scanner):
        scanner.skip_spaces()
        if scanner.peek() != "#":
            self._error("Expected #")
        scanner.advance()
        fd = int(self._eval_expr(scanner))
        scanner.skip_spaces()
        if scanner.peek() != ",":
            self._error("Expected ,")
        scanner.advance()
        filename = self._eval_expr(scanner)
        scanner.skip_spaces()
        if scanner.peek() != ",":
            self._error("Expected ,")
        scanner.advance()
        mode = self._eval_expr(scanner)
        if not isinstance(filename, str) or not isinstance(mode, str):
            self._error("Type mismatch")
        if fd in self.files:
            self.files[fd].close()
        try:
            self.files[fd] = open(filename, "r" if mode.lower() == "r" else "w")
        except Exception as e:
            self._error(f"Cannot open file: {e}")

    def _stmt_close(self, scanner: Scanner):
        scanner.skip_spaces()
        if scanner.peek() != "#":
            self._error("Expected #")
        scanner.advance()
        fd = int(self._eval_expr(scanner))
        if fd in self.files:
            self.files[fd].close()
            del self.files[fd]

    def _eval_expr(self, scanner: Scanner) -> Union[float, str]:
        """Evaluates an expression, handling relational operators with lowest precedence."""
        left = self._eval_sum(scanner)
        while scanner.remaining():
            scanner.skip_spaces()
            rel_op, rem = None, scanner.remaining()
            for r in ("<=", ">=", "<>", "<", ">", "="):
                if rem.startswith(r):
                    rel_op = r
                    break
            if rel_op:
                scanner.advance(len(rel_op))
                right = self._eval_sum(scanner)
                if isinstance(left, type(right)):
                    if rel_op == "=":
                        res = left == right
                    elif rel_op == "<>":
                        res = left != right
                    elif rel_op == "<":
                        res = left < right
                    elif rel_op == ">":
                        res = left > right
                    elif rel_op == "<=":
                        res = left <= right
                    else:  # rel_op == ">="
                        res = left >= right
                    left = 1.0 if res else 0.0
                else:
                    self._error("Type mismatch in comparison")
            else:
                break
        return left

    def _eval_sum(self, scanner: Scanner) -> Union[float, str]:
        """Evaluates addition and subtraction, which have higher precedence than comparisons."""
        left = self._eval_term(scanner)
        while scanner.remaining():
            scanner.skip_spaces()
            op = scanner.peek()
            if op in ("+", "-"):
                scanner.advance()
                right = self._eval_term(scanner)
                if op == "+":
                    if isinstance(left, str) and isinstance(right, str):
                        left = left + right
                    elif isinstance(left, float) and isinstance(right, float):
                        left = left + right
                    else:
                        self._error("Type mismatch")
                else:
                    if isinstance(left, str) or isinstance(right, str):
                        self._error("Type mismatch")
                    left = left - right
            else:
                break
        return left

    def _eval_term(self, scanner: Scanner) -> Union[float, str]:
        left = self._eval_power(scanner)
        while scanner.remaining():
            scanner.skip_spaces()
            op = scanner.peek()
            if op in ("*", "/"):
                scanner.advance()
                right = self._eval_power(scanner)
                if isinstance(left, str) or isinstance(right, str):
                    self._error("Type mismatch")
                if op == "*":
                    left = left * right
                else:
                    if right == 0:
                        self._error("Division by zero")
                    left = left / right
            else:
                break
        return left

    def _eval_power(self, scanner: Scanner) -> Union[float, str]:
        left = self._eval_factor(scanner)
        scanner.skip_spaces()
        if scanner.peek() == "^":
            scanner.advance()
            right = self._eval_power(scanner)
            if isinstance(left, str) or isinstance(right, str):
                self._error("Type mismatch")
            left = math.pow(left, right)
        return left

    def _eval_factor(self, scanner: Scanner) -> Union[float, str]:
        scanner.skip_spaces()
        char = scanner.peek()
        if char == "(":
            scanner.advance()
            val = self._eval_expr(scanner)
            scanner.skip_spaces()
            if scanner.peek() != ")":
                self._error("Missing ')'")
            scanner.advance()
            return val
        if char == '"':
            scanner.advance()
            start = scanner.pos
            while scanner.peek() and scanner.peek() != '"':
                scanner.advance()
            val = scanner.text[start : scanner.pos]
            if scanner.peek() == '"':
                scanner.advance()
            else:
                self._error("Unterminated string")
            return val
        if char == "-":
            scanner.advance()
            val = self._eval_factor(scanner)
            if isinstance(val, str):
                self._error("Type mismatch")
            return -val
        if char == "+":
            scanner.advance()
            return self._eval_factor(scanner)
        # rem = scanner.remaining().upper() # dead code?
        for func in [
            "SIN",
            "COS",
            "TAN",
            "ABS",
            "INT",
            "SQR",
            "SGN",
            "EXP",
            "LOG",
            "RND",
            "LEN",
            "VAL",
            "STR$",
            "CHR$",
            "ASC",
        ]:
            if scanner.match_keyword(func):
                scanner.advance(len(func))
                scanner.skip_spaces()
                if scanner.peek() != "(":
                    self._error(f"Function {func} requires '('")
                scanner.advance()
                arg = self._eval_expr(scanner)
                scanner.skip_spaces()
                if scanner.peek() != ")":
                    self._error("Missing ')'")
                scanner.advance()
                if func == "LEN":
                    return (
                        float(len(arg))
                        if isinstance(arg, str)
                        else self._error("Type mismatch")
                    )
                if func == "VAL":
                    return (
                        float(arg)
                        if isinstance(arg, str)
                        and arg.replace(".", "", 1).replace("-", "", 1).isdigit()
                        else 0.0
                    )
                if func == "STR$":
                    return (
                        str(int(arg))
                        if isinstance(arg, float) and arg == int(arg)
                        else str(arg)
                    )
                if func == "CHR$":
                    return (
                        chr(int(arg))
                        if isinstance(arg, float)
                        else self._error("Type mismatch")
                    )
                if func == "ASC":
                    return float(ord(arg[0])) if isinstance(arg, str) and arg else 0.0
                if isinstance(arg, str):
                    self._error("Type mismatch")
                if func == "SIN":
                    return math.sin(arg)
                if func == "COS":
                    return math.cos(arg)
                if func == "TAN":
                    return math.tan(arg)
                if func == "ABS":
                    return abs(arg)
                if func == "INT":
                    return float(math.floor(arg))
                if func == "SQR":
                    return math.sqrt(arg)
                if func == "SGN":
                    return 1.0 if arg > 0 else (-1.0 if arg < 0 else 0.0)
                if func == "EXP":
                    return math.exp(arg)
                if func == "LOG":
                    return math.log(arg)
                if func == "RND":
                    if arg < 0:
                        random.seed(abs(arg))
                    return random.random()
        match = re.match(r"^[0-9]*\.?[0-9]+([eE][+-]?[0-9]+)?", scanner.remaining())
        if match:
            val_str = match.group(0)
            scanner.advance(len(val_str))
            return float(val_str)
        if char.isalpha():
            name, is_string, idx = self._get_var_ref(scanner)
            if is_string:
                return self.vars.get(name, "")
            if idx is not None:
                if name not in self.arrays:
                    self._error("Use of undimensioned array")
                if idx >= len(self.arrays[name]):
                    self._error("Array index out of bounds")
                return self.arrays[name][idx]
            return self.vars.get(name, 0.0)
        self._error("Syntax error in expression")

    def inject_variable(self, name: str, value: Union[float, str]):
        name = name.upper()
        if isinstance(value, str):
            if not name.endswith("$"):
                name += "$"
            self.string_caps[name], self.vars[name] = max(len(value), 1024), value
        else:
            self.vars[name] = float(value)
