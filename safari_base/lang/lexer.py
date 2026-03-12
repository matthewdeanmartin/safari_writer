"""Tokenizer for the dBASE language processor."""

from __future__ import annotations

import re

from safari_base.lang.errors import ParseError
from safari_base.lang.types import Token, TokenType

# Keywords that must be recognized as such (case-insensitive)
KEYWORDS = frozenset({
    "ALL", "ALIAS", "AND", "APPEND", "AVERAGE", "BLANK", "BOTTOM", "CASE",
    "CD", "CLOSE", "CONTINUE", "COPY", "COUNT", "CREATE", "DEF", "DELETE",
    "DIM", "DIR", "DISPLAY", "DO", "EACH", "ELSE", "ELSEIF", "END",
    "ENDCASE", "ENDDO", "ENDFOR", "ENDIF", "ENDSCAN", "ERASE", "EXCLUSIVE",
    "EXIT", "EXTENDED", "FILE", "FIELDS", "FILTER", "FN", "FOR", "FROM",
    "FUNC", "GO", "GOTO", "IF", "IN", "INDEX", "LIST", "LOCATE", "LOOP",
    "MD", "MODIFY", "NEXT", "NOT", "NOTE", "ON", "OR", "ORDER",
    "OTHERWISE", "PACK", "PRINT", "PROC", "QUIT", "RD", "RECALL", "RENAME",
    "REPLACE", "REST", "RETURN", "SCAN", "SEEK", "SELECT", "SET", "SKIP",
    "STEP", "STORE", "STRUCTURE", "SUM", "TABLE", "TAG", "TO", "TOP",
    "USE", "WHILE", "WITH", "ZAP", "DEFAULT", "DELETED", "RECORD",
    "AVERAGE",
})


def tokenize(source: str, start_line: int = 1) -> list[Token]:
    """Tokenize a dBASE source string into a list of tokens."""
    tokens: list[Token] = []
    lines = source.split("\n")
    line_num = start_line
    continuation = False

    for raw_line in lines:
        # Strip trailing whitespace
        line = raw_line.rstrip()

        # Handle line continuation from previous line
        if continuation:
            continuation = False
            # Don't emit a newline — we're continuing
        else:
            if tokens and tokens[-1].type != TokenType.NEWLINE:
                tokens.append(Token(TokenType.NEWLINE, "\n", line_num - 1))

        # Skip blank lines
        if not line.strip():
            line_num += 1
            continue

        stripped = line.lstrip()

        # Full-line comment: * in column 1 or NOTE
        if stripped.startswith("*"):
            line_num += 1
            continue
        if stripped.upper().startswith("NOTE ") or stripped.upper() == "NOTE":
            line_num += 1
            continue

        pos = 0
        while pos < len(line):
            # Skip whitespace
            if line[pos] in " \t":
                pos += 1
                continue

            # Inline comment &&
            if line[pos:pos + 2] == "&&":
                break  # rest of line is comment

            # Line continuation ;
            if line[pos] == ";":
                continuation = True
                pos += 1
                continue

            # String literals
            if line[pos] in ('"', "'"):
                quote = line[pos]
                end = line.find(quote, pos + 1)
                if end == -1:
                    end = len(line)
                tokens.append(Token(TokenType.STRING, line[pos + 1:end], line_num))
                pos = end + 1
                continue

            # Numbers
            m = re.match(r"\d+(\.\d+)?", line[pos:])
            if m:
                tokens.append(Token(TokenType.NUMBER, m.group(), line_num))
                pos += m.end()
                continue

            # Logical literals .T. .F. and logical operators .AND. .OR. .NOT.
            if line[pos] == ".":
                upper_rest = line[pos:].upper()
                if upper_rest.startswith(".T."):
                    tokens.append(Token(TokenType.LOGICAL, ".T.", line_num))
                    pos += 3
                    continue
                if upper_rest.startswith(".F."):
                    tokens.append(Token(TokenType.LOGICAL, ".F.", line_num))
                    pos += 3
                    continue
                if upper_rest.startswith(".AND."):
                    tokens.append(Token(TokenType.DOT_AND, ".AND.", line_num))
                    pos += 5
                    continue
                if upper_rest.startswith(".OR."):
                    tokens.append(Token(TokenType.DOT_OR, ".OR.", line_num))
                    pos += 4
                    continue
                if upper_rest.startswith(".NOT."):
                    tokens.append(Token(TokenType.DOT_NOT, ".NOT.", line_num))
                    pos += 5
                    continue
                # Lone dot — might be part of a decimal, treat as error context
                raise ParseError(f"Unexpected '.' at position {pos}", line_number=line_num)

            # Arrow ->
            if line[pos:pos + 2] == "->":
                tokens.append(Token(TokenType.ARROW, "->", line_num))
                pos += 2
                continue

            # Two-char operators
            two = line[pos:pos + 2]
            if two == "==":
                tokens.append(Token(TokenType.EQEQ, "==", line_num))
                pos += 2
                continue
            if two == "<>":
                tokens.append(Token(TokenType.NEQ, "<>", line_num))
                pos += 2
                continue
            if two == "!=":
                tokens.append(Token(TokenType.BANGEQ, "!=", line_num))
                pos += 2
                continue
            if two == "<=":
                tokens.append(Token(TokenType.LE, "<=", line_num))
                pos += 2
                continue
            if two == ">=":
                tokens.append(Token(TokenType.GE, ">=", line_num))
                pos += 2
                continue

            # Single-char operators
            one_char_map = {
                "+": TokenType.PLUS,
                "-": TokenType.MINUS,
                "*": TokenType.STAR,
                "/": TokenType.SLASH,
                "^": TokenType.CARET,
                "=": TokenType.EQ,
                "<": TokenType.LT,
                ">": TokenType.GT,
                "(": TokenType.LPAREN,
                ")": TokenType.RPAREN,
                "{": TokenType.LBRACE,
                "}": TokenType.RBRACE,
                ",": TokenType.COMMA,
            }
            if line[pos] in one_char_map:
                tokens.append(Token(one_char_map[line[pos]], line[pos], line_num))
                pos += 1
                continue

            # ? print command — special case: at start of statement or after newline
            if line[pos] == "?":
                tokens.append(Token(TokenType.KEYWORD, "?", line_num))
                pos += 1
                continue

            # Identifiers and keywords
            m = re.match(r"[A-Za-z_][A-Za-z0-9_]*", line[pos:])
            if m:
                word = m.group()
                upper_word = word.upper()
                if upper_word in KEYWORDS:
                    tokens.append(Token(TokenType.KEYWORD, upper_word, line_num))
                else:
                    tokens.append(Token(TokenType.IDENT, word, line_num))
                pos += m.end()
                continue

            raise ParseError(
                f"Unexpected character '{line[pos]}' at position {pos}",
                line_number=line_num,
            )

        line_num += 1

    # Final newline and EOF
    if tokens and tokens[-1].type != TokenType.NEWLINE:
        tokens.append(Token(TokenType.NEWLINE, "\n", line_num))
    tokens.append(Token(TokenType.EOF, "", line_num))
    return tokens
