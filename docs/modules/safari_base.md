# Safari Base

Safari Base is a dBASE-style shell for browsing and updating SQLite-backed data. In the Safari Writer main menu it appears as **Base (Address Book)**.

## Starting Safari Base

```bash
safari-base
safari-base address_book.db
```

If you do not pass a database path, Safari Base starts with an in-memory session.

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

## Current Notes

Some classic dBASE-style commands are still placeholders, so Safari Base is best treated as an early but usable table browser and data-entry shell rather than a full clone.
