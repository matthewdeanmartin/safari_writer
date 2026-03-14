# Safari Base

Safari Base is a dBASE-style shell for browsing and updating SQLite-backed data. In the Safari Writer main menu it appears as **Base (Address Book)**.

## Starting Safari Base

```bash
safari-base
safari-base address_book.db
```

If you do not pass a database path, Safari Base starts with an in-memory session.

Safari Base expects SQLite databases. Common filenames include `address_book.db`, `contacts.sqlite`, or other standard SQLite extensions such as `.db`, `.sqlite`, `.sqlite3`, and `.db3`.

## Current Workflow

Safari Base is currently centered on a single-screen shell:

- Browse the current table.
- Inspect table structure.
- Switch between tables.
- Append records.
- Use the Assist menu for classic dBASE-style command shortcuts.

## Important Keys

- **F1** — Show built-in help.
- **F6** — Show table structure.
- **F7** — Show tables.
- **F8** — Return to browse mode.
- **F10 / F2** — Open the Assist menu.
- **F3 / Ctrl + A** — Start append mode.
- **Insert** — Toggle insert mode.
- **CapsLock / F9** — Toggle caps mode.
- **Esc** — Return to browse mode, clear the prompt, or quit if the prompt is empty.
- **Ctrl + Q** — Quit Safari Base immediately.

## Commands and `.prg` programs

Safari Base supports interactive shell commands plus dBASE-style program files:

- `HELP`, `?`, `COMMANDS`
- `BROWSE`, `LIST`, `DISPLAY`
- `TABLES`, `USE <table>`, `STRUCT`
- `APPEND`, `EDIT`, `DELETE`, `ASSIST`
- `MODIFY COMMAND <file>` — Open or create a `.prg` program in the full-screen editor.
- `DO <file>` — Run a `.prg` program.

If you omit the extension, Safari Base resolves program filenames as `.prg` automatically.

## What `.prg` means here

`.prg` files are Safari Base program files: plain-text dBASE-style scripts stored next to your database or in the current working directory. They are not SQLite database files themselves.

Use them when you want repeatable table workflows such as setup scripts, reports, and small data-entry helpers. See the dedicated reference page: [PRG Programs](../reference/prg_language.md).

## Current Notes

Some classic dBASE-style commands are still placeholders, so Safari Base is best treated as an early but usable table browser and data-entry shell rather than a full clone.
