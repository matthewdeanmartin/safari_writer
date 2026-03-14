# Spec 15: Safari Basic — Document Macros

## Overview

Safari Basic is a line-numbered BASIC interpreter embedded in Safari Writer.
Users write `.BAS` files that run against the current document context,
`PRINT` text into the document buffer at the cursor position (in the editor),
or produce a draft post in Safari Fed.

The interpreter is intentionally minimal: a Atari BASIC subset plus custom
`WRITER.*`, `DOCUMENT.*`, `SELECTION.*`, and `POST.*` extensions.

______________________________________________________________________

## 1. Macro File Format

- Plain text `.BAS` files stored in `~/.safari/macros/` (configurable via settings).
- Line-numbered: `10 PRINT "hello"`. Lines execute in ascending numeric order.
- Blank lines and lines beginning with `REM` are ignored.
- Example:

```basic
10 DATA "Alice", "@alice@example.social", "2026-03-08"
20 READ AUTHOR$, HANDLE$, DATE$
30 PRINT "## Post by "; AUTHOR$
40 PRINT "Handle: "; HANDLE$
50 PRINT "Date:   "; DATE$
60 PRINT ""
70 PRINT DOCUMENT.LINE(CURSOR.ROW - 1)
```

______________________________________________________________________

## 2. Module Layout

```
safari_basic/
  __init__.py
  interpreter.py   # tokenizer + line executor
  builtins.py      # PRINT, DATA, READ, DIM, FOR/NEXT, IF/THEN, GOTO, GOSUB
  commands.py      # custom Safari extensions: WRITER.*, DOCUMENT.*, etc.
  context.py       # MacroContext — bridges interpreter to app state
  runner.py        # load file, inject context, run, return output

safari_writer/screens/
  macro_picker.py  # ModalScreen listing .BAS files, returns chosen path

macros/            # example macros shipped with the project
  post_header.bas
  thread_export.bas
  word_count.bas
  format_quotes.bas
```

______________________________________________________________________

## 3. MacroContext

```python
@dataclass
class MacroContext:
    document_lines: list[str]           # full buffer as plain-text lines
    cursor_row: int                     # 0-based cursor row at invocation
    cursor_col: int                     # 0-based cursor column
    selection_start: tuple | None       # (row, col) or None
    selection_end: tuple | None
    current_post: Any | None            # FedPost if invoked from Fed, else None
    output_lines: list[str]             # PRINT appends here
    writer_commands: list[WriterCommand]  # queued document mutations
```

`WriterCommand` is a tagged union (dataclass variants):

- `InsertAtCursor(text: str)`
- `GotoPosition(row: int, col: int)`
- `DeleteLine(row: int)`
- `ReplaceAll(old: str, new: str)`
- `InsertFormatMarker(marker: str)`

______________________________________________________________________

## 4. Custom BASIC Variables and Commands

### Read-only document variables

Variable names are plain uppercase identifiers (no dots) so the Atari BASIC
scanner can parse them as standard tokens.

| Variable | Value |
|---|---|
| `DOCLINES` | Total number of lines in the document |
| `CURSORROW` | Cursor row at macro invocation (1-based) |
| `CURSORCOL` | Cursor column (1-based) |
| `SELCOUNT` | Number of selected lines |
| `CLIPBOARD$` | Clipboard text |
| `DOC1$` … `DOC200$` | Individual document lines (pre-injected by runner) |
| `SEL1$` … `SELN$` | Selected lines (pre-injected by runner) |

### Post/Fed context (populated when invoked from Fed via `~`)

| Variable | Value |
|---|---|
| `PAUTHOR$` | `post.author` |
| `PHANDLE$` | `post.handle` |
| `PDATE$` | `post.posted_at` |
| `PTAGS$` | Space-joined tags string |
| `PLINES` | Number of content lines (numeric) |
| `PBOOSTS` | Boost count (numeric) |
| `PFAVES` | Favourite count (numeric) |
| `PLINE1$` … `PLINE9$` | Individual post content lines |

______________________________________________________________________

## 5. BASIC Subset — Phase 1 (MVP)

- `PRINT expr [; expr ...]` — append to output_lines
- `DATA val, val, ...` / `READ var$` — static data lists in program
- `LET var$ = expr` and bare `var$ = expr`
- `LET n = expr` and bare `n = expr` (numeric variables)
- `IF expr THEN statement`
- `GOTO N`
- `REM comment`
- String concatenation: `A$ + B$` and `A$; B$` inside PRINT
- Numeric arithmetic: `+`, `-`, `*`, `/`
- Comparison operators: `=`, `<>`, `<`, `>`, `<=`, `>=`
- String literals: `"..."`, numeric literals

### Phase 2

- `FOR I = A TO B [STEP C]` / `NEXT I`
- `GOSUB N` / `RETURN`
- `DIM A$(N)` / array indexing `A$(I)`
- `INPUT var$` — prompt in editor status line
- String functions: `LEFT$(s,n)`, `RIGHT$(s,n)`, `MID$(s,i,n)`, `LEN(s)`, `STR$(n)`, `VAL(s)`

### Phase 3

- `WRITER.*` mutation commands applied to live document
- `SELECTION.*` array population
- `POST.*` variables from Fed context
- File I/O: `OPEN #1, "file.txt"` / `PRINT #1, expr` / `CLOSE #1` (sandboxed to macros dir)

______________________________________________________________________

## 6. Execution Flow

### From EditorScreen (Ctrl+)

```
Ctrl+\ pressed in EditorScreen
  → push MacroPickerScreen (modal, lists *.BAS from macros dir)
  → user selects foo.BAS → picker dismissed with path
  → MacroRunner.build_context(app_state, current_post=None)
  → MacroRunner.run(path, context)
       interpreter executes lines in order
       PRINT → context.output_lines.append(...)
       WRITER.* → context.writer_commands.append(...)
  → output = "\n".join(context.output_lines)
  → EditorScreen.insert_at_cursor(output)
  → apply context.writer_commands in order
```

### From SafariFedMainScreen (~)

```
~ pressed in SafariFedMainScreen
  → push MacroPickerScreen
  → user selects foo.BAS
  → MacroRunner.build_context(app_state, current_post=state.current_post())
       POST.* variables populated from FedPost fields
  → MacroRunner.run(path, context)
  → output = "\n".join(context.output_lines)
  → state.create_local_post(text=output, draft=True)
  → state.set_folder("Drafts")
  → status: "Macro output saved as draft"
```

______________________________________________________________________

## 7. MacroPickerScreen

- Modal screen pushed over the current screen.
- Lists all `*.BAS` files from the macros directory.
- Arrow keys navigate; Enter selects; Escape cancels.
- Displays filename and first `REM` line as description.
- Returns `Path` to chosen file or `None` on cancel.

______________________________________________________________________

## 8. Error Handling

- Syntax errors: display in editor status line as `MACRO ERROR line N: message`.
- Runtime errors (division by zero, bad array index): same status line format, macro aborts.
- No output is inserted if the macro errors out.
- Missing macros directory: status line warns, picker shows empty list with hint.

______________________________________________________________________

## 9. Settings

New keys in `~/.safari/settings.json`:

```json
{
  "macros_dir": "~/.safari/macros"
}
```

______________________________________________________________________

## 10. Example Macros

### `post_header.bas`

```basic
10 REM Insert a formatted header from the current Fed post
20 PRINT "## "; PAUTHOR$; " ("; PHANDLE$; ")"
30 PRINT "Posted: "; PDATE$
40 PRINT "Tags:   "; PTAGS$
50 PRINT ""
60 PRINT PLINE1$
70 PRINT PLINE2$
80 PRINT PLINE3$
90 PRINT PLINE4$
100 PRINT PLINE5$
```

### `thread_export.bas`

```basic
10 REM Export current Fed post as a plain-text quote block
20 PRINT "> "; PHANDLE$; " wrote:"
30 PRINT ">"
40 PRINT "> "; PLINE1$
50 PRINT "> "; PLINE2$
60 PRINT "> "; PLINE3$
70 PRINT ""
80 PRINT "— "; PAUTHOR$; ", "; PDATE$
```

### `doc_stats.bas`

```basic
10 REM Print document line count and cursor position
20 PRINT "Document lines: "; STR$(DOCLINES)
30 PRINT "Cursor row:     "; STR$(CURSORROW)
40 PRINT "Cursor col:     "; STR$(CURSORCOL)
50 PRINT "Selection lines:"; STR$(SELCOUNT)
```
