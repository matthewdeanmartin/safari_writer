# PRG Programs

`.prg` is the program-file format used by Safari Base. These files are plain-text dBASE-style scripts, not database files.

## What `.prg` files do

Safari Base uses `.prg` files for repeatable command workflows such as:

- table setup
- report generation
- scripted browsing or lookup flows
- lightweight automation around a SQLite-backed database

Safari Base can:

- edit them with `MODIFY COMMAND <file>`
- run them with `DO <file>`

If you leave off the extension, Safari Base automatically resolves the filename as `.prg`.

## Where files live

When Safari Base has an open database, program files are resolved relative to the database directory. Otherwise they are resolved from the current working directory.

## Running a program

From inside Safari Base:

```text
DO hello.prg
```

From the full-screen shell, `DO hello` also works because `.prg` is implied.

## Editing a program

```text
MODIFY COMMAND report.prg
```

This opens the dedicated program editor for `.prg` files.

## Relationship to SQLite databases

Safari Base uses SQLite for table storage, typically in files such as `.db`, `.sqlite`, or `.sqlite3`. The `.prg` file is the script that operates on that data; it is not the database itself.

## Related tools

- **Safari Base** — owns the `.prg` workflow.
- **Safari Writer** — can open `.prg` files as plain text with Safari Base highlighting.
- **Safari DOS** — can launch `.prg` files directly.
