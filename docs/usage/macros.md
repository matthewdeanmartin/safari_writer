# Macros (Safari Basic)

Safari Writer and Safari Fed can run BASIC macros — small `.BAS` programs that generate text and insert it into your document or create a draft post.

## Quick start

1. Place a `.BAS` file in `~/.safari/macros/`.
2. In the **editor**, press **Ctrl+Backslash** to open the macro picker.
3. In **Safari Fed**, press **~** to open the macro picker against the current post.
4. Use **Up/Down** to select a macro and press **Enter**.

The macro's `PRINT` output is inserted at the cursor (editor) or saved as a new draft (Fed).

---

## Writing a macro

Macros are plain-text files with line-numbered Atari BASIC. The first `REM` line is shown as a description in the picker.

```basic
10 REM A simple greeting
20 PRINT "Hello from Safari Basic!"
30 PRINT "Document has "; STR$(DOCLINES); " lines."
```

Save this as `~/.safari/macros/greeting.bas` and run it from the editor with **Ctrl+Backslash**. The two lines will be inserted at the cursor.

---

## Pre-injected variables

The runner injects the following read-only variables before your macro runs. No `DIM` statement is needed for these.

### Document state (editor context)

| Variable | Type | Value |
|---|---|---|
| `DOCLINES` | numeric | Total lines in the document |
| `CURSORROW` | numeric | Cursor row at invocation (1-based) |
| `CURSORCOL` | numeric | Cursor column (1-based) |
| `SELCOUNT` | numeric | Number of selected lines |
| `CLIPBOARD$` | string | Current clipboard text |
| `DOC1$` … `DOC200$` | string | Individual document lines |
| `SEL1$` … `SELN$` | string | Selected lines |

### Fed post context (`~` in Safari Fed)

| Variable | Type | Value |
|---|---|---|
| `PAUTHOR$` | string | Post author display name |
| `PHANDLE$` | string | Post @handle |
| `PDATE$` | string | Post timestamp |
| `PTAGS$` | string | Space-joined hashtags |
| `PLINES` | numeric | Number of content lines |
| `PBOOSTS` | numeric | Boost count |
| `PFAVES` | numeric | Favourite count |
| `PLINE1$` … `PLINE9$` | string | Individual post content lines |

Post variables are available in editor macros too if the editor was opened via a Fed handoff, but they will be empty strings/zeros otherwise.

---

## Example macros

### Insert a post header (`post_header.bas`)

```basic
10 REM Insert a formatted header from the current Fed post
20 PRINT "## "; PAUTHOR$; " ("; PHANDLE$; ")"
30 PRINT "Posted: "; PDATE$
40 PRINT "Tags:   "; PTAGS$
50 PRINT ""
60 PRINT PLINE1$
70 PRINT PLINE2$
80 PRINT PLINE3$
```

Press **~** in Safari Fed on any post, select this macro, and the output is saved as a draft in the Drafts folder.

### Export a post as a blockquote (`thread_export.bas`)

```basic
10 REM Export current Fed post as a quoted block for a blog draft
20 PRINT "> "; PHANDLE$; " wrote:"
30 PRINT ">"
40 PRINT "> "; PLINE1$
50 PRINT "> "; PLINE2$
60 PRINT "> "; PLINE3$
70 PRINT ""
80 PRINT "— "; PAUTHOR$; ", "; PDATE$
```

### Show document stats (`doc_stats.bas`)

```basic
10 REM Print document line count and cursor position
20 PRINT "Document lines: "; STR$(DOCLINES)
30 PRINT "Cursor row:     "; STR$(CURSORROW)
40 PRINT "Cursor col:     "; STR$(CURSORCOL)
50 PRINT "Selection lines:"; STR$(SELCOUNT)
```

### Insert a DATA-driven separator (`datestamp.bas`)

```basic
10 REM Insert a datestamp separator at the cursor position
20 PRINT "---"
30 PRINT "Date: "; PDATE$
40 PRINT "---"
```

### Conditional output with IF/THEN

```basic
10 REM Add a boost notice only if the post has boosts
20 IF PBOOSTS > 0 THEN PRINT "Boosted "; STR$(PBOOSTS); " times"
30 IF PBOOSTS = 0 THEN PRINT "(no boosts yet)"
```

### Loop over selected lines

```basic
10 REM Quote each selected line with a > prefix
20 LET I = 1
30 IF I > SELCOUNT THEN END
40 PRINT "> "; SEL1$
50 LET I = I + 1
60 GOTO 30
```

> **Note:** `SEL1$` is always the first selected line. For a proper loop over all selections use `SEL1$`, `SEL2$`, etc. as separate variables — the interpreter does not support dynamic variable names.

---

## BASIC language reference

Safari Basic implements a subset of Atari BASIC. The following are supported in macros:

| Statement | Example |
|---|---|
| `PRINT` | `PRINT "hello"; VAR$` |
| `LET` (or bare assignment) | `LET X = 5` / `X = 5` |
| `IF … THEN` | `IF X > 0 THEN PRINT "yes"` |
| `GOTO` | `GOTO 100` |
| `GOSUB` / `RETURN` | `GOSUB 500` |
| `FOR` / `NEXT` | `FOR I = 1 TO 10 : NEXT I` |
| `DIM` | `DIM A$(40)` (required for user string vars) |
| `INPUT` | `INPUT NAME$` |
| `DATA` / `READ` | `DATA "a","b" : READ X$` |
| `REM` | `REM comment` |
| `END` / `STOP` | `END` |

String functions: `LEN`, `LEFT$`, `RIGHT$`, `MID$`, `STR$`, `VAL`, `CHR$`, `ASC`.
Math functions: `SIN`, `COS`, `TAN`, `ABS`, `INT`, `SQR`, `SGN`, `EXP`, `LOG`, `RND`.

> **Important:** User-defined string variables (variables you declare yourself, not the pre-injected ones) must be dimensioned with `DIM` before assignment:
> ```basic
> 10 DIM RESULT$(200)
> 20 RESULT$ = "Hello"
> 30 PRINT RESULT$
> ```

---

## Macro picker keys

| Key | Action |
|---|---|
| Up / Down | Move selection |
| Enter | Run selected macro |
| Escape | Cancel |

---

## Macro directory

The default macro directory is `~/.safari/macros/`. You can change it by setting `macros_dir` in `~/.safari/settings.json`:

```json
{
  "macros_dir": "/home/you/my-macros"
}
```

The directory is created automatically if it does not exist.

---

## Error handling

If a macro encounters a syntax or runtime error, the insertion is cancelled and a message is shown in the status bar:

```
MACRO ERROR: Use of undimensioned string
```

No partial output is inserted on error.
