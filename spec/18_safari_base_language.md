I looked up both pieces: the Python `dbf` library and the dBASE/xBase command language. The most useful finding is that Python’s `dbf` package is a **table/file library**, not a dBASE language runtime. It explicitly supports **dBase III** tables, along with Clipper, FoxPro, and Visual FoxPro formats; it handles unicode text, code pages, memos, and null fields, but it does **not** support on-disk index files and some later field types. So it is a reasonable storage backend for a dBASE III+ interpreter, but you still need to build the parser, runtime, work-area model, and command semantics yourself. ([PyPI][1])

Below is a compact implementation spec for a **headless dBASE III+ execution engine** aimed at “DML + DDL + easy OS-ish commands,” using Python and `dbf` as the DBF layer.

______________________________________________________________________

# Spec: Headless dBASE III+ Executor

## 1. Purpose

Implement a headless interpreter for a practical subset of **dBASE III+ style xBase code** that can:

- create and modify `.dbf` tables,
- open tables into dBASE-style work areas,
- read, navigate, search, and update records,
- execute `.prg` scripts and single commands,
- support structured control flow,
- support a small, easy-to-implement OS/file subset.

This runtime is **not** a full interactive clone of the original product. It is a scriptable batch/CLI execution engine for modern machines.

dBASE historically combined a command prompt, procedural language, and navigational database commands such as `USE`, `SKIP`, `GO`, `REPLACE`, and `STORE`, and scripts were commonly run via `DO`. The common portability center of gravity for xBase dialects is close to dBASE III+ style command syntax. ([Wikipedia][2])

______________________________________________________________________

## 2. Backend choice

### 2.1 Storage layer

Use Python package `dbf` as the primary DBF backend.

### 2.2 Why

`dbf` already supports dBase III-family tables and memo/null/codepage handling, which removes most of the low-level DBF file work. ([PyPI][1])

### 2.3 Important limitation

The engine must **not** rely on the backend for persistent index support, because `dbf` does not support index files. If indexed behavior is needed, implement it in the interpreter as:

- temporary in-memory orderings,
- optional generated sidecar index files later,
- or leave commands like `INDEX ON` as partially supported / deferred. ([PyPI][1])

______________________________________________________________________

## 3. Non-goals

Do **not** implement in v1:

- screen/form/report designers,
- `@ ... SAY/GET`,
- macros that execute arbitrary Python,
- graphics, hardware, printer, or DOS-shell integration,
- network/multiuser locking beyond a simple single-process model,
- full SQL layer,
- full compatibility with every clone,
- obscure commands whose main purpose was UI or hardware control.

dBASE Plus documents a much larger modern language and also includes a later “Local SQL” layer, but this spec is intentionally targeting the older xBase command model instead of the full later product. ([dBase.com][3])

______________________________________________________________________

## 4. Execution model

## 4.1 Modes

Support three modes:

1. **Command mode**
   Execute one command string.

1. **Program mode**
   Execute a `.prg` file with line-oriented commands.

1. **Embedded mode**
   Python API for host applications:

   - `execute(command: str) -> Result`
   - `run_program(path: Path, args: list[str]) -> Result`

### 4.2 State

Interpreter state must include:

- current working directory,
- current default DBF directory,
- memory variables,
- active work area number,
- map of open work areas,
- current relation/order/filter state per work area,
- procedure call stack,
- error state and `ON ERROR` hook later.

### 4.3 Work areas

Model dBASE work areas explicitly:

- multiple open tables,
- one active area at a time,
- `SELECT n` changes active area,
- `USE` opens a table in current area unless otherwise specified.

The xBase family is built around the notion of an active table/work area plus record-pointer navigation commands such as `GO`, `SKIP`, `LOCATE`, and `SEEK`. ([Wikipedia][2])

______________________________________________________________________

## 5. Language surface

## 5.1 Source format

- ASCII/UTF-8 text source.

- Case-insensitive keywords.

- End of line terminates a command unless continued with `;`.

- Comments:

  - `*` in column 1,
  - `&&` inline comment,
  - `NOTE` line comment optional.

## 5.2 Identifiers

- Unquoted identifiers are case-insensitive.
- Table aliases and memvar names are normalized internally.
- Field names should follow dBASE-ish naming restrictions, but modern implementation may allow a somewhat relaxed parser and validate on table creation.

## 5.3 Literals

Support:

- strings: `"hello"` and `'hello'`
- numerics: integers and decimals
- logical: `.T.`, `.F.`
- date literals: `CTOD("YYYY-MM-DD")` at minimum, optionally `{^YYYY-MM-DD}` as an extension
- null: optional extension only if backend supports it

## 5.4 Expressions

Support:

- arithmetic: `+ - * / ^`
- comparison: `= == <> != < <= > >=`
- logical: `.AND. .OR. .NOT.`
- string concatenation: `+`
- parentheses
- field references
- memvar references
- function calls

______________________________________________________________________

## 6. Program structure

Support:

- straight-line command scripts,
- `DO <program>`
- `RETURN`
- `IF / ELSE / ELSEIF / ENDIF`
- `DO CASE / CASE / OTHERWISE / ENDCASE`
- `DO WHILE / ENDDO`
- `FOR / TO / STEP / ENDFOR`
- `SCAN / ENDSCAN`
- `EXIT`, `LOOP`

Later dBASE documentation still describes the core control structures in ways consistent with the classic xBase model: `IF...ENDIF`, `DO CASE...ENDCASE`, `DO WHILE...ENDDO`, and `SCAN...ENDSCAN`. `SCAN` is specifically described as a structured alternative to record-by-record looping with `SKIP`/`EOF()`. ([dBase.com][4])

______________________________________________________________________

## 7. Data model

## 7.1 Table files

Primary unit is a `.dbf` table, optionally with memo sidecar files.

## 7.2 Supported field types in v1

At minimum:

- Character
- Numeric
- Date
- Logical
- Memo

These are the practical dBASE III-era core types and align with ordinary DBF support expectations. The Python `dbf` package also supports memos and nulls. ([PyPI][1])

## 7.3 Deleted records

Honor dBASE deleted-record semantics:

- `DELETE` marks record deleted,
- `RECALL` unmarks,
- `PACK` physically removes deleted records,
- `SET DELETED ON|OFF` controls visibility.

dBASE materials and later dBASE docs preserve `PACK` as the physical removal operation for rows marked deleted. ([dBase.com][5])

______________________________________________________________________

## 8. DDL commands to support

## 8.1 `CREATE`

Support:

```text
CREATE <table>
```

Headless behavior:

- if run without a UI structure editor, it must be paired with a structured spec format in script, or support only:

```text
CREATE <table> FROM <structure_table>
```

### Recommended v1 extension

Support a modern-but-dBASE-flavored headless form:

```text
CREATE TABLE customers ;
  (cust_id C(10), name C(40), balance N(12,2), active L, joined D)
```

This is an implementation extension, not historical syntax, but it makes headless use practical.

### Historical compatibility target

Also support structure-extended workflow:

- `COPY STRUCTURE EXTENDED TO ...`
- `CREATE ... FROM ...`

dBASE help for later versions documents `CREATE ... STRUCTURE EXTENDED` and structure-driven creation; older tutorials also describe `COPY TO ... STRUCTURE EXTENDED` / `CREATE ... FROM ...` workflows. ([dBase.com][6])

## 8.2 `MODIFY STRUCTURE`

For headless runtime, do **not** implement an interactive designer. Instead define:

```text
MODIFY STRUCTURE <table> ADD COLUMN ...
MODIFY STRUCTURE <table> DROP COLUMN ...
MODIFY STRUCTURE <table> ALTER COLUMN ...
```

This is another headless extension. The legacy command opened a structure editor UI, which is not appropriate here. Later dBASE help explicitly describes `MODIFY STRUCTURE` as opening an interactive Table Designer. ([dBase.com][7])

## 8.3 `COPY STRUCTURE`

Support:

- `COPY STRUCTURE TO <newtable>`
- `COPY STRUCTURE EXTENDED TO <newtable>`

## 8.4 `ZAP`

Optional. If supported, require an unsafe mode flag because it destroys all records.

______________________________________________________________________

## 9. DML and navigational commands

## 9.1 Opening and selecting tables

Support:

```text
USE customers
USE customers ALIAS cust
USE customers EXCLUSIVE
USE
SELECT 1
SELECT cust
```

`USE` is central to xBase table access, and tutorials/documentation still show the classic pattern of opening a table and then issuing commands such as `INDEX ON`. ([dBase.com][8])

## 9.2 Record navigation

Support:

```text
GO TOP
GO BOTTOM
GO <n>
SKIP
SKIP <n>
EOF()
BOF()
RECNO()
RECCOUNT()
```

## 9.3 Search/filter

Support:

```text
LOCATE FOR <expr>
CONTINUE
SET FILTER TO <expr>
FOUND()
```

`LOCATE` remains part of the xBase command set and is commonly paired with indexed or filtered navigation. ([dBase.com][9])

## 9.4 Indexed search

Support a reduced form:

```text
SEEK <expr>
```

Semantics:

- works only when an active order exists,
- v1 order may be in-memory only,
- if no active order, raise runtime error.

`SEEK` is a standard indexed search command in xBase-family documentation. ([dBase.com][10])

## 9.5 Insert/update/delete

Support:

```text
APPEND BLANK
APPEND FROM <table>
INSERT INTO <table> (...) VALUES (...)     && optional extension
REPLACE field WITH expr
REPLACE field1 WITH expr1, field2 WITH expr2
REPLACE ALL field WITH expr FOR <cond>
DELETE
DELETE ALL FOR <cond>
RECALL
RECALL ALL FOR <cond>
PACK
```

`REPLACE`, `APPEND`, and deleted-record workflows are core dBASE behavior. Later docs and knowledgebase examples still treat `REPLACE ALL`, `REPLACE WHILE`, and `APPEND` as standard xBase commands. ([dBase.com][11])

## 9.6 Bulk traversal

Support:

```text
SCAN
  ...
ENDSCAN

SCAN FOR <expr>
  ...
ENDSCAN
```

`SCAN` is preferable to hand-written `DO WHILE .NOT. EOF()` loops for record traversal and is described that way in dBASE help. ([dBase.com][12])

## 9.7 Projection/display-ish commands

Since this is headless, commands that historically printed to screen should emit structured output:

```text
LIST
LIST ALL
LIST FIELDS name, balance FOR active
DISPLAY STRUCTURE
COUNT FOR <expr> TO <memvar>
SUM balance TO total FOR active
AVERAGE balance TO avg FOR active
```

______________________________________________________________________

## 10. Index support

Because `dbf` lacks persistent index-file support, define three levels:

### v1 required

- `SET ORDER TO` on interpreter-managed in-memory order
- `INDEX ON <expr> TAG <name>` creates transient order for current session only

### v1 optional

- save order metadata in sidecar JSON

### v2

- persistent `.ndx`/`.mdx`-like compatibility layer if desired

This limitation comes directly from the Python backend choice. ([PyPI][1])

______________________________________________________________________

## 11. Variables and memory

Support:

- `STORE <expr> TO <var>`
- simple assignment extension: `<var> = <expr>`
- `PRIVATE` optional later
- `PUBLIC` optional later
- parameters to `DO <program> WITH ...`

dBASE historically uses memory variables alongside field references, and `STORE` is part of that classic model. ([Wikipedia][2])

______________________________________________________________________

## 12. Functions to support in v1

## 12.1 Logical/database

- `EOF()`
- `BOF()`
- `FOUND()`
- `RECNO()`
- `RECCOUNT()`
- `DELETED()`

## 12.2 String

- `LEN()`
- `SUBSTR()`
- `LEFT()`
- `RIGHT()`
- `LTRIM()`
- `RTRIM()`
- `TRIM()`
- `UPPER()`
- `LOWER()`

## 12.3 Conversion

- `STR()`
- `VAL()`
- `DTOC()`
- `CTOD()`

## 12.4 Date

- `DATE()`
- `YEAR()`
- `MONTH()`
- `DAY()`

These categories match the well-known dBASE model of field manipulation plus string, numeric, and date functions. ([Wikipedia][2])

______________________________________________________________________

## 13. OS / filesystem commands

The user asked for “only the OS-related stuff that is easy to implement.” So support a **small safe subset**:

### 13.1 Required

```text
DIR [<pattern>]
CD <path>
PWD                 && extension
SET DEFAULT TO <path>
RENAME <old> TO <new>
COPY FILE <old> TO <new>
```

### 13.2 Optional

```text
MD <dir>            && make directory
RD <dir>            && remove empty directory only
ERASE <file>
```

### 13.3 Safety rules

- sandbox root configurable,
- no command may escape sandbox unless explicitly enabled,
- `ERASE`, `RD`, and `ZAP` disabled by default unless `unsafe=True`.

The spec is intentionally stricter than original DOS-era behavior.

______________________________________________________________________

## 14. Control-flow syntax

## 14.1 If

```text
IF <expr>
   ...
ELSEIF <expr>
   ...
ELSE
   ...
ENDIF
```

Later dBASE help describes `IF` executing the first true branch until `ELSEIF`, `ELSE`, or `ENDIF`. ([dBase.com][4])

## 14.2 Case

```text
DO CASE
CASE <expr>
   ...
CASE <expr>
   ...
OTHERWISE
   ...
ENDCASE
```

This matches standard dBASE/xBase branching semantics. ([dBase.com][13])

## 14.3 While

```text
DO WHILE <expr>
   ...
ENDDO
```

## 14.4 For

```text
FOR i = 1 TO 10
   ...
NEXT
```

or, if you want more modern internal normalization:

```text
FOR i = 1 TO 10 STEP 1
   ...
ENDFOR
```

Pick one canonical parser form and accept aliases if convenient.

## 14.5 Scan

```text
SCAN [FOR <expr>] [WHILE <expr>]
   ...
ENDSCAN
```

______________________________________________________________________

## 15. Error handling

## 15.1 Runtime errors

Raise structured errors with:

- code,
- message,
- source line,
- command text,
- current program,
- current work area.

## 15.2 Script behavior

Two modes:

- **fail-fast** default,
- `ON ERROR` hook later.

## 15.3 Common errors

- no active work area,
- table not found,
- field not found,
- invalid record number,
- exclusive access required,
- no active order for `SEEK`,
- parse error,
- unsafe command disabled.

______________________________________________________________________

## 16. Output model

Because this is headless, commands that historically displayed to the console should produce one of:

- plain text table output,
- JSON rows,
- Python object result.

Recommended CLI flags:

```text
--output text
--output json
--output csv
```

Examples:

- `LIST` returns rows,
- `DISPLAY STRUCTURE` returns table metadata,
- `COUNT TO x` stores variable and also returns numeric result in command mode.

______________________________________________________________________

## 17. Grammar sketch

Not a full formal grammar, but enough for implementation direction:

```ebnf
program        := { statement newline } ;

statement      := command
                | if_stmt
                | case_stmt
                | do_while_stmt
                | scan_stmt
                | for_stmt ;

if_stmt        := "IF" expr newline
                  { statement newline }
                  { "ELSEIF" expr newline { statement newline } }
                  [ "ELSE" newline { statement newline } ]
                  "ENDIF" ;

case_stmt      := "DO" "CASE" newline
                  { "CASE" expr newline { statement newline } }
                  [ "OTHERWISE" newline { statement newline } ]
                  "ENDCASE" ;

do_while_stmt  := "DO" "WHILE" expr newline
                  { statement newline }
                  "ENDDO" ;

scan_stmt      := "SCAN" [scope] [for_clause] [while_clause] newline
                  { statement newline }
                  "ENDSCAN" ;

for_stmt       := "FOR" ident "=" expr "TO" expr [ "STEP" expr ] newline
                  { statement newline }
                  ( "NEXT" | "ENDFOR" ) ;

command        := use_cmd
                | select_cmd
                | create_cmd
                | modify_structure_cmd
                | append_cmd
                | replace_cmd
                | delete_cmd
                | recall_cmd
                | pack_cmd
                | locate_cmd
                | seek_cmd
                | go_cmd
                | skip_cmd
                | store_cmd
                | list_cmd
                | display_cmd
                | dir_cmd
                | cd_cmd
                | rename_cmd
                | copy_file_cmd
                | do_cmd
                | return_cmd
                | exit_cmd
                | loop_cmd ;
```

______________________________________________________________________

## 18. Semantic rules

## 18.1 Current record

Every open work area has:

- record pointer,
- deleted visibility,
- filter expression,
- active order,
- EOF/BOF state.

## 18.2 Field resolution

Unqualified field names resolve against current work area.
Qualified names like `cust->name` are nice to have in v1.1.

## 18.3 Scope

Support common dBASE-ish scopes:

- `ALL`
- `NEXT n`
- `RECORD n`
- `REST`

These scopes are frequently paired with commands such as `COUNT`, `REPLACE`, and `LOCATE` in dBASE documentation/tutorial material. ([Studocu][14])

## 18.4 Deleted visibility

If `SET DELETED ON`, deleted rows are skipped by navigation and set operations unless explicitly addressed.

______________________________________________________________________

## 19. Suggested command subset for v1

If you want the first version to be implementable quickly, this is the right cut:

### Core table/session

- `USE`
- `SELECT`
- `CLOSE`
- `SET DEFAULT TO`
- `SET DELETED ON|OFF`

### DDL

- `CREATE TABLE ...`
- `COPY STRUCTURE TO`
- `COPY STRUCTURE EXTENDED TO`
- `CREATE FROM`
- `MODIFY STRUCTURE` headless extension

### DML

- `APPEND BLANK`
- `REPLACE`
- `DELETE`
- `RECALL`
- `PACK`
- `LIST`
- `DISPLAY STRUCTURE`
- `COUNT`
- `SUM`

### Navigation/query

- `GO TOP`
- `GO BOTTOM`
- `GO n`
- `SKIP`
- `LOCATE FOR`
- `CONTINUE`
- `SCAN ... ENDSCAN`
- `SEEK` with transient order support

### Language

- `STORE`
- assignment
- `IF`
- `DO CASE`
- `DO WHILE`
- `FOR`
- `DO program`
- `RETURN`
- `EXIT`
- `LOOP`

### Easy OS

- `DIR`
- `CD`
- `SET DEFAULT TO`
- `RENAME`
- `COPY FILE`

______________________________________________________________________

## 20. Example script

```text
SET DEFAULT TO data
USE customers ALIAS cust

LOCATE FOR cust->active .AND. cust->balance > 1000
IF FOUND()
    ? "Found a qualifying customer"
ENDIF

SCAN FOR cust->active
    REPLACE balance WITH balance * 1.02
ENDSCAN

COPY STRUCTURE TO customers_empty
```

______________________________________________________________________

## 21. Implementation notes for the clankers

## 21.1 Parser

Use a real parser, not regex soup.
Good options:

- Lark
- ANTLR grammar
- hand-written Pratt parser for expressions + recursive descent for statements

## 21.2 Runtime

Use explicit objects:

- `Interpreter`
- `WorkArea`
- `TableHandle`
- `Environment`
- `CommandResult`

## 21.3 Table abstraction

Hide `dbf` behind an adapter so you can later swap backend or add index sidecars.

## 21.4 Testing

You’ll want:

- parser golden tests,
- command semantic tests,
- DBF fixture tests,
- script integration tests,
- compatibility tests against known dBASE examples.

______________________________________________________________________

## 22. Recommendation

My recommendation is:

- use `dbf` for `.dbf/.dbt` file handling,

- define a **strict dBASE III+ subset**,

- add **two intentional headless extensions**:

  - `CREATE TABLE ... (...)`
  - headless `MODIFY STRUCTURE ...`

- defer real persistent index compatibility,

- keep OS commands sandboxed and small.

That gives you something implementable without pretending you’re recreating every corner of vintage dBASE.
