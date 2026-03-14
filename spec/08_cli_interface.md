# Spec 08: Command-Line Interface

## 1. Overview

Safari Writer currently starts directly into the Textual application and always lands on the Main Menu. This spec defines a future **argparse-based** CLI that supports:

1. **direct-entry TUI startup** — the user can launch the app straight into the editor, proofreader, global format, mail merge, print/export flow, or file browser; and
1. **headless operation** — the user can run non-interactive commands for export, proofing, format conversion, and mail-merge inspection without booting Textual.

This document is a behavior spec only. It does **not** require implementation in this phase.

______________________________________________________________________

## 2. Design Goals

- Preserve the existing default UX: `safari-writer` with no arguments still opens the TUI Main Menu.
- Use the Python standard library `argparse` module.
- Prefer **explicit subcommands** over overloaded flags.
- Keep command dispatch easy to unit test with `pytest`.
- Keep TUI startup logic separate from headless logic.
- Reuse existing non-UI logic where possible (`format_codec.py`, `export_md.py`, `export_ps.py`, proofreader helpers, mail-merge data model).
- Return explicit exit codes instead of calling `sys.exit()` deep inside helpers.

### Non-goals

- No alternate CLI framework (`click`, `typer`, etc.).
- No implementation-specific code in this spec.
- No shell-specific completion scripts in the first CLI pass.

______________________________________________________________________

## 3. Invocation Model

## 3.1 Primary entry point

The installed console script remains:

```text
safari-writer
```

It continues to map to `safari_writer.main:main`.

## 3.2 Top-level grammar

```text
safari-writer [global-options] [command] [command-options]
```

If `command` is omitted, the CLI behaves like:

```text
safari-writer tui menu
```

## 3.3 Compatibility shorthand

To support the common “open a file immediately” case, a single bare file argument should be accepted as a convenience alias for direct-entry editor startup:

```text
safari-writer draft.sfw
```

Equivalent to:

```text
safari-writer tui edit --file draft.sfw
```

If the bare positional form is supported, it must be limited to exactly one file path and must not conflict with explicit subcommands.

______________________________________________________________________

## 4. Global Options

These options apply before the first subcommand.

| Option | Meaning |
|---|---|
| `-h`, `--help` | Show top-level help and exit with code `0`. |
| `--version` | Show version string and exit with code `0`. |
| `--cwd PATH` | Resolve relative input/output paths as if launched from `PATH`; fail if `PATH` does not exist or is not a directory. |
| `--encoding NAME` | Default text encoding for headless file I/O when a command supports an override; default remains UTF-8. |
| `-q`, `--quiet` | Suppress non-error status output in headless mode. |
| `-v`, `--verbose` | Emit additional progress/details in headless mode. |

### Global option rules

- `--quiet` and `--verbose` are mutually exclusive.
- `--cwd` affects path resolution for both headless commands and TUI startup requests.
- TUI commands may accept `--quiet` / `--verbose` syntactically, but they do not need to change runtime behavior in the initial implementation.

______________________________________________________________________

## 5. Command Tree

```text
safari-writer
├── tui
│   ├── menu
│   ├── edit
│   ├── proofreader
│   ├── global-format
│   ├── mail-merge
│   ├── print
│   ├── index-current
│   └── index-external
├── export
│   ├── markdown
│   ├── postscript
│   └── ansi
├── proof
│   ├── check
│   ├── list
│   └── suggest
├── format
│   ├── encode
│   ├── decode
│   └── strip
└── mail-merge
    ├── inspect
    ├── subset
    ├── append
    └── validate
```

The `tui` branch is for direct-entry interactive use. All other top-level branches are headless.

______________________________________________________________________

## 6. TUI Commands

## 6.1 Shared behavior for all `tui` subcommands

- These commands launch the Textual app rather than a headless handler.
- CLI parsing determines a **startup request** that tells the app which screen/workflow to enter first.
- If `--file` is provided, the file is loaded before the first screen is shown.
- File load errors must be surfaced immediately in the TUI message area when possible; if startup cannot continue, the command should fail before entering Textual with a non-zero exit code.

### Shared TUI options

| Option | Meaning |
|---|---|
| `--file PATH` | Preload a document before entering the requested TUI destination. |
| `--read-only` | Open the document in view-only mode when the eventual implementation supports it. |
| `--cwd PATH` | Inherited global path resolution. |

`--read-only` is forward-looking. It should exist in the CLI spec now so parser shape stays stable, even if initial implementation treats it as accepted-but-not-yet-enforced.

## 6.2 `tui menu`

Open the standard Main Menu.

```text
safari-writer tui menu
```

### Behavior

- Equivalent to today’s default startup.
- `--file` may preload the document into state while still landing on the Main Menu.
- If `--file` is omitted, startup uses a fresh in-memory document state.

## 6.3 `tui edit`

Open directly in the editor.

```text
safari-writer tui edit [--file PATH | --new]
```

### Options

| Option | Meaning |
|---|---|
| `--file PATH` | Load the specified file and enter the editor. |
| `--new` | Start a new blank document and enter the editor. |
| `--cursor-line N` | Initial 1-based line number. |
| `--cursor-column N` | Initial 1-based column number. |

### Rules

- `--file` and `--new` are mutually exclusive.
- If neither is supplied, behavior is equivalent to `--new`.
- Cursor coordinates are clamped to the loaded buffer bounds.
- If `--cursor-column` is supplied without `--cursor-line`, line defaults to `1`.

## 6.4 `tui proofreader`

Open directly in the Proofreader module.

```text
safari-writer tui proofreader [--file PATH] [--mode highlight|print|correct|search]
```

### Options

| Option | Meaning |
|---|---|
| `--file PATH` | Load a document before entering the module. |
| `--mode MODE` | Select the initial proofreader action. |
| `--personal-dict PATH` | Preload a personal dictionary file. Repeatable. |

### Rules

- If `--mode` is omitted, land on the Proofreader menu.
- `--mode highlight` enters Highlight Errors immediately.
- `--mode print` enters Print Errors immediately.
- `--mode correct` enters Correct Errors immediately.
- `--mode search` enters Dictionary Search immediately.
- Personal dictionary load failures must be reported explicitly.

## 6.5 `tui global-format`

Open directly in Global Format.

```text
safari-writer tui global-format [--file PATH]
```

### Behavior

- If `--file` is given, load the file first so the user edits format in the context of that document.
- Without `--file`, open Global Format using default in-memory state.

## 6.6 `tui mail-merge`

Open directly in the Mail Merge module.

```text
safari-writer tui mail-merge [--database PATH]
```

### Options

| Option | Meaning |
|---|---|
| `--database PATH` | Load a mail-merge JSON database before entering the module. |
| `--mode MODE` | Optional initial mode: `menu`, `enter`, `update`, `format`, `subset`. |

### Rules

- If `--database` is invalid, fail before launching TUI.
- If `--mode` is omitted, land on the Mail Merge main menu.

## 6.7 `tui print`

Open directly in the Print / Export flow.

```text
safari-writer tui print [--file PATH] [--target ansi|markdown|postscript]
```

### Options

| Option | Meaning |
|---|---|
| `--file PATH` | Load a document before entering print/export. |
| `--target TARGET` | Select the initial print target instead of first showing the modal chooser. |

### Rules

- If `--target` is omitted, open the standard Print dialog.
- `--target ansi` opens preview directly.
- `--target markdown` and `--target postscript` open the save/export prompt path directly.

## 6.8 `tui index-current`

Open the current-folder file browser immediately.

```text
safari-writer tui index-current [--path PATH]
```

- `--path` defaults to the effective working directory.
- If `--path` is supplied, it must be a directory.

## 6.9 `tui index-external`

Open the external-drive browser immediately.

```text
safari-writer tui index-external
```

### Rules

- If no external drives are available, the startup request should still succeed and land on the same fallback/message path the TUI would normally use.

______________________________________________________________________

## 7. Headless Export Commands

These commands do not start Textual.

## 7.1 Shared export behavior

- All export commands require an input document path.
- `.sfw` input is decoded through the Safari Writer format codec.
- Non-`.sfw` input is treated as plain text.
- If merge fields exist and no merge database is supplied, placeholders remain unresolved.
- On success, return exit code `0`.
- On argument or runtime failure, return a non-zero exit code and write a human-readable message to stderr.

## 7.2 `export markdown`

```text
safari-writer export markdown INPUT [-o OUTPUT] [--merge-db PATH] [--stdout]
```

### Options

| Option | Meaning |
|---|---|
| `INPUT` | Source document to export. |
| `-o`, `--output PATH` | Destination `.md` file. |
| `--merge-db PATH` | Optional mail-merge database to apply. |
| `--stdout` | Write Markdown to stdout instead of a file. |

### Rules

- `--output` and `--stdout` are mutually exclusive.
- If neither is provided, default output path is `<input-stem>.md`.

## 7.3 `export postscript`

```text
safari-writer export postscript INPUT [-o OUTPUT] [--merge-db PATH]
```

### Rules

- Default output path is `<input-stem>.ps`.
- Output is text PostScript written as UTF-8.

## 7.4 `export ansi`

```text
safari-writer export ansi INPUT [--page N] [--stdout]
```

### Purpose

This is the headless counterpart to preview rendering. It exists primarily for scripting and pytest coverage of the page-layout/rendering pipeline.

### Rules

- Default output is stdout.
- `--page N` restricts output to a single rendered page when supported.
- If `--page` is out of range, return a non-zero exit code.

______________________________________________________________________

## 8. Headless Proof Commands

These commands use proofing logic without booting the module UI.

## 8.1 `proof check`

```text
safari-writer proof check INPUT [--personal-dict PATH ...]
```

### Behavior

- Exit `0` if no spelling errors are found.
- Exit `1` if spelling errors are found.
- Exit `2` for usage/runtime problems.
- Human-readable summary goes to stdout unless `--quiet` is active.

## 8.2 `proof list`

```text
safari-writer proof list INPUT [--personal-dict PATH ...] [--json]
```

### Behavior

- Emit each spelling issue with at least line, column, and token.
- `--json` returns structured output intended for scripting and pytest assertions.
- Exit `0` even when errors are found; use non-zero only for failures to execute.

## 8.3 `proof suggest`

```text
safari-writer proof suggest WORD
```

### Behavior

- Print suggestion candidates, one per line by default.
- Exit `0` whether or not suggestions exist.
- Exit non-zero only when the spell backend cannot be initialized and strict behavior is requested in a later phase.

______________________________________________________________________

## 9. Headless Format Commands

These commands expose the `.sfw` codec directly.

## 9.1 `format encode`

```text
safari-writer format encode INPUT [-o OUTPUT]
```

- Read plain text input and write `.sfw`-encoded output.
- Default output path is `<input-stem>.sfw`.

## 9.2 `format decode`

```text
safari-writer format decode INPUT [-o OUTPUT]
```

- Decode `.sfw` tags into Safari Writer’s in-memory control-character text representation.
- Default output path is `<input-stem>.decoded.txt`.

## 9.3 `format strip`

```text
safari-writer format strip INPUT [-o OUTPUT]
```

- Remove inline formatting control codes and write plain text.
- Default output path is `<input-stem>.txt`.

______________________________________________________________________

## 10. Headless Mail-Merge Commands

These commands operate on the JSON database format without entering the TUI module.

## 10.1 `mail-merge inspect`

```text
safari-writer mail-merge inspect DATABASE [--json]
```

### Behavior

- Show schema fields, field widths, record count, records free, and filename.
- `--json` produces structured output suitable for tests and scripting.

## 10.2 `mail-merge subset`

```text
safari-writer mail-merge subset DATABASE --field N --low VALUE --high VALUE [--json]
```

### Behavior

- Apply the same inclusive range semantics as the TUI subset builder.
- Output either matching record indexes or full records; the first implementation should choose one and document it consistently.
- `--json` is strongly preferred for deterministic automated tests.

## 10.3 `mail-merge append`

```text
safari-writer mail-merge append BASE_DB OTHER_DB [-o OUTPUT]
```

### Behavior

- Validate schema compatibility first.
- On success, write a merged database file.
- Default output path is `<base-stem>.merged.json`.

## 10.4 `mail-merge validate`

```text
safari-writer mail-merge validate DATABASE
```

### Behavior

- Confirm structural validity: field count, max lengths, record width consistency, record limit, and JSON shape.
- Exit `0` for valid data, `1` for invalid data, `2` for execution failures.

______________________________________________________________________

## 11. Parser and Dispatch Requirements

## 11.1 Parser construction

The CLI should be built with `argparse.ArgumentParser` plus nested subparsers.

Recommended parser layout:

- top-level parser
  - global options
  - top-level subparsers with `dest="command"`
- nested subparsers for groups like `tui`, `export`, `proof`, `format`, `mail-merge`

### Required parser behaviors

- Each actionable leaf command sets a callable handler with `set_defaults(handler=...)`.
- Help text must show both the immediate branch and the next available subcommands.
- Mutual exclusions should be enforced by `argparse`, not by ad-hoc post-parse string checks when possible.

## 11.2 Dispatch model

The future implementation should separate the CLI into three layers:

1. **parser layer** — builds `argparse` objects and parses argv;
1. **request layer** — converts parsed args into typed startup/export/proof/mail-merge requests;
1. **execution layer** — performs TUI launch or headless work and returns an exit code.

This keeps parser tests, request-conversion tests, and execution tests independent.

______________________________________________________________________

## 12. TUI Startup Request Model

Direct-entry behavior should not be expressed as raw parser conditionals scattered through the Textual app. Instead, the CLI should produce a startup configuration object with fields like:

- destination (`menu`, `edit`, `proofreader`, `global_format`, `mail_merge`, `print`, `index_current`, `index_external`)
- optional document path
- optional mail-merge database path
- optional proofreader mode
- optional print target
- optional cursor line/column
- read-only flag

The app should receive this object at construction time and use it in `on_mount()` to decide which screen to push first.

______________________________________________________________________

## 13. Exit Codes

| Exit code | Meaning |
|---|---|
| `0` | Success |
| `1` | Command completed but found a negative result (for example `proof check` found spelling errors, or `mail-merge validate` found invalid data) |
| `2` | Usage error, parse error, file I/O failure, unsupported request, or other execution failure |

The implementation should keep exit code meanings stable across commands.

______________________________________________________________________

## 14. Error Handling Rules

- Parse errors remain under argparse control and exit as usage errors.
- File-not-found, invalid-path, and invalid-extension errors must name the offending path.
- Headless commands must write errors to stderr.
- TUI direct-entry failures that occur before Textual starts should also write to stderr and return a non-zero exit code.
- TUI-internal failures after startup should use the app’s message/status surface.
- No silent fallback from a requested direct-entry destination to some other screen unless explicitly specified.

Example: `safari-writer tui proofreader --mode correct --file missing.sfw` must fail clearly, not quietly land on the main menu.

______________________________________________________________________

## 15. Pytest Testability Requirements

The eventual CLI implementation should be designed so tests can exercise parser behavior without launching Textual.

## 15.1 Required public seams

- `build_parser() -> argparse.ArgumentParser`
- `parse_args(argv: list[str]) -> argparse.Namespace`
- `main(argv: list[str] | None = None) -> int`
- per-command request builders or handlers that accept parsed args directly

## 15.2 Testing expectations

### Parser tests

- bare invocation
- help/version
- valid nested subcommands
- invalid subcommands
- mutual exclusion errors
- default output-path derivation

### Request-conversion tests

- `tui edit --file demo.sfw`
- `tui proofreader --mode correct --personal-dict foo.txt`
- `export markdown doc.sfw --stdout`
- `mail-merge subset db.json --field 2 --low A --high E`

### Execution tests

- headless export returns expected content and exit code
- proof commands return correct exit-code contract
- format commands preserve/strip tags correctly
- TUI commands build the correct startup request without requiring a real terminal

## 15.3 Anti-patterns to avoid

- calling `sys.exit()` inside non-entry helpers
- reading `sys.argv` directly in multiple places
- printing directly from business-logic helpers instead of using injected streams or returned values
- entangling parser construction with Textual app imports when tests only need parser coverage

______________________________________________________________________

## 16. Help and Documentation Expectations

- `safari-writer --help` should show the command groups.
- `safari-writer tui --help` should explain direct-entry TUI use.
- `safari-writer export --help` should list the export formats.
- Every leaf command must include at least one example in its help epilog or README documentation.

Representative examples:

```text
safari-writer
safari-writer draft.sfw
safari-writer tui proofreader --file draft.sfw --mode correct
safari-writer export markdown draft.sfw --stdout
safari-writer proof list draft.sfw --json
safari-writer mail-merge inspect contacts.json
```

______________________________________________________________________

## 17. Phased Delivery Guidance

The interface should be implemented in phases, but the parser shape should be planned up front.

### Phase A

- top-level parser
- `tui menu`
- `tui edit`
- bare-file shorthand
- `export markdown`
- `export postscript`

### Phase B

- remaining direct-entry TUI destinations
- `proof check` / `proof list`
- `format encode` / `decode` / `strip`

### Phase C

- `export ansi`
- headless mail-merge commands
- richer structured output modes

This preserves a stable public CLI while allowing the implementation to grow incrementally.
