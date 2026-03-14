# Command Line Interface

You can use Safari Writer from the command line without the full interface.

## Export Commands

- `safari-writer export markdown INPUT -o OUTPUT` — Export a `.sfw` file to Markdown.
- `safari-writer export postscript INPUT -o OUTPUT` — Export a `.sfw` file to PostScript.
- `safari-writer export ansi INPUT` — View formatted output in your terminal.

## Proofreading Commands

- `safari-writer proof check INPUT` — Scan for misspelled words.
- `safari-writer proof suggest WORD` — Get spelling suggestions for a word.

## Formatting Commands

- `safari-writer format strip INPUT -o OUTPUT` — Remove all formatting codes from a file.
- `safari-writer format encode INPUT -o OUTPUT` — Add or fix formatting markers.

## Mail Merge Commands

- `safari-writer mail-merge validate DATABASE` — Check a database for errors.
- `safari-writer mail-merge inspect DATABASE` — View database schema and records.

## Safari Fed Commands

- `safari-fed` — Launch the Mastodon client in demo mode (no credentials needed).
- `safari-fed --folder FOLDER` — Open a specific folder on launch (`Home`, `Mentions`, `Bookmarks`, `Drafts`, `Sent`, `Deferred`).
- `safari-fed --account NAME` — Start with a named Mastodon identity selected.

## Safari REPL Commands

- `safari-repl` — Launch the standalone Atari BASIC REPL.
- `safari-repl FILE` — Load a `.BAS` program on startup.
- `safari-writer tui safari-repl` — Open Safari REPL inside the Safari Writer shell.
- `safari-writer tui safari-repl --file FILE` — Open the embedded REPL with a `.BAS` file preloaded.
