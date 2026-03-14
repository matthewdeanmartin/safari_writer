# safari_writer

A retro word processor plus a family of keyboard-first companion tools.

Main goals

- Better notepad
- Can post to Mastodon with spellcheck
- Can be used to read long documents
- Supports feature set of AtariWriter and adjacent applications, including database, image viewer, file browser
- 1980 Retro UI, Retro scripting languages
- Modern features, modern keybindings

## Installation

```bash
pipx install safari-writer
```

## Usage

You can run the main editor or the companion tools directly:

```bash
safari-writer
safari-dos browse C:\work --show-hidden --sort date --descending
safari-dos ls C:\work --sort type
safari-chat
safari-chat docs\index.md
safari-fed --folder Mentions
safari-base address_book.db
safari-reader --library C:\books
safari-repl demo.bas
safari-slides docs\safari_suite_tools.slides.md
safari-view open images\frog.png --mode st --no-dithering
safari-view render images\frog.png --mode 2600 --width 160 --height 192 --output out\frog-2600.png
```

Most people start with `safari-writer` and open the other tools from the Main Menu.

## Features

- **Safari Writer**: The core word processor.
  - Keybindings mostly modern, but somewhat influenced by original Atari.
  - Search and replace, word count, and alphabetize.
  - Style codes/printer codes for formatting.
  - Print/export to markdown, ANSI preview, postscript, or PDF.
- **Proofreader**: A built-in spell checker.
- **Mailmerge**: Database-driven form letters with a dedicated record editor.
- **Safari DOS**: A menu-driven way to do file browsing and manipulation, featuring a classic two-pane layout and a "Garbage" bin for file recovery.
- **Safari Chat**: A "Clippy" style helper based on ELIZA. It answers your questions using the help docs and offers emotional support—no LLMs involved.
- **Safari Base**: A dBASE-style shell for browsing and updating SQLite-backed address-book style data.
- **Safari Fed**: A calm, keyboard-driven Mastodon client styled after Pine and retro BBS readers. Queue-based reading, folder metaphors, thread view, and a direct handoff to Safari Writer.
- **Safari Reader**: A keyboard-first library, catalog, and long-form reading app.
- **Safari REPL**: A small Atari BASIC REPL and `.BAS` file runner with Writer handoff for loaded files.
- **Safari Slides**: A SlideMD presentation viewer with notes and fragment support.
- **Safari View**: A retro image viewer and renderer with Textual, Tk, and batch render entry points.
- **Safari BASIC**: The shared Atari BASIC-compatible macro engine used by Safari Writer and Safari Fed.

## Current Limitations

- Doesn't support original binary AtariWriter files
- Keybindings still evolving.

## Trademarks and stuff

I have no relationship to Atari. This is Safari Writer and has no relationship to Atari.

License is MIT.

Dual licensed with a Shareware license. Dual meaning, you pick which of the two you want to govern our relationship.

## Languages / Internationalization

Safari Writer automatically uses your operating system's locale. If you want to run the app in a different language, set the `SAFARI_LOCALE` environment variable before launching.

| Code | Language |
|------|------------|
| `en` | English |
| `eo` | Esperanto |
| `es` | Spanish |
| `fr` | French |
| `is` | Icelandic |
| `ru` | Russian |

**Linux / macOS:**

```bash
SAFARI_LOCALE=eo safari-writer
```

**Windows (PowerShell):**

```powershell
$env:SAFARI_LOCALE="eo"; safari-writer
```

**Windows (Command Prompt):**

```cmd
set SAFARI_LOCALE=eo && safari-writer
```

You can use a bare language code (`eo`) or a full IETF tag (`eo_EO`). If no catalog exists for the full tag, the bare code is tried automatically. If neither is found, the app falls back to English.
