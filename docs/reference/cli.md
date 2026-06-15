# Command Line Interface

Safari Writer ships several small CLIs. Every standalone app now supports `--version`.

## Safari Writer

| Command | Behavior |
| --- | --- |
| `safari-writer` | Launch the main menu and editor shell. |
| `safari-writer FILE.sfw` | Shorthand for `safari-writer tui edit --file FILE.sfw`. |
| `safari-writer FILE.sfw --cursor-line 10 --no-splash` | Bare-file shorthand still accepts trailing global and edit options. |
| `safari-writer tui edit --new` | Open an untitled blank document. |
| `safari-writer tui edit --file FILE.sfw` | Open a document directly in the editor. If the file does not exist yet, Safari Writer opens a blank unsaved document associated with that path and does not create the file until you save. |
| `safari-writer tui proofreader --file FILE.sfw --mode correct` | Open directly in the proofreader. |
| `safari-writer tui global-format --file FILE.sfw` | Open Global Format. |
| `safari-writer tui mail-merge --database DATA.json --mode update` | Open Mail Merge. |
| `safari-writer tui print --file FILE.sfw --target pdf` | Jump straight to print/export flow. |
| `safari-writer tui safari-dos --path PATH` | Open Safari DOS inside Safari Writer. |
| `safari-writer tui safari-reader` | Open Safari Reader inside Safari Writer. |
| `safari-writer tui safari-repl --file PROGRAM.bas` | Open Safari REPL inside Safari Writer. |
| `safari-writer tui safari-slides --file DECK.slides.md` | Open Safari Slides inside Safari Writer. |

`--read-only` is supported for `menu`, `edit`, `proofreader`, `print`, and embedded `safari-slides`. In read-only mode Safari Writer blocks editing, correction, saving, delete/create actions, and similar write paths. `--read-only` is rejected for `global-format` and `mail-merge`.

## Export Commands

- `safari-writer export markdown INPUT -o OUTPUT`
- `safari-writer export postscript INPUT -o OUTPUT`
- `safari-writer export pdf INPUT -o OUTPUT`
- `safari-writer export slides INPUT -o OUTPUT`
- `safari-writer export ansi INPUT --page 2`

## Proofing and Formatting

- `safari-writer proof check INPUT`
- `safari-writer proof suggest WORD`
- `safari-writer format strip INPUT -o OUTPUT`
- `safari-writer format encode INPUT -o OUTPUT`
- `safari-writer mail-merge validate DATABASE`
- `safari-writer mail-merge inspect DATABASE`

## Safari DOS

- `safari-dos`
- `safari-dos browse PATH --show-hidden --sort date --descending`
- `safari-dos ls PATH --sort type`
- `safari-dos help`

## Safari Chat

- `safari-chat`
- `safari-chat PATH_TO_HELP.md`

## Safari Fed

- `safari-fed`
- `safari-fed --folder FOLDER`
- `safari-fed --account NAME`

## Safari Reader

- `safari-reader`
- `safari-reader --library PATH`

## Safari REPL

- `safari-repl`
- `safari-repl FILE.bas`

## Safari Slides

- `safari-slides`
- `safari-slides DECK.slides.md`

If the requested deck does not exist yet, Safari Slides opens a blank unsaved deck associated with that filename and waits for an explicit save.

## Safari View

- `safari-view`
- `safari-view open IMAGE --mode st --no-dithering`
- `safari-view browse PATH --select IMAGE`
- `safari-view render IMAGE --mode 2600 --width 160 --height 192 -o OUTPUT.png`
- `safari-view tk --image IMAGE --mode native`

## Safari Base

- `safari-base`
- `safari-base ADDRESS_BOOK.db`
