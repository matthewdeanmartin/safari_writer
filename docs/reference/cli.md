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
