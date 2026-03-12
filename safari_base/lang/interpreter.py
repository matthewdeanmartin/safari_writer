"""Command execution engine for the dBASE language processor."""

from __future__ import annotations

import datetime
import glob
import os
import shutil
from pathlib import Path
from typing import Any

from safari_base.lang.dbf_adapter import (
    TableHandle, copy_structure, create_table, open_table,
)
from safari_base.lang.environment import Environment
from safari_base.lang.errors import (
    DBaseError, NoTableError, ParseError, UnsafeCommandError,
)
from safari_base.lang.functions import call_function
from safari_base.lang.parser import parse, parse_command
from safari_base.lang.types import (
    AppendBlankStmt, AppendFromStmt, AssignStmt, AverageStmt, BinOp,
    CdStmt, CloseStmt, CommandResult, CommentStmt, ContinueStmt,
    CopyFileStmt, CopyStructureStmt, CountStmt, CreateFromStmt,
    CreateTableStmt, DefFnStmt, DeleteStmt, DimHashStmt, DirStmt,
    DisplayStructureStmt, DoCaseStmt, DoProgramStmt, DoWhileStmt,
    EraseStmt, ExitStmt, Expr, FieldRef, ForEachStmt, ForStmt,
    FuncCall, FuncDefStmt, GoStmt, HashAssignStmt, Ident, IfStmt,
    IndexOnStmt, ListStmt, LocateStmt, LogicalLit, LoopStmt, MdStmt,
    NumberLit, PackStmt, PrintStmt, ProcCallStmt, ProcDefStmt,
    QuitStmt, RdStmt, RecallStmt, RenameStmt, ReplaceStmt,
    ReturnStmt, ScanStmt, SeekStmt, SelectStmt, SetDefaultStmt,
    SetDeletedStmt, SetFilterStmt, SetOrderStmt, SetStmt, SkipStmt,
    Stmt, StoreStmt, StringLit, SumStmt, UnaryOp, UseStmt, ZapStmt,
)


class _LoopSignal(Exception):
    """Internal signal for LOOP statement."""


class _ExitSignal(Exception):
    """Internal signal for EXIT statement."""


class _ReturnSignal(Exception):
    """Internal signal for RETURN statement."""
    def __init__(self, value: Any = None) -> None:
        self.value = value


class _QuitSignal(Exception):
    """Internal signal for QUIT statement."""


class Interpreter:
    """Execute dBASE III+ commands against an Environment."""

    def __init__(self, env: Environment | None = None) -> None:
        self.env = env or Environment()

    # -- Public API (three modes from the spec) ------------------------------

    def execute(self, command: str) -> CommandResult:
        """Execute a single command string (command mode)."""
        try:
            stmt = parse_command(command)
            return self._exec_stmt(stmt)
        except _QuitSignal:
            return CommandResult(success=True, message="QUIT")
        except DBaseError as e:
            return CommandResult(success=False, message=str(e))

    def run_program(self, path: Path | str, args: list[str] | None = None) -> CommandResult:
        """Execute a .prg file (program mode)."""
        p = Path(path)
        if not p.suffix:
            p = p.with_suffix(".prg")

        if not p.is_absolute():
            p = self.env.work_dir / p

        if not p.exists():
            return CommandResult(success=False, message=f"Program not found: {p}")

        source = p.read_text(encoding="utf-8")
        return self.run_source(source, program_name=p.stem, args=args)

    def run_source(self, source: str, program_name: str = "<input>", args: list[str] | None = None) -> CommandResult:
        """Execute dBASE source code directly (embedded mode)."""
        try:
            stmts = parse(source)
        except ParseError as e:
            return CommandResult(success=False, message=str(e))

        self.env.push_program(program_name)
        try:
            for stmt in stmts:
                self._exec_stmt(stmt)
            output = self.env.flush_output()
            return CommandResult(success=True, message=output or "OK", data=output)
        except _QuitSignal:
            output = self.env.flush_output()
            return CommandResult(success=True, message=output or "QUIT", data=output)
        except _ReturnSignal:
            output = self.env.flush_output()
            return CommandResult(success=True, message=output or "OK", data=output)
        except DBaseError as e:
            e.program = self.env.current_program
            wa = self.env.current_work_area()
            e.work_area = wa.alias if wa else ""
            return CommandResult(success=False, message=str(e))
        finally:
            self.env.pop_program()

    # -- Statement execution -------------------------------------------------

    def _exec_stmt(self, stmt: Stmt) -> CommandResult:
        if isinstance(stmt, UseStmt):
            return self._exec_use(stmt)
        if isinstance(stmt, SelectStmt):
            return self._exec_select(stmt)
        if isinstance(stmt, CloseStmt):
            return self._exec_close(stmt)
        if isinstance(stmt, GoStmt):
            return self._exec_go(stmt)
        if isinstance(stmt, SkipStmt):
            return self._exec_skip(stmt)
        if isinstance(stmt, StoreStmt):
            return self._exec_store(stmt)
        if isinstance(stmt, AssignStmt):
            return self._exec_assign(stmt)
        if isinstance(stmt, ReplaceStmt):
            return self._exec_replace(stmt)
        if isinstance(stmt, AppendBlankStmt):
            return self._exec_append_blank(stmt)
        if isinstance(stmt, DeleteStmt):
            return self._exec_delete(stmt)
        if isinstance(stmt, RecallStmt):
            return self._exec_recall(stmt)
        if isinstance(stmt, PackStmt):
            return self._exec_pack(stmt)
        if isinstance(stmt, ZapStmt):
            return self._exec_zap(stmt)
        if isinstance(stmt, LocateStmt):
            return self._exec_locate(stmt)
        if isinstance(stmt, ContinueStmt):
            return self._exec_continue(stmt)
        if isinstance(stmt, CreateTableStmt):
            return self._exec_create_table(stmt)
        if isinstance(stmt, CopyStructureStmt):
            return self._exec_copy_structure(stmt)
        if isinstance(stmt, IndexOnStmt):
            return self._exec_index_on(stmt)
        if isinstance(stmt, ListStmt):
            return self._exec_list(stmt)
        if isinstance(stmt, DisplayStructureStmt):
            return self._exec_display_structure(stmt)
        if isinstance(stmt, CountStmt):
            return self._exec_count(stmt)
        if isinstance(stmt, SumStmt):
            return self._exec_sum(stmt)
        if isinstance(stmt, AverageStmt):
            return self._exec_average(stmt)
        if isinstance(stmt, PrintStmt):
            return self._exec_print(stmt)
        if isinstance(stmt, IfStmt):
            return self._exec_if(stmt)
        if isinstance(stmt, DoCaseStmt):
            return self._exec_do_case(stmt)
        if isinstance(stmt, DoWhileStmt):
            return self._exec_do_while(stmt)
        if isinstance(stmt, ForStmt):
            return self._exec_for(stmt)
        if isinstance(stmt, ScanStmt):
            return self._exec_scan(stmt)
        if isinstance(stmt, DoProgramStmt):
            return self._exec_do_program(stmt)
        if isinstance(stmt, ReturnStmt):
            return self._exec_return(stmt)
        if isinstance(stmt, ExitStmt):
            raise _ExitSignal()
        if isinstance(stmt, LoopStmt):
            raise _LoopSignal()
        if isinstance(stmt, QuitStmt):
            raise _QuitSignal()
        if isinstance(stmt, SetDeletedStmt):
            return self._exec_set_deleted(stmt)
        if isinstance(stmt, SetFilterStmt):
            return self._exec_set_filter(stmt)
        if isinstance(stmt, SetDefaultStmt):
            return self._exec_set_default(stmt)
        if isinstance(stmt, SetOrderStmt):
            return self._exec_set_order(stmt)
        if isinstance(stmt, SetStmt):
            return CommandResult(message=f"SET {stmt.setting} noted")
        if isinstance(stmt, DirStmt):
            return self._exec_dir(stmt)
        if isinstance(stmt, CdStmt):
            return self._exec_cd(stmt)
        if isinstance(stmt, RenameStmt):
            return self._exec_rename(stmt)
        if isinstance(stmt, CopyFileStmt):
            return self._exec_copy_file(stmt)
        if isinstance(stmt, EraseStmt):
            return self._exec_erase(stmt)
        if isinstance(stmt, MdStmt):
            return self._exec_md(stmt)
        if isinstance(stmt, RdStmt):
            return self._exec_rd(stmt)
        if isinstance(stmt, SeekStmt):
            return self._exec_seek(stmt)
        if isinstance(stmt, CommentStmt):
            return CommandResult()
        if isinstance(stmt, FuncDefStmt):
            return self._exec_func_def(stmt)
        if isinstance(stmt, ProcDefStmt):
            return self._exec_proc_def(stmt)
        if isinstance(stmt, DefFnStmt):
            return self._exec_def_fn(stmt)
        if isinstance(stmt, ProcCallStmt):
            return self._exec_proc_call(stmt)
        if isinstance(stmt, DimHashStmt):
            return self._exec_dim_hash(stmt)
        if isinstance(stmt, HashAssignStmt):
            return self._exec_hash_assign(stmt)
        if isinstance(stmt, ForEachStmt):
            return self._exec_for_each(stmt)

        return CommandResult(success=False, message=f"Unhandled statement: {type(stmt).__name__}")

    # -- Expression evaluation -----------------------------------------------

    def _eval(self, expr: Expr) -> Any:
        if isinstance(expr, NumberLit):
            return expr.value
        if isinstance(expr, StringLit):
            return expr.value
        if isinstance(expr, LogicalLit):
            return expr.value
        if isinstance(expr, Ident):
            return self._resolve_ident(expr.name)
        if isinstance(expr, FieldRef):
            return self._resolve_field_ref(expr.alias, expr.field_name)
        if isinstance(expr, FuncCall):
            # Check for hashmap access: NAME(key) where NAME is a dict variable
            name_upper = expr.name.upper()
            if name_upper in self.env.variables and isinstance(self.env.variables[name_upper], dict):
                if len(expr.args) != 1:
                    raise DBaseError(f"Hash access {expr.name}() requires exactly 1 key")
                key = str(self._eval(expr.args[0]))
                hmap = self.env.variables[name_upper]
                if key not in hmap:
                    raise DBaseError(f"Key not found in {expr.name}: {key}")
                return hmap[key]
            args = [self._eval(a) for a in expr.args]
            # Check user-defined functions first
            user_fn = self.env.get_user_func(expr.name)
            if user_fn is not None:
                return self._call_user_func(user_fn, args)
            return call_function(expr.name, args, self.env)
        if isinstance(expr, BinOp):
            return self._eval_binop(expr)
        if isinstance(expr, UnaryOp):
            return self._eval_unary(expr)
        raise DBaseError(f"Cannot evaluate expression: {type(expr).__name__}")

    def _resolve_ident(self, name: str) -> Any:
        """Resolve an identifier: check current work area fields first, then variables."""
        wa = self.env.current_work_area()
        if wa is not None and wa.has_field(name):
            return wa.get_field(name)
        upper = name.upper()
        if upper in self.env.variables:
            return self.env.variables[upper]
        # Return the name as a string for flexibility
        raise DBaseError(f"Variable not found: {name}", code="VAR_NOT_FOUND")

    def _resolve_field_ref(self, alias: str, field_name: str) -> Any:
        wa = self.env.get_area_by_alias(alias)
        if wa is None:
            # Try current work area
            wa = self.env.current_work_area()
        if wa is None:
            raise NoTableError(f"No table open for alias '{alias}'")
        return wa.get_field(field_name)

    def _eval_binop(self, expr: BinOp) -> Any:
        left = self._eval(expr.left)
        right = self._eval(expr.right)
        op = expr.op

        if op == "+":
            if isinstance(left, str) and isinstance(right, str):
                return left + right
            return float(left) + float(right)
        if op == "-":
            return float(left) - float(right)
        if op == "*":
            return float(left) * float(right)
        if op == "/":
            r = float(right)
            if r == 0:
                raise DBaseError("Division by zero")
            return float(left) / r
        if op == "^":
            return float(left) ** float(right)

        # Comparisons
        if op in ("=", "=="):
            return self._compare_eq(left, right)
        if op in ("<>", "!="):
            return not self._compare_eq(left, right)
        if op == "<":
            return self._compare_lt(left, right)
        if op == "<=":
            return self._compare_lt(left, right) or self._compare_eq(left, right)
        if op == ">":
            return not self._compare_lt(left, right) and not self._compare_eq(left, right)
        if op == ">=":
            return not self._compare_lt(left, right)

        # Logical
        if op == ".AND.":
            return bool(left) and bool(right)
        if op == ".OR.":
            return bool(left) or bool(right)

        raise DBaseError(f"Unknown operator: {op}")

    def _eval_unary(self, expr: UnaryOp) -> Any:
        val = self._eval(expr.operand)
        if expr.op == "-":
            return -float(val)
        if expr.op == ".NOT.":
            return not bool(val)
        raise DBaseError(f"Unknown unary operator: {expr.op}")

    def _compare_eq(self, a: Any, b: Any) -> bool:
        if isinstance(a, str) and isinstance(b, str):
            return a.rstrip() == b.rstrip()
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            return float(a) == float(b)
        if isinstance(a, bool) and isinstance(b, bool):
            return a == b
        return str(a) == str(b)

    def _compare_lt(self, a: Any, b: Any) -> bool:
        if isinstance(a, str) and isinstance(b, str):
            return a.rstrip() < b.rstrip()
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            return float(a) < float(b)
        return str(a) < str(b)

    def _truthy(self, val: Any) -> bool:
        if isinstance(val, bool):
            return val
        if isinstance(val, (int, float)):
            return val != 0
        if isinstance(val, str):
            return len(val.strip()) > 0
        return bool(val)

    # -- Command implementations ---------------------------------------------

    def _exec_use(self, stmt: UseStmt) -> CommandResult:
        if not stmt.table:
            self.env.close_current()
            return CommandResult(message="Table closed")
        path = self.env.resolve_dbf_path(stmt.table)
        if not Path(path).exists():
            raise DBaseError(f"Table not found: {path}")
        raw_table = open_table(path, stmt.exclusive)
        alias = stmt.alias or Path(path).stem
        handle = TableHandle(raw_table, alias, stmt.exclusive)
        handle.go_top()
        self.env.open_table(handle)
        return CommandResult(message=f"Table {alias} opened with {handle.record_count} records")

    def _exec_select(self, stmt: SelectStmt) -> CommandResult:
        self.env.select_area(stmt.area)
        return CommandResult(message=f"Work area {self.env.active_area}")

    def _exec_close(self, stmt: CloseStmt) -> CommandResult:
        self.env.close_current()
        return CommandResult(message="Table closed")

    def _exec_go(self, stmt: GoStmt) -> CommandResult:
        wa = self.env.require_work_area()
        if stmt.target == "TOP":
            wa.go_top()
            return CommandResult(message=f"Record {wa.recno}")
        if stmt.target == "BOTTOM":
            wa.go_bottom()
            return CommandResult(message=f"Record {wa.recno}")
        n = int(self._eval(stmt.target))
        wa.go_record(n)
        return CommandResult(message=f"Record {wa.recno}")

    def _exec_skip(self, stmt: SkipStmt) -> CommandResult:
        wa = self.env.require_work_area()
        count = int(self._eval(stmt.count)) if stmt.count else 1
        wa.skip(count)
        return CommandResult(message=f"Record {wa.recno}")

    def _exec_store(self, stmt: StoreStmt) -> CommandResult:
        val = self._eval(stmt.expr)
        self.env.set_var(stmt.var, val)
        return CommandResult(message=f"{stmt.var} = {val}")

    def _exec_assign(self, stmt: AssignStmt) -> CommandResult:
        val = self._eval(stmt.expr)
        self.env.set_var(stmt.var, val)
        return CommandResult(message=f"{stmt.var} = {val}")

    def _exec_replace(self, stmt: ReplaceStmt) -> CommandResult:
        wa = self.env.require_work_area()

        if stmt.scope == "ALL":
            count = 0
            wa.go_top()
            while not wa.eof:
                if stmt.condition is None or self._truthy(self._eval(stmt.condition)):
                    for field_name, expr in stmt.assignments:
                        val = self._eval(expr)
                        wa.set_field(field_name, val)
                    count += 1
                wa.skip(1)
            return CommandResult(message=f"{count} records replaced", rows_affected=count)
        else:
            if stmt.condition is not None and not self._truthy(self._eval(stmt.condition)):
                return CommandResult(message="Condition not met")
            for field_name, expr in stmt.assignments:
                val = self._eval(expr)
                wa.set_field(field_name, val)
            return CommandResult(message="1 record replaced", rows_affected=1)

    def _exec_append_blank(self, stmt: AppendBlankStmt) -> CommandResult:
        wa = self.env.require_work_area()
        recno = wa.append_blank()
        return CommandResult(message=f"Record {recno} appended", rows_affected=1)

    def _exec_delete(self, stmt: DeleteStmt) -> CommandResult:
        wa = self.env.require_work_area()
        if stmt.scope == "ALL":
            count = 0
            wa.go_top()
            while not wa.eof:
                if stmt.condition is None or self._truthy(self._eval(stmt.condition)):
                    wa.delete_current()
                    count += 1
                wa.skip(1)
            return CommandResult(message=f"{count} records deleted", rows_affected=count)
        else:
            wa.delete_current()
            return CommandResult(message="Record deleted", rows_affected=1)

    def _exec_recall(self, stmt: RecallStmt) -> CommandResult:
        wa = self.env.require_work_area()
        if stmt.scope == "ALL":
            count = 0
            wa.go_top()
            while not wa.eof:
                if stmt.condition is None or self._truthy(self._eval(stmt.condition)):
                    wa.recall_current()
                    count += 1
                wa.skip(1)
            return CommandResult(message=f"{count} records recalled", rows_affected=count)
        else:
            wa.recall_current()
            return CommandResult(message="Record recalled", rows_affected=1)

    def _exec_pack(self, stmt: PackStmt) -> CommandResult:
        wa = self.env.require_work_area()
        removed = wa.pack()
        return CommandResult(message=f"{removed} records removed", rows_affected=removed)

    def _exec_zap(self, stmt: ZapStmt) -> CommandResult:
        if not self.env.unsafe:
            raise UnsafeCommandError("ZAP")
        wa = self.env.require_work_area()
        count = wa.zap()
        return CommandResult(message=f"{count} records zapped", rows_affected=count)

    def _exec_locate(self, stmt: LocateStmt) -> CommandResult:
        wa = self.env.require_work_area()
        wa._locate_condition = stmt.condition
        wa.go_top()
        while not wa.eof:
            if self._truthy(self._eval(stmt.condition)):
                wa._found = True
                wa._locate_recno = wa._recno
                return CommandResult(message=f"Record {wa.recno}")
            wa.skip(1)
        wa._found = False
        return CommandResult(message="Not found")

    def _exec_continue(self, stmt: ContinueStmt) -> CommandResult:
        wa = self.env.require_work_area()
        if wa._locate_condition is None:
            raise DBaseError("No active LOCATE to continue")
        wa.skip(1)
        while not wa.eof:
            if self._truthy(self._eval(wa._locate_condition)):
                wa._found = True
                wa._locate_recno = wa._recno
                return CommandResult(message=f"Record {wa.recno}")
            wa.skip(1)
        wa._found = False
        return CommandResult(message="Not found")

    def _exec_seek(self, stmt: SeekStmt) -> CommandResult:
        wa = self.env.require_work_area()
        if wa._order is None:
            raise DBaseError("No active order for SEEK — use INDEX ON first", code="NO_ORDER")
        target = self._eval(stmt.expr)
        # Linear search in the ordered records
        for idx in wa._order:
            wa.go_record(idx + 1)
            # Compare the first field as the key (simplified)
            key = wa.get_field(wa.field_names()[0])
            if self._compare_eq(key, target):
                wa._found = True
                return CommandResult(message=f"Found at record {wa.recno}")
        wa._found = False
        wa.go_top()
        return CommandResult(message="Not found")

    def _exec_create_table(self, stmt: CreateTableStmt) -> CommandResult:
        path = self.env.resolve_dbf_path(stmt.table)
        if Path(path).exists():
            raise DBaseError(f"Table already exists: {path}")
        raw_table = create_table(path, stmt.columns)
        alias = Path(path).stem
        handle = TableHandle(raw_table, alias)
        self.env.open_table(handle)
        return CommandResult(message=f"Table {alias} created")

    def _exec_copy_structure(self, stmt: CopyStructureStmt) -> CommandResult:
        wa = self.env.require_work_area()
        path = self.env.resolve_dbf_path(stmt.target)
        copy_structure(wa, path, stmt.extended)
        label = "extended " if stmt.extended else ""
        return CommandResult(message=f"Structure {label}copied to {stmt.target}")

    def _exec_index_on(self, stmt: IndexOnStmt) -> CommandResult:
        wa = self.env.require_work_area()
        # Build an in-memory index by evaluating the expression for each record
        keys: list[tuple[Any, int]] = []
        saved_recno = wa._recno
        wa.go_top()
        while not wa.eof:
            key = self._eval(stmt.expr)
            keys.append((key, wa._recno))
            wa.skip(1)
        keys.sort(key=lambda x: (str(x[0]), x[1]))
        wa._order = [rec for _, rec in keys]
        wa._order_tag = stmt.tag or "default"
        wa._recno = saved_recno
        wa._eof = saved_recno >= wa.record_count
        return CommandResult(message=f"Index created: {wa._order_tag} ({len(keys)} keys)")

    def _exec_list(self, stmt: ListStmt) -> CommandResult:
        wa = self.env.require_work_area()
        fields = stmt.fields or wa.field_names()

        # Header
        header = " | ".join(f"{f:<12}" for f in fields)
        self.env.emit(header)
        self.env.emit("-" * len(header))

        count = 0
        wa.go_top()
        while not wa.eof:
            if self.env.deleted_on and wa.is_deleted():
                wa.skip(1)
                continue
            if stmt.condition is not None and not self._truthy(self._eval(stmt.condition)):
                wa.skip(1)
                continue
            values = []
            for f in fields:
                val = wa.get_field(f)
                values.append(f"{val!s:<12}")
            deleted_marker = "*" if wa.is_deleted() else " "
            self.env.emit(f"{wa.recno:>4}{deleted_marker}| " + " | ".join(values))
            count += 1
            wa.skip(1)

        self.env.emit(f"\n{count} records listed")
        return CommandResult(message=f"{count} records listed", rows_affected=count)

    def _exec_display_structure(self, stmt: DisplayStructureStmt) -> CommandResult:
        wa = self.env.require_work_area()
        self.env.emit(f"Structure for table: {wa.alias}")
        self.env.emit(f"Number of records: {wa.record_count}")
        self.env.emit(f"{'Field':<12} {'Type':<6} {'Width':>5} {'Dec':>4}")
        self.env.emit("-" * 30)
        for name, type_char, width, decimals in wa.field_info():
            self.env.emit(f"{name:<12} {type_char:<6} {width:>5} {decimals:>4}")
        return CommandResult(message=f"Structure displayed for {wa.alias}")

    def _exec_count(self, stmt: CountStmt) -> CommandResult:
        wa = self.env.require_work_area()
        count = 0
        wa.go_top()
        while not wa.eof:
            if self.env.deleted_on and wa.is_deleted():
                wa.skip(1)
                continue
            if stmt.condition is None or self._truthy(self._eval(stmt.condition)):
                count += 1
            wa.skip(1)
        if stmt.to_var:
            self.env.set_var(stmt.to_var, float(count))
        self.env.emit(f"{count} records")
        return CommandResult(message=f"{count} records", data=count)

    def _exec_sum(self, stmt: SumStmt) -> CommandResult:
        wa = self.env.require_work_area()
        total = 0.0
        wa.go_top()
        while not wa.eof:
            if self.env.deleted_on and wa.is_deleted():
                wa.skip(1)
                continue
            if stmt.condition is None or self._truthy(self._eval(stmt.condition)):
                total += float(self._eval(stmt.expr))
            wa.skip(1)
        if stmt.to_var:
            self.env.set_var(stmt.to_var, total)
        self.env.emit(f"Sum: {total}")
        return CommandResult(message=f"Sum: {total}", data=total)

    def _exec_average(self, stmt: AverageStmt) -> CommandResult:
        wa = self.env.require_work_area()
        total = 0.0
        count = 0
        wa.go_top()
        while not wa.eof:
            if self.env.deleted_on and wa.is_deleted():
                wa.skip(1)
                continue
            if stmt.condition is None or self._truthy(self._eval(stmt.condition)):
                total += float(self._eval(stmt.expr))
                count += 1
            wa.skip(1)
        avg = total / count if count > 0 else 0.0
        if stmt.to_var:
            self.env.set_var(stmt.to_var, avg)
        self.env.emit(f"Average: {avg}")
        return CommandResult(message=f"Average: {avg}", data=avg)

    def _exec_print(self, stmt: PrintStmt) -> CommandResult:
        parts: list[str] = []
        for expr in stmt.exprs:
            val = self._eval(expr)
            parts.append(str(val))
        text = " ".join(parts) if parts else ""
        self.env.emit(text)
        return CommandResult(message=text)

    # -- Control flow --------------------------------------------------------

    def _exec_if(self, stmt: IfStmt) -> CommandResult:
        if self._truthy(self._eval(stmt.condition)):
            for s in stmt.then_body:
                self._exec_stmt(s)
            return CommandResult()

        for ei_cond, ei_body in stmt.elseif_clauses:
            if self._truthy(self._eval(ei_cond)):
                for s in ei_body:
                    self._exec_stmt(s)
                return CommandResult()

        for s in stmt.else_body:
            self._exec_stmt(s)
        return CommandResult()

    def _exec_do_case(self, stmt: DoCaseStmt) -> CommandResult:
        for case_cond, case_body in stmt.cases:
            if self._truthy(self._eval(case_cond)):
                for s in case_body:
                    self._exec_stmt(s)
                return CommandResult()
        for s in stmt.otherwise:
            self._exec_stmt(s)
        return CommandResult()

    def _exec_do_while(self, stmt: DoWhileStmt) -> CommandResult:
        iterations = 0
        max_iter = 1_000_000
        while self._truthy(self._eval(stmt.condition)):
            iterations += 1
            if iterations > max_iter:
                raise DBaseError("DO WHILE loop exceeded maximum iterations")
            try:
                for s in stmt.body:
                    self._exec_stmt(s)
            except _LoopSignal:
                continue
            except _ExitSignal:
                break
        return CommandResult(message=f"Loop completed ({iterations} iterations)")

    def _exec_for(self, stmt: ForStmt) -> CommandResult:
        start = float(self._eval(stmt.start))
        end = float(self._eval(stmt.end))
        step = float(self._eval(stmt.step)) if stmt.step else 1.0

        self.env.set_var(stmt.var, start)
        iterations = 0
        max_iter = 1_000_000

        while True:
            current = float(self.env.get_var(stmt.var))
            if step > 0 and current > end:
                break
            if step < 0 and current < end:
                break
            iterations += 1
            if iterations > max_iter:
                raise DBaseError("FOR loop exceeded maximum iterations")
            try:
                for s in stmt.body:
                    self._exec_stmt(s)
            except _LoopSignal:
                pass
            except _ExitSignal:
                break
            self.env.set_var(stmt.var, current + step)

        return CommandResult(message=f"FOR completed ({iterations} iterations)")

    def _exec_scan(self, stmt: ScanStmt) -> CommandResult:
        wa = self.env.require_work_area()
        count = 0
        wa.go_top()

        while not wa.eof:
            if self.env.deleted_on and wa.is_deleted():
                wa.skip(1)
                continue
            if stmt.condition is not None and not self._truthy(self._eval(stmt.condition)):
                wa.skip(1)
                continue
            count += 1
            try:
                for s in stmt.body:
                    self._exec_stmt(s)
            except _LoopSignal:
                wa.skip(1)
                continue
            except _ExitSignal:
                break
            wa.skip(1)

        return CommandResult(message=f"SCAN completed ({count} records)", rows_affected=count)

    def _exec_do_program(self, stmt: DoProgramStmt) -> CommandResult:
        return self.run_program(stmt.program, [str(self._eval(a)) for a in stmt.args])

    def _exec_return(self, stmt: ReturnStmt) -> CommandResult:
        val = self._eval(stmt.expr) if stmt.expr else None
        raise _ReturnSignal(val)

    # -- User-defined functions/procedures -----------------------------------

    def _exec_func_def(self, stmt: FuncDefStmt) -> CommandResult:
        self.env.define_user_func(stmt.name, stmt)
        return CommandResult(message=f"Function {stmt.name} defined")

    def _exec_proc_def(self, stmt: ProcDefStmt) -> CommandResult:
        self.env.define_user_func(stmt.name, stmt)
        return CommandResult(message=f"Procedure {stmt.name} defined")

    def _exec_def_fn(self, stmt: DefFnStmt) -> CommandResult:
        # Store with FN_ prefix to match the parser's FN call convention
        self.env.define_user_func("FN_" + stmt.name, stmt)
        return CommandResult(message=f"FN {stmt.name} defined")

    def _exec_proc_call(self, stmt: ProcCallStmt) -> CommandResult:
        args = [self._eval(a) for a in stmt.args]
        user_fn = self.env.get_user_func(stmt.name)
        if user_fn is None:
            raise DBaseError(f"Undefined procedure: {stmt.name}")
        self._call_user_func(user_fn, args)
        return CommandResult()

    def _call_user_func(self, defn: FuncDefStmt | ProcDefStmt | DefFnStmt, args: list[Any]) -> Any:
        """Execute a user-defined function/procedure and return the result."""
        params = defn.params
        if len(args) != len(params):
            raise DBaseError(
                f"{defn.name}() expects {len(params)} argument(s), got {len(args)}"
            )

        # Save existing variables that will be shadowed by params
        saved: dict[str, Any] = {}
        for i, p in enumerate(params):
            key = p.upper()
            if key in self.env.variables:
                saved[key] = self.env.variables[key]
            self.env.variables[key] = args[i]

        try:
            if isinstance(defn, DefFnStmt):
                # One-liner: just evaluate the expression
                result = self._eval(defn.expr)
            else:
                # Multi-line body
                result = None
                try:
                    for s in defn.body:
                        self._exec_stmt(s)
                except _ReturnSignal as ret:
                    result = ret.value
            return result
        finally:
            # Restore saved variables, remove params that weren't previously defined
            for p in params:
                key = p.upper()
                if key in saved:
                    self.env.variables[key] = saved[key]
                else:
                    self.env.variables.pop(key, None)

    # -- Hashmaps ------------------------------------------------------------

    def _exec_dim_hash(self, stmt: DimHashStmt) -> CommandResult:
        self.env.set_var(stmt.name, {})
        return CommandResult(message=f"Hash {stmt.name} created")

    def _exec_hash_assign(self, stmt: HashAssignStmt) -> CommandResult:
        name_upper = stmt.name.upper()
        if name_upper not in self.env.variables or not isinstance(self.env.variables[name_upper], dict):
            raise DBaseError(f"{stmt.name} is not a hashmap — use DIM {stmt.name}{{}} first")
        key = str(self._eval(stmt.key))
        val = self._eval(stmt.expr)
        self.env.variables[name_upper][key] = val
        return CommandResult(message=f"{stmt.name}({key}) = {val}")

    def _exec_for_each(self, stmt: ForEachStmt) -> CommandResult:
        name_upper = stmt.hashmap.upper()
        if name_upper not in self.env.variables or not isinstance(self.env.variables[name_upper], dict):
            raise DBaseError(f"{stmt.hashmap} is not a hashmap")
        hmap = self.env.variables[name_upper]
        iterations = 0
        max_iter = 1_000_000
        for key in list(hmap.keys()):
            iterations += 1
            if iterations > max_iter:
                raise DBaseError("FOR EACH loop exceeded maximum iterations")
            self.env.set_var(stmt.var, key)
            try:
                for s in stmt.body:
                    self._exec_stmt(s)
            except _LoopSignal:
                continue
            except _ExitSignal:
                break
        return CommandResult(message=f"FOR EACH completed ({iterations} iterations)")

    # -- Settings ------------------------------------------------------------

    def _exec_set_deleted(self, stmt: SetDeletedStmt) -> CommandResult:
        self.env.deleted_on = stmt.on
        state = "ON" if stmt.on else "OFF"
        return CommandResult(message=f"SET DELETED {state}")

    def _exec_set_filter(self, stmt: SetFilterStmt) -> CommandResult:
        wa = self.env.current_work_area()
        if wa:
            wa._filter_expr = stmt.condition
        msg = "Filter cleared" if stmt.condition is None else "Filter set"
        return CommandResult(message=msg)

    def _exec_set_default(self, stmt: SetDefaultStmt) -> CommandResult:
        path = self.env.resolve_path(stmt.path)
        if not path.is_dir():
            raise DBaseError(f"Not a directory: {path}")
        self.env.default_dir = path
        return CommandResult(message=f"Default directory: {path}")

    def _exec_set_order(self, stmt: SetOrderStmt) -> CommandResult:
        wa = self.env.current_work_area()
        if wa:
            if not stmt.tag:
                wa._order = None
                wa._order_tag = ""
                return CommandResult(message="Order cleared")
            if wa._order_tag.upper() == stmt.tag.upper():
                return CommandResult(message=f"Order set to {stmt.tag}")
            raise DBaseError(f"Order tag not found: {stmt.tag}")
        return CommandResult(message="No table open")

    # -- OS commands ---------------------------------------------------------

    def _exec_dir(self, stmt: DirStmt) -> CommandResult:
        target = self.env.work_dir
        pattern = stmt.pattern.strip() if stmt.pattern else "*"
        entries = sorted(target.glob(pattern))
        lines: list[str] = []
        for entry in entries:
            kind = "<DIR>" if entry.is_dir() else f"{entry.stat().st_size:>8}"
            lines.append(f"  {kind}  {entry.name}")
        text = "\n".join(lines) if lines else "(empty)"
        self.env.emit(text)
        return CommandResult(message=f"{len(entries)} entries", data=lines)

    def _exec_cd(self, stmt: CdStmt) -> CommandResult:
        path = self.env.resolve_path(stmt.path)
        if not path.is_dir():
            raise DBaseError(f"Not a directory: {path}")
        self.env.work_dir = path
        return CommandResult(message=f"Directory: {path}")

    def _exec_rename(self, stmt: RenameStmt) -> CommandResult:
        old_path = self.env.resolve_path(stmt.old)
        new_path = self.env.resolve_path(stmt.new)
        if not old_path.exists():
            raise DBaseError(f"File not found: {old_path}")
        old_path.rename(new_path)
        return CommandResult(message=f"Renamed {stmt.old} to {stmt.new}")

    def _exec_copy_file(self, stmt: CopyFileStmt) -> CommandResult:
        src = self.env.resolve_path(stmt.source)
        dst = self.env.resolve_path(stmt.target)
        if not src.exists():
            raise DBaseError(f"File not found: {src}")
        shutil.copy2(str(src), str(dst))
        return CommandResult(message=f"Copied {stmt.source} to {stmt.target}")

    def _exec_erase(self, stmt: EraseStmt) -> CommandResult:
        if not self.env.unsafe:
            raise UnsafeCommandError("ERASE")
        path = self.env.resolve_path(stmt.filename)
        if not path.exists():
            raise DBaseError(f"File not found: {path}")
        path.unlink()
        return CommandResult(message=f"Erased {stmt.filename}")

    def _exec_md(self, stmt: MdStmt) -> CommandResult:
        path = self.env.resolve_path(stmt.dirname)
        path.mkdir(parents=True, exist_ok=True)
        return CommandResult(message=f"Directory created: {stmt.dirname}")

    def _exec_rd(self, stmt: RdStmt) -> CommandResult:
        if not self.env.unsafe:
            raise UnsafeCommandError("RD")
        path = self.env.resolve_path(stmt.dirname)
        if not path.is_dir():
            raise DBaseError(f"Not a directory: {path}")
        path.rmdir()
        return CommandResult(message=f"Directory removed: {stmt.dirname}")
