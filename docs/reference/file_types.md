# File Types

Safari Writer and its companion tools work with a mix of document, program, and data files.

## Core writing formats

- **`.sfw`** — Safari Writer formatted document with inline control codes.
- **`.txt`** — Plain text.
- **`.md`** — Markdown.

## Suite scripting and program formats

- **`.bas`** — Safari Basic source. Used for Writer/Fed macros and Safari REPL programs.
- **`.asm`** — Safari ASM source. Used by the `safari-asm` interpreter and runnable from Safari DOS or the Writer editor.
- **`.prg`** — Safari Base program files. These are dBASE-style scripts that Safari Base can edit with `MODIFY COMMAND` and execute with `DO`.
- **`.py`** — Python scripts. Safari DOS and the editor runner can launch these too.

## Safari Base data files

Safari Base works with SQLite databases rather than a custom binary database format. Common file extensions include:

- **`.db`**
- **`.sqlite`**
- **`.sqlite3`**
- **`.db3`**

You typically open these with `safari-base path\to\data.db`.

## Editor highlighting

Safari Writer recognizes these suite-specific formats for syntax highlighting:

- **`.bas`** — highlighted as **Safari Basic**
- **`.asm`** — highlighted as **Safari ASM**
- **`.prg`** — highlighted as **Safari Base**

Safari Writer can also open many source-code and config files with syntax highlighting, including `.py`, `.js`, `.ts`, `.json`, `.toml`, `.yaml`, `.yml`, `.ini`, and `.cfg`.

## Where they show up

- **Safari Writer** can edit `.sfw`, `.txt`, `.md`, `.bas`, `.asm`, `.prg`, and many other plain-text files.
- **Safari DOS** can run `.bas`, `.asm`, `.prg`, and `.py`.
- **Safari REPL** focuses on `.bas`.
- **Safari ASM** focuses on `.asm`.
- **Safari Base** opens SQLite databases and works with `.prg` programs.
