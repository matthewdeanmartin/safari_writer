"""Recursive-descent parser for the dBASE language processor."""

from __future__ import annotations

from safari_base.lang.errors import ParseError
from safari_base.lang.lexer import tokenize
from safari_base.lang.types import (AppendBlankStmt, AppendFromStmt,
                                    AssignStmt, AverageStmt, BinOp, CdStmt,
                                    CloseStmt, CommentStmt, ContinueStmt,
                                    CopyFileStmt, CopyStructureStmt, CountStmt,
                                    CreateFromStmt, CreateTableStmt, DefFnStmt,
                                    DeleteStmt, DimHashStmt, DirStmt,
                                    DisplayStructureStmt, DoCaseStmt,
                                    DoProgramStmt, DoWhileStmt, EraseStmt,
                                    ExitStmt, Expr, FieldRef, ForEachStmt,
                                    ForStmt, FuncCall, FuncDefStmt, GoStmt,
                                    HashAccessExpr, HashAssignStmt, Ident,
                                     IfStmt, IndexOnStmt, ListStmt, LocateStmt,
                                     InsertStmt, LogicalLit, LoopStmt, MdStmt, NumberLit,
                                     PackStmt, PrintStmt, ProcCallStmt,
                                    ProcDefStmt, QuitStmt, RdStmt, RecallStmt,
                                    RenameStmt, ReplaceStmt, ReturnStmt,
                                    ScanStmt, SeekStmt, SelectStmt,
                                    SetDefaultStmt, SetDeletedStmt,
                                    SetFilterStmt, SetOrderStmt, SetStmt,
                                    SkipStmt, Stmt, StoreStmt, StringLit,
                                    SumStmt, Token, TokenType, UnaryOp,
                                    UseStmt, ZapStmt)


class Parser:
    """Recursive descent parser for dBASE III+ commands."""

    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.pos = 0

    # -- Token helpers -------------------------------------------------------

    def _peek(self) -> Token:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return Token(TokenType.EOF, "", 0)

    def _advance(self) -> Token:
        tok = self._peek()
        self.pos += 1
        return tok

    def _expect(self, ttype: TokenType, value: str | None = None) -> Token:
        tok = self._peek()
        if tok.type != ttype:
            raise ParseError(
                f"Expected {ttype.name} but got {tok.type.name} '{tok.value}'",
                line_number=tok.line,
            )
        if value is not None and tok.value.upper() != value.upper():
            raise ParseError(
                f"Expected '{value}' but got '{tok.value}'",
                line_number=tok.line,
            )
        return self._advance()

    def _match_keyword(self, *keywords: str) -> Token | None:
        tok = self._peek()
        if tok.type == TokenType.KEYWORD and tok.value.upper() in keywords:
            return self._advance()
        return None

    def _match_type(self, ttype: TokenType) -> Token | None:
        if self._peek().type == ttype:
            return self._advance()
        return None

    def _at_end_of_statement(self) -> bool:
        return self._peek().type in (TokenType.NEWLINE, TokenType.EOF)

    def _skip_newlines(self) -> None:
        while self._peek().type == TokenType.NEWLINE:
            self._advance()

    def _consume_to_eol(self) -> str:
        """Consume remaining tokens on this line, return as string."""
        parts: list[str] = []
        while not self._at_end_of_statement():
            parts.append(self._advance().value)
        return " ".join(parts)

    def _read_ident_or_string(self) -> str:
        """Read an identifier or string token and return its value."""
        tok = self._peek()
        if tok.type == TokenType.IDENT:
            return self._advance().value
        if tok.type == TokenType.STRING:
            return self._advance().value
        if tok.type == TokenType.KEYWORD:
            # Allow keywords as identifiers in some contexts (e.g., file names)
            return self._advance().value
        raise ParseError(
            f"Expected identifier but got {tok.type.name}", line_number=tok.line
        )

    # -- Expression parser (Pratt-style precedence climbing) -----------------

    def _parse_expr(self) -> Expr:
        return self._parse_or()

    def _parse_or(self) -> Expr:
        left = self._parse_and()
        while self._match_type(TokenType.DOT_OR):
            right = self._parse_and()
            left = BinOp(".OR.", left, right)
        return left

    def _parse_and(self) -> Expr:
        left = self._parse_not()
        while self._match_type(TokenType.DOT_AND):
            right = self._parse_not()
            left = BinOp(".AND.", left, right)
        return left

    def _parse_not(self) -> Expr:
        if self._match_type(TokenType.DOT_NOT):
            operand = self._parse_not()
            return UnaryOp(".NOT.", operand)
        return self._parse_comparison()

    def _parse_comparison(self) -> Expr:
        left = self._parse_addition()
        ops = {
            TokenType.EQ: "=",
            TokenType.EQEQ: "==",
            TokenType.NEQ: "<>",
            TokenType.BANGEQ: "!=",
            TokenType.LT: "<",
            TokenType.LE: "<=",
            TokenType.GT: ">",
            TokenType.GE: ">=",
        }
        for ttype, op_str in ops.items():
            if self._match_type(ttype):
                right = self._parse_addition()
                return BinOp(op_str, left, right)
        return left

    def _parse_addition(self) -> Expr:
        left = self._parse_multiplication()
        while True:
            if self._match_type(TokenType.PLUS):
                right = self._parse_multiplication()
                left = BinOp("+", left, right)
            elif self._match_type(TokenType.MINUS):
                right = self._parse_multiplication()
                left = BinOp("-", left, right)
            else:
                break
        return left

    def _parse_multiplication(self) -> Expr:
        left = self._parse_power()
        while True:
            if self._match_type(TokenType.STAR):
                right = self._parse_power()
                left = BinOp("*", left, right)
            elif self._match_type(TokenType.SLASH):
                right = self._parse_power()
                left = BinOp("/", left, right)
            else:
                break
        return left

    def _parse_power(self) -> Expr:
        left = self._parse_unary()
        if self._match_type(TokenType.CARET):
            right = self._parse_unary()
            left = BinOp("^", left, right)
        return left

    def _parse_unary(self) -> Expr:
        if self._match_type(TokenType.MINUS):
            operand = self._parse_unary()
            return UnaryOp("-", operand)
        return self._parse_primary()

    def _parse_primary(self) -> Expr:
        tok = self._peek()

        if tok.type == TokenType.NUMBER:
            self._advance()
            return NumberLit(float(tok.value))

        if tok.type == TokenType.STRING:
            self._advance()
            return StringLit(tok.value)

        if tok.type == TokenType.LOGICAL:
            self._advance()
            return LogicalLit(tok.value.upper() == ".T.")

        if tok.type == TokenType.LPAREN:
            self._advance()
            expr = self._parse_expr()
            self._expect(TokenType.RPAREN)
            return expr

        if tok.type in (TokenType.IDENT, TokenType.KEYWORD):
            # Handle FN name(args) — DEF FN call syntax
            if tok.type == TokenType.KEYWORD and tok.value.upper() == "FN":
                self._advance()  # consume FN
                fn_name = self._read_ident_or_string().upper()
                self._expect(TokenType.LPAREN)
                args: list[Expr] = []
                if self._peek().type != TokenType.RPAREN:
                    args.append(self._parse_expr())
                    while self._match_type(TokenType.COMMA):
                        args.append(self._parse_expr())
                self._expect(TokenType.RPAREN)
                return FuncCall("FN_" + fn_name, args)
            name = self._advance().value
            # Check for function call
            if self._peek().type == TokenType.LPAREN:
                self._advance()  # consume (
                args2: list[Expr] = []
                if self._peek().type != TokenType.RPAREN:
                    args2.append(self._parse_expr())
                    while self._match_type(TokenType.COMMA):
                        args2.append(self._parse_expr())
                self._expect(TokenType.RPAREN)
                return FuncCall(name.upper(), args2)
            # Check for alias->field
            if self._peek().type == TokenType.ARROW:
                self._advance()  # consume ->
                field_name = self._read_ident_or_string()
                return FieldRef(name, field_name)
            return Ident(name)

        raise ParseError(
            f"Unexpected token: {tok.type.name} '{tok.value}'", line_number=tok.line
        )

    # -- Statement parser ----------------------------------------------------

    def parse_program(self) -> list[Stmt]:
        """Parse a full program (multiple statements)."""
        statements: list[Stmt] = []
        self._skip_newlines()
        while self._peek().type != TokenType.EOF:
            stmt = self._parse_statement()
            if stmt is not None:
                statements.append(stmt)
            self._skip_newlines()
        return statements

    def _parse_statement(self) -> Stmt | None:
        tok = self._peek()
        line = tok.line

        if tok.type == TokenType.NEWLINE:
            self._advance()
            return None

        if tok.type == TokenType.EOF:
            return None

        # ? print
        if tok.type == TokenType.KEYWORD and tok.value == "?":
            return self._parse_print(line)

        # Assignment: ident = expr  (but only if next-next is =)
        if tok.type == TokenType.IDENT:
            # Lookahead for assignment
            if (
                self.pos + 1 < len(self.tokens)
                and self.tokens[self.pos + 1].type == TokenType.EQ
            ):
                name = self._advance().value
                self._advance()  # consume =
                expr = self._parse_expr()
                self._skip_to_eol()
                return AssignStmt(var=name, expr=expr, line=line)

        if tok.type != TokenType.KEYWORD:
            # Try as assignment or expression
            if tok.type == TokenType.IDENT:
                return self._parse_ident_statement(line)
            raise ParseError(f"Unexpected token: {tok.value}", line_number=line)

        kw = tok.value.upper()

        # Check if this keyword is actually being used as a variable assignment
        # e.g., "count = count + 1" where COUNT is a keyword
        if (
            self.pos + 1 < len(self.tokens)
            and self.tokens[self.pos + 1].type == TokenType.EQ
            and kw
            not in (
                "IF",
                "DO",
                "FOR",
                "SCAN",
                "SET",
                "CREATE",
                "COPY",
                "INDEX",
                "DISPLAY",
                "ENDIF",
                "ENDDO",
                "ENDFOR",
                "ENDSCAN",
                "ENDCASE",
                "ELSE",
                "ELSEIF",
                "CASE",
                "OTHERWISE",
            )
        ):
            name = self._advance().value
            self._advance()  # consume =
            expr = self._parse_expr()
            self._skip_to_eol()
            return AssignStmt(var=name, expr=expr, line=line)

        if kw == "USE":
            return self._parse_use(line)
        if kw == "SELECT":
            return self._parse_select(line)
        if kw == "CLOSE":
            self._advance()
            self._skip_to_eol()
            return CloseStmt(line=line)
        if kw in ("GO", "GOTO"):
            return self._parse_go(line)
        if kw == "SKIP":
            return self._parse_skip(line)
        if kw == "STORE":
            return self._parse_store(line)
        if kw == "REPLACE":
            return self._parse_replace(line)
        if kw == "APPEND":
            return self._parse_append(line)
        if kw == "DELETE":
            return self._parse_delete(line)
        if kw == "RECALL":
            return self._parse_recall(line)
        if kw == "PACK":
            self._advance()
            self._skip_to_eol()
            return PackStmt(line=line)
        if kw == "ZAP":
            self._advance()
            self._skip_to_eol()
            return ZapStmt(line=line)
        if kw == "LOCATE":
            return self._parse_locate(line)
        if kw == "CONTINUE":
            self._advance()
            self._skip_to_eol()
            return ContinueStmt(line=line)
        if kw == "SEEK":
            return self._parse_seek(line)
        if kw == "SET":
            return self._parse_set(line)
        if kw == "CREATE":
            return self._parse_create(line)
        if kw == "COPY":
            return self._parse_copy(line)
        if kw == "INDEX":
            return self._parse_index(line)
        if kw == "LIST":
            return self._parse_list(line)
        if kw == "DISPLAY":
            return self._parse_display(line)
        if kw == "COUNT":
            return self._parse_count(line)
        if kw == "SUM":
            return self._parse_sum(line)
        if kw == "AVERAGE":
            return self._parse_average(line)
        if kw == "DIM":
            return self._parse_dim(line)
        if kw == "PRINT":
            return self._parse_print(line)
        if kw == "IF":
            return self._parse_if(line)
        if kw == "DO":
            return self._parse_do(line)
        if kw == "FOR":
            return self._parse_for_or_foreach(line)
        if kw == "SCAN":
            return self._parse_scan(line)
        if kw == "RETURN":
            return self._parse_return(line)
        if kw == "EXIT":
            self._advance()
            self._skip_to_eol()
            return ExitStmt(line=line)
        if kw == "LOOP":
            self._advance()
            self._skip_to_eol()
            return LoopStmt(line=line)
        if kw == "QUIT":
            self._advance()
            self._skip_to_eol()
            return QuitStmt(line=line)
        if kw == "DIR":
            return self._parse_dir(line)
        if kw == "CD":
            return self._parse_cd(line)
        if kw == "RENAME":
            return self._parse_rename(line)
        if kw == "ERASE":
            return self._parse_erase(line)
        if kw == "MD":
            return self._parse_md(line)
        if kw == "RD":
            return self._parse_rd(line)
        if kw == "FUNC":
            return self._parse_func_def(line)
        if kw == "PROC":
            return self._parse_proc_def(line)
        if kw == "DEF":
            return self._parse_def_fn(line)
        # END FUNC / END PROC are consumed by their parent parsers;
        # if we see a bare END here, skip it
        if kw == "END":
            self._advance()
            self._skip_to_eol()
            return None

        # Unknown keyword — consume the line
        self._advance()
        rest = self._consume_to_eol()
        raise ParseError(f"Unknown command: {kw} {rest}", line_number=line)

    def _parse_ident_statement(self, line: int) -> Stmt:
        """Parse a statement starting with an identifier (assignment, hash assign, or proc call)."""
        name = self._advance().value
        if self._match_type(TokenType.EQ):
            expr = self._parse_expr()
            self._skip_to_eol()
            return AssignStmt(var=name, expr=expr, line=line)
        # NAME(expr) = expr  (hash assignment)  OR  NAME(args) (proc call)
        if self._peek().type == TokenType.LPAREN:
            self._advance()  # consume (
            args: list[Expr] = []
            if self._peek().type != TokenType.RPAREN:
                args.append(self._parse_expr())
                while self._match_type(TokenType.COMMA):
                    args.append(self._parse_expr())
            self._expect(TokenType.RPAREN)
            # Hash assignment: NAME(key) = expr
            if self._peek().type == TokenType.EQ:
                self._advance()  # consume =
                if len(args) != 1:
                    raise ParseError(
                        f"Hash assignment requires exactly 1 key, got {len(args)}",
                        line_number=line,
                    )
                val_expr = self._parse_expr()
                self._skip_to_eol()
                return HashAssignStmt(
                    name=name.upper(), key=args[0], expr=val_expr, line=line
                )
            # Procedure call
            self._skip_to_eol()
            return ProcCallStmt(name=name.upper(), args=args, line=line)
        raise ParseError(f"Expected '=' or '(' after '{name}'", line_number=line)

    def _skip_to_eol(self) -> None:
        """Skip to end of current statement (newline or EOF)."""
        while not self._at_end_of_statement():
            self._advance()

    # -- Individual command parsers ------------------------------------------

    def _parse_print(self, line: int) -> PrintStmt:
        self._advance()  # consume ?
        exprs: list[Expr] = []
        if not self._at_end_of_statement():
            exprs.append(self._parse_expr())
            while self._match_type(TokenType.COMMA):
                exprs.append(self._parse_expr())
        self._skip_to_eol()
        return PrintStmt(exprs=exprs, line=line)

    def _parse_use(self, line: int) -> UseStmt:
        self._advance()  # consume USE
        if self._at_end_of_statement():
            return UseStmt(line=line)  # USE with no args closes current table
        table = self._read_ident_or_string()
        alias = ""
        exclusive = False
        while not self._at_end_of_statement():
            if self._match_keyword("ALIAS"):
                alias = self._read_ident_or_string()
            elif self._match_keyword("EXCLUSIVE"):
                exclusive = True
            else:
                break
        self._skip_to_eol()
        return UseStmt(table=table, alias=alias, exclusive=exclusive, line=line)

    def _parse_select(self, line: int) -> SelectStmt:
        self._advance()  # consume SELECT
        tok = self._peek()
        if tok.type == TokenType.NUMBER:
            area: str | int = int(float(self._advance().value))
        else:
            area = self._read_ident_or_string()
        self._skip_to_eol()
        return SelectStmt(area=area, line=line)

    def _parse_go(self, line: int) -> GoStmt:
        self._advance()  # consume GO/GOTO
        if self._match_keyword("TOP"):
            self._skip_to_eol()
            return GoStmt(target="TOP", line=line)
        if self._match_keyword("BOTTOM"):
            self._skip_to_eol()
            return GoStmt(target="BOTTOM", line=line)
        expr = self._parse_expr()
        self._skip_to_eol()
        return GoStmt(target=expr, line=line)

    def _parse_skip(self, line: int) -> SkipStmt:
        self._advance()  # consume SKIP
        count = None
        if not self._at_end_of_statement():
            count = self._parse_expr()
        self._skip_to_eol()
        return SkipStmt(count=count, line=line)

    def _parse_store(self, line: int) -> StoreStmt:
        self._advance()  # consume STORE
        expr = self._parse_expr()
        self._expect(TokenType.KEYWORD, "TO")
        var = self._read_ident_or_string()
        self._skip_to_eol()
        return StoreStmt(expr=expr, var=var, line=line)

    def _parse_replace(self, line: int) -> ReplaceStmt:
        self._advance()  # consume REPLACE
        scope = ""
        condition = None
        # Check for ALL scope
        if self._match_keyword("ALL"):
            scope = "ALL"

        assignments: list[tuple[str, Expr]] = []
        field_name = self._read_ident_or_string()
        self._expect(TokenType.KEYWORD, "WITH")
        expr = self._parse_expr()
        assignments.append((field_name, expr))

        while self._match_type(TokenType.COMMA):
            field_name = self._read_ident_or_string()
            self._expect(TokenType.KEYWORD, "WITH")
            expr = self._parse_expr()
            assignments.append((field_name, expr))

        if self._match_keyword("FOR"):
            condition = self._parse_expr()

        self._skip_to_eol()
        return ReplaceStmt(
            assignments=assignments, scope=scope, condition=condition, line=line
        )

    def _parse_append(self, line: int) -> Stmt:
        self._advance()  # consume APPEND
        if self._match_keyword("BLANK"):
            self._skip_to_eol()
            return AppendBlankStmt(line=line)
        if self._match_keyword("FROM"):
            source = self._read_ident_or_string()
            self._skip_to_eol()
            return AppendFromStmt(source=source, line=line)
        self._skip_to_eol()
        return AppendBlankStmt(line=line)

    def _parse_delete(self, line: int) -> DeleteStmt:
        self._advance()  # consume DELETE
        scope = ""
        condition = None
        if self._match_keyword("ALL"):
            scope = "ALL"
        if self._match_keyword("FOR"):
            condition = self._parse_expr()
        self._skip_to_eol()
        return DeleteStmt(scope=scope, condition=condition, line=line)

    def _parse_recall(self, line: int) -> RecallStmt:
        self._advance()  # consume RECALL
        scope = ""
        condition = None
        if self._match_keyword("ALL"):
            scope = "ALL"
        if self._match_keyword("FOR"):
            condition = self._parse_expr()
        self._skip_to_eol()
        return RecallStmt(scope=scope, condition=condition, line=line)

    def _parse_locate(self, line: int) -> LocateStmt:
        self._advance()  # consume LOCATE
        self._expect(TokenType.KEYWORD, "FOR")
        condition = self._parse_expr()
        self._skip_to_eol()
        return LocateStmt(condition=condition, line=line)

    def _parse_seek(self, line: int) -> SeekStmt:
        self._advance()  # consume SEEK
        expr = self._parse_expr()
        self._skip_to_eol()
        return SeekStmt(expr=expr, line=line)

    def _parse_set(self, line: int) -> Stmt:
        self._advance()  # consume SET
        tok = self._peek()
        if tok.type != TokenType.KEYWORD:
            rest = self._consume_to_eol()
            return SetStmt(setting=rest, line=line)

        setting = tok.value.upper()
        if setting == "DELETED":
            self._advance()
            on = True
            if self._match_keyword("ON"):
                on = True
            elif self._match_keyword("OFF"):
                on = False
            elif not self._at_end_of_statement():
                val = self._read_ident_or_string()
                on = val.upper() == "ON"
            self._skip_to_eol()
            return SetDeletedStmt(on=on, line=line)

        if setting == "FILTER":
            self._advance()
            self._expect(TokenType.KEYWORD, "TO")
            if self._at_end_of_statement():
                return SetFilterStmt(condition=None, line=line)
            condition = self._parse_expr()
            self._skip_to_eol()
            return SetFilterStmt(condition=condition, line=line)

        if setting == "DEFAULT":
            self._advance()
            self._expect(TokenType.KEYWORD, "TO")
            path = self._read_ident_or_string()
            self._skip_to_eol()
            return SetDefaultStmt(path=path, line=line)

        if setting == "ORDER":
            self._advance()
            self._expect(TokenType.KEYWORD, "TO")
            if self._at_end_of_statement():
                return SetOrderStmt(tag="", line=line)
            tag = self._read_ident_or_string()
            self._skip_to_eol()
            return SetOrderStmt(tag=tag, line=line)

        # Generic SET
        self._advance()
        rest = self._consume_to_eol()
        return SetStmt(setting=setting, value=rest, line=line)

    def _parse_create(self, line: int) -> Stmt:
        self._advance()  # consume CREATE
        if self._match_keyword("TABLE"):
            return self._parse_create_table(line)
        # CREATE <table> FROM <structure>
        table = self._read_ident_or_string()
        if self._match_keyword("FROM"):
            source = self._read_ident_or_string()
            self._skip_to_eol()
            return CreateFromStmt(table=table, source=source, line=line)
        self._skip_to_eol()
        return CreateTableStmt(table=table, columns=[], line=line)

    def _parse_create_table(self, line: int) -> CreateTableStmt:
        table = self._read_ident_or_string()
        columns: list[tuple[str, str, int, int]] = []
        if self._match_type(TokenType.LPAREN):
            while True:
                col_name = self._read_ident_or_string()
                type_tok = self._read_ident_or_string()
                type_char = type_tok[0].upper()
                width = 10
                decimals = 0

                # Check for (width, decimals)
                if self._match_type(TokenType.LPAREN):
                    width = int(float(self._expect(TokenType.NUMBER).value))
                    if self._match_type(TokenType.COMMA):
                        decimals = int(float(self._expect(TokenType.NUMBER).value))
                    self._expect(TokenType.RPAREN)
                # Check for width decimals (no parens)
                elif self._peek().type == TokenType.NUMBER:
                    width = int(float(self._advance().value))
                    if self._peek().type == TokenType.NUMBER:
                        decimals = int(float(self._advance().value))

                columns.append((col_name, type_char, width, decimals))
                if not self._match_type(TokenType.COMMA):
                    break
            self._expect(TokenType.RPAREN)
        self._skip_to_eol()
        return CreateTableStmt(table=table, columns=columns, line=line)

    def _parse_copy(self, line: int) -> Stmt:
        self._advance()  # consume COPY
        if self._match_keyword("STRUCTURE"):
            extended = False
            if self._match_keyword("EXTENDED"):
                extended = True
            self._expect(TokenType.KEYWORD, "TO")
            target = self._read_ident_or_string()
            self._skip_to_eol()
            return CopyStructureStmt(target=target, extended=extended, line=line)
        if self._match_keyword("FILE"):
            source = self._read_ident_or_string()
            self._expect(TokenType.KEYWORD, "TO")
            target = self._read_ident_or_string()
            self._skip_to_eol()
            return CopyFileStmt(source=source, target=target, line=line)
        rest = self._consume_to_eol()
        raise ParseError(f"Unknown COPY variant: {rest}", line_number=line)

    def _parse_index(self, line: int) -> IndexOnStmt:
        self._advance()  # consume INDEX
        self._expect(TokenType.KEYWORD, "ON")
        expr = self._parse_expr()
        tag = ""
        if self._match_keyword("TAG"):
            tag = self._read_ident_or_string()
        self._skip_to_eol()
        return IndexOnStmt(expr=expr, tag=tag, line=line)

    def _parse_insert(self, line: int) -> InsertStmt:
        """Parse INSERT INTO table (fields) VALUES (values)"""
        self._advance()  # consume INSERT
        self._expect(TokenType.KEYWORD, "INTO")
        table = self._read_ident_or_string()

        fields: list[str] = []
        if self._match_type(TokenType.LPAREN):
            fields.append(self._read_ident_or_string())
            while self._match_type(TokenType.COMMA):
                fields.append(self._read_ident_or_string())
            self._expect(TokenType.RPAREN)

        self._expect(TokenType.KEYWORD, "VALUES")
        self._expect(TokenType.LPAREN)
        values: list[Expr] = []
        values.append(self._parse_expr())
        while self._match_type(TokenType.COMMA):
            values.append(self._parse_expr())
        self._expect(TokenType.RPAREN)

        self._skip_to_eol()
        return InsertStmt(table=table, fields=fields, values=values, line=line)

    def _parse_list(self, line: int) -> ListStmt:
        self._advance()  # consume LIST
        fields: list[str] = []
        scope = ""
        condition = None
        if self._match_keyword("ALL"):
            scope = "ALL"
        if self._match_keyword("FIELDS"):
            fields.append(self._read_ident_or_string())
            while self._match_type(TokenType.COMMA):
                fields.append(self._read_ident_or_string())
        if self._match_keyword("FOR"):
            condition = self._parse_expr()
        self._skip_to_eol()
        return ListStmt(fields=fields, scope=scope, condition=condition, line=line)

    def _parse_display(self, line: int) -> Stmt:
        self._advance()  # consume DISPLAY
        if self._match_keyword("STRUCTURE"):
            self._skip_to_eol()
            return DisplayStructureStmt(line=line)
        # Generic DISPLAY — treat like LIST for now
        self._skip_to_eol()
        return ListStmt(line=line)

    def _parse_count(self, line: int) -> CountStmt:
        self._advance()  # consume COUNT
        condition = None
        to_var = ""
        if self._match_keyword("FOR"):
            condition = self._parse_expr()
        if self._match_keyword("TO"):
            to_var = self._read_ident_or_string()
        self._skip_to_eol()
        return CountStmt(condition=condition, to_var=to_var, line=line)

    def _parse_sum(self, line: int) -> SumStmt:
        self._advance()  # consume SUM
        expr = self._parse_expr()
        to_var = ""
        condition = None
        if self._match_keyword("TO"):
            to_var = self._read_ident_or_string()
        if self._match_keyword("FOR"):
            condition = self._parse_expr()
        self._skip_to_eol()
        return SumStmt(expr=expr, to_var=to_var, condition=condition, line=line)

    def _parse_average(self, line: int) -> AverageStmt:
        self._advance()  # consume AVERAGE
        expr = self._parse_expr()
        to_var = ""
        condition = None
        if self._match_keyword("TO"):
            to_var = self._read_ident_or_string()
        if self._match_keyword("FOR"):
            condition = self._parse_expr()
        self._skip_to_eol()
        return AverageStmt(expr=expr, to_var=to_var, condition=condition, line=line)

    def _parse_if(self, line: int) -> IfStmt:
        self._advance()  # consume IF
        condition = self._parse_expr()
        self._skip_to_eol()
        self._skip_newlines()

        then_body = self._parse_block("ENDIF", "ELSE", "ELSEIF")
        elseif_clauses: list[tuple[Expr, list[Stmt]]] = []
        else_body: list[Stmt] = []

        while self._match_keyword("ELSEIF"):
            ei_cond = self._parse_expr()
            self._skip_to_eol()
            self._skip_newlines()
            ei_body = self._parse_block("ENDIF", "ELSE", "ELSEIF")
            elseif_clauses.append((ei_cond, ei_body))

        if self._match_keyword("ELSE"):
            self._skip_to_eol()
            self._skip_newlines()
            else_body = self._parse_block("ENDIF")

        self._expect(TokenType.KEYWORD, "ENDIF")
        self._skip_to_eol()
        return IfStmt(
            condition=condition,
            then_body=then_body,
            elseif_clauses=elseif_clauses,
            else_body=else_body,
            line=line,
        )

    def _parse_do(self, line: int) -> Stmt:
        self._advance()  # consume DO
        tok = self._peek()

        if tok.type == TokenType.KEYWORD and tok.value == "CASE":
            return self._parse_do_case(line)
        if tok.type == TokenType.KEYWORD and tok.value == "WHILE":
            return self._parse_do_while(line)

        # DO <program> [WITH args]
        program = self._read_ident_or_string()
        args: list[Expr] = []
        if self._match_keyword("WITH"):
            args.append(self._parse_expr())
            while self._match_type(TokenType.COMMA):
                args.append(self._parse_expr())
        self._skip_to_eol()
        return DoProgramStmt(program=program, args=args, line=line)

    def _parse_do_case(self, line: int) -> DoCaseStmt:
        self._advance()  # consume CASE
        self._skip_to_eol()
        self._skip_newlines()

        cases: list[tuple[Expr, list[Stmt]]] = []
        otherwise: list[Stmt] = []

        while self._match_keyword("CASE"):
            case_cond = self._parse_expr()
            self._skip_to_eol()
            self._skip_newlines()
            case_body = self._parse_block("CASE", "OTHERWISE", "ENDCASE")
            cases.append((case_cond, case_body))

        if self._match_keyword("OTHERWISE"):
            self._skip_to_eol()
            self._skip_newlines()
            otherwise = self._parse_block("ENDCASE")

        self._expect(TokenType.KEYWORD, "ENDCASE")
        self._skip_to_eol()
        return DoCaseStmt(cases=cases, otherwise=otherwise, line=line)

    def _parse_do_while(self, line: int) -> DoWhileStmt:
        self._advance()  # consume WHILE
        condition = self._parse_expr()
        self._skip_to_eol()
        self._skip_newlines()
        body = self._parse_block("ENDDO")
        self._expect(TokenType.KEYWORD, "ENDDO")
        self._skip_to_eol()
        return DoWhileStmt(condition=condition, body=body, line=line)

    def _parse_dim(self, line: int) -> DimHashStmt:
        """Parse DIM FOO{}"""
        self._advance()  # consume DIM
        name = self._read_ident_or_string().upper()
        self._expect(TokenType.LBRACE)
        self._expect(TokenType.RBRACE)
        self._skip_to_eol()
        return DimHashStmt(name=name, line=line)

    def _parse_for_or_foreach(self, line: int) -> ForStmt | ForEachStmt:
        """Parse FOR ... or FOR EACH ..."""
        self._advance()  # consume FOR
        # Check for FOR EACH
        if self._match_keyword("EACH"):
            return self._parse_for_each(line)
        return self._parse_for_body(line)

    def _parse_for_each(self, line: int) -> ForEachStmt:
        """Parse FOR EACH var IN hashname ... NEXT"""
        var = self._read_ident_or_string()
        self._expect(TokenType.KEYWORD, "IN")
        hashmap = self._read_ident_or_string().upper()
        self._skip_to_eol()
        self._skip_newlines()
        body = self._parse_block("ENDFOR", "NEXT")
        if self._match_keyword("ENDFOR") or self._match_keyword("NEXT"):
            pass
        self._skip_to_eol()
        return ForEachStmt(var=var, hashmap=hashmap, body=body, line=line)

    def _parse_for_body(self, line: int) -> ForStmt:
        # FOR already consumed by _parse_for_or_foreach
        var = self._read_ident_or_string()
        self._expect(TokenType.EQ)
        start = self._parse_expr()
        self._expect(TokenType.KEYWORD, "TO")
        end = self._parse_expr()
        step = None
        if self._match_keyword("STEP"):
            step = self._parse_expr()
        self._skip_to_eol()
        self._skip_newlines()
        body = self._parse_block("ENDFOR", "NEXT")
        # Accept either ENDFOR or NEXT
        if self._match_keyword("ENDFOR") or self._match_keyword("NEXT"):
            pass
        self._skip_to_eol()
        return ForStmt(var=var, start=start, end=end, step=step, body=body, line=line)

    def _parse_scan(self, line: int) -> ScanStmt:
        self._advance()  # consume SCAN
        condition = None
        if self._match_keyword("FOR"):
            condition = self._parse_expr()
        self._skip_to_eol()
        self._skip_newlines()
        body = self._parse_block("ENDSCAN")
        self._expect(TokenType.KEYWORD, "ENDSCAN")
        self._skip_to_eol()
        return ScanStmt(condition=condition, body=body, line=line)

    def _parse_return(self, line: int) -> ReturnStmt:
        self._advance()  # consume RETURN
        expr = None
        if not self._at_end_of_statement():
            expr = self._parse_expr()
        self._skip_to_eol()
        return ReturnStmt(expr=expr, line=line)

    def _parse_dir(self, line: int) -> DirStmt:
        self._advance()  # consume DIR
        pattern = ""
        if not self._at_end_of_statement():
            pattern = self._consume_to_eol()
        return DirStmt(pattern=pattern, line=line)

    def _parse_cd(self, line: int) -> CdStmt:
        self._advance()  # consume CD
        path = self._consume_to_eol()
        return CdStmt(path=path, line=line)

    def _parse_rename(self, line: int) -> RenameStmt:
        self._advance()  # consume RENAME
        old = self._read_ident_or_string()
        self._expect(TokenType.KEYWORD, "TO")
        new = self._read_ident_or_string()
        self._skip_to_eol()
        return RenameStmt(old=old, new=new, line=line)

    def _parse_erase(self, line: int) -> EraseStmt:
        self._advance()  # consume ERASE
        filename = self._read_ident_or_string()
        self._skip_to_eol()
        return EraseStmt(filename=filename, line=line)

    def _parse_md(self, line: int) -> MdStmt:
        self._advance()  # consume MD
        dirname = self._read_ident_or_string()
        self._skip_to_eol()
        return MdStmt(dirname=dirname, line=line)

    def _parse_rd(self, line: int) -> RdStmt:
        self._advance()  # consume RD
        dirname = self._read_ident_or_string()
        self._skip_to_eol()
        return RdStmt(dirname=dirname, line=line)

    def _parse_param_list(self) -> list[str]:
        """Parse (A, B, C) parameter list, return list of names."""
        params: list[str] = []
        self._expect(TokenType.LPAREN)
        if self._peek().type != TokenType.RPAREN:
            params.append(self._read_ident_or_string())
            while self._match_type(TokenType.COMMA):
                params.append(self._read_ident_or_string())
        self._expect(TokenType.RPAREN)
        return params

    def _parse_func_def(self, line: int) -> FuncDefStmt:
        """Parse FUNC name(params) ... END FUNC"""
        self._advance()  # consume FUNC
        name = self._read_ident_or_string().upper()
        params = self._parse_param_list()
        self._skip_to_eol()
        self._skip_newlines()
        body = self._parse_block("END")
        # Expect END FUNC
        self._expect(TokenType.KEYWORD, "END")
        self._expect(TokenType.KEYWORD, "FUNC")
        self._skip_to_eol()
        return FuncDefStmt(name=name, params=params, body=body, line=line)

    def _parse_proc_def(self, line: int) -> ProcDefStmt:
        """Parse PROC name(params) ... END PROC"""
        self._advance()  # consume PROC
        name = self._read_ident_or_string().upper()
        params = self._parse_param_list()
        self._skip_to_eol()
        self._skip_newlines()
        body = self._parse_block("END")
        # Expect END PROC
        self._expect(TokenType.KEYWORD, "END")
        self._expect(TokenType.KEYWORD, "PROC")
        self._skip_to_eol()
        return ProcDefStmt(name=name, params=params, body=body, line=line)

    def _parse_def_fn(self, line: int) -> DefFnStmt:
        """Parse DEF FN name(params) = expr"""
        self._advance()  # consume DEF
        self._expect(TokenType.KEYWORD, "FN")
        name = self._read_ident_or_string().upper()
        params = self._parse_param_list()
        self._expect(TokenType.EQ)
        expr = self._parse_expr()
        self._skip_to_eol()
        return DefFnStmt(name=name, params=params, expr=expr, line=line)

    def _parse_block(self, *terminators: str) -> list[Stmt]:
        """Parse statements until we see one of the terminator keywords."""
        body: list[Stmt] = []
        while True:
            self._skip_newlines()
            tok = self._peek()
            if tok.type == TokenType.EOF:
                break
            if tok.type == TokenType.KEYWORD and tok.value in terminators:
                break
            stmt = self._parse_statement()
            if stmt is not None:
                body.append(stmt)
        return body


def parse(source: str) -> list[Stmt]:
    """Parse a dBASE source string into a list of AST statements."""
    tokens = tokenize(source)
    parser = Parser(tokens)
    return parser.parse_program()


def parse_command(command: str) -> Stmt:
    """Parse a single dBASE command string."""
    stmts = parse(command)
    if not stmts:
        raise ParseError("Empty command")
    return stmts[0]
