# safari_writer

A text editor with some support for style codes. UI is inspired by AtariWriter but there are a lot of differences.

## Installation

```bash
pipx install safari-writer
```

## Usage

You can run the main editor or the companion tools directly:

```bash
safari-writer # Word processor 
safari-dos # File browser/manager
safari-chat # Eliza style help chat bot
safari-fed # Mastodon client
safari-base  # xbase clone
safari-repl # BASIC repl
```

Follow the menus. 

## Features

- **Safari Writer**: The core text editor.
  - Keybindings mostly modern, but somewhat influenced by original Atari.
  - Search and replace, word count, and alphabetize.
  - Style codes/printer codes for formatting.
  - Print/export to markdown, ANSI preview, postscript, or PDF.
- **Proofreader**: A built-in spell checker.
- **Mailmerge**: Database-driven form letters with a dedicated record editor.
- **Safari DOS**: A menu-driven way to do file browsing and manipulation, featuring a classic two-pane layout and a "Garbage" bin for file recovery.
- **Safari Chat**: A "Clippy" style helper based on ELIZA. It answers your questions using the help docs and offers emotional support—no LLMs involved.
- **Safari Base**: An alternative UI for the mail merge data files (currently in extreme beta).
- **Safari Fed**: A calm, keyboard-driven Mastodon client styled after Pine and retro BBS readers. Queue-based reading, folder metaphors, thread view, and a direct handoff to Safari Writer.
- **Safari BASIC**: Atari BASIC compatible BASIC for macros

## Current Limitations

- Doesn't support original binary AtariWriter files
- Keybindings still evolving.

## Trademarks and stuff

I have no relationship to Atari. This is Safari Writer and has no relationship to Atari.

License is MIT.

Dual licensed with a Shareware license. Dual meaning, you pick which of the two you want to govern our relationship.

## Languages / Internationalization

Safari Writer automatically uses your operating system's locale. If you want to run the app in a different language, set the `SAFARI_LOCALE` environment variable before launching.

| Code | Language   |
|------|------------|
| `en` | English    |
| `eo` | Esperanto  |
| `es` | Spanish    |
| `fr` | French     |
| `is` | Icelandic  |
| `ru` | Russian    |

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
