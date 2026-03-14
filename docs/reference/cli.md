# Command Line Interface

You can use Safari Writer from the command line without the full interface.

## Safari Writer Commands

- `safari-writer` — Launch the main menu and editor shell.

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

## Safari DOS Commands

- `safari-dos` — Launch the DOS main menu.
- `safari-dos browse PATH --show-hidden --sort date --descending` — Open the browser on a directory with startup options.
- `safari-dos ls PATH --sort type` — List a directory without opening the TUI.
- `safari-dos help` — Jump straight to the DOS help screen.

## Safari Chat Commands

- `safari-chat` — Launch Safari Chat with the bundled default help document.
- `safari-chat PATH_TO_HELP.md` — Load a specific Markdown help document instead.

## Safari Fed Commands

- `safari-fed` — Launch the Mastodon client in demo mode (no credentials needed).
- `safari-fed --folder FOLDER` — Open a specific folder on launch (`Home`, `Mentions`, `Bookmarks`, `Drafts`, `Sent`, `Deferred`).
- `safari-fed --account NAME` — Start with a named Mastodon identity selected.

## Safari Reader Commands

- `safari-reader` — Launch the reader with the default local library.
- `safari-reader --library PATH` — Use a specific library directory.

## Safari REPL Commands

- `safari-repl` — Launch the standalone Atari BASIC REPL.
- `safari-repl FILE` — Load a `.BAS` program on startup.
- `safari-writer tui safari-repl` — Open Safari REPL inside the Safari Writer shell.
- `safari-writer tui safari-repl --file FILE` — Open the embedded REPL with a `.BAS` file preloaded.

## Safari Slides Commands

- `safari-slides` — Launch Safari Slides with the built-in welcome deck.
- `safari-slides DECK.slides.md` — Open a specific SlideMD deck.

## Safari View Commands

- `safari-view` — Legacy shorthand for opening the Textual browser.
- `safari-view open IMAGE --mode st --no-dithering` — Open one image directly in the Textual viewer.
- `safari-view browse PATH --select IMAGE` — Start in a directory-focused browser session.
- `safari-view render IMAGE --mode 2600 --width 160 --height 192 -o OUTPUT.png` — Render an image through the retro pipeline without opening the UI.
- `safari-view tk --image IMAGE --mode native` — Launch the Tk frontend.

## Safari Base Commands

- `safari-base` — Launch Safari Base with an in-memory session.
- `safari-base ADDRESS_BOOK.db` — Open a specific SQLite database file.
