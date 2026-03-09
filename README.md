# safari_writer

A text editor with some support for style codes. UI is inspired by AtariWriter but there are a lot of differences.

## Installation

```bash
pipx install safari-writer
```

## Usage

You can run the main editor or the companion tools directly:

```bash
# Start the word processor
safari-writer

# Start the file manager
safari-dos

# Start the help assistant
safari-chat

# Start the Mastodon client
safari-fed
```

Follow the menus. 

## Features

- **Safari Writer**: The core text editor.
  - Keybindings mostly modern, but somewhat influenced by original Atari.
  - Search and replace, word count, and alphabetize.
  - Style codes/printer codes for formatting.
  - Print/export to markdown, ANSI preview, or postscript. 
- **Proofreader**: A built-in spell checker.
- **Mailmerge**: Database-driven form letters with a dedicated record editor.
- **Safari DOS**: A menu-driven way to do file browsing and manipulation, featuring a classic two-pane layout and a "Garbage" bin for file recovery.
- **Safari Chat**: A "Clippy" style helper based on ELIZA. It answers your questions using the help docs and offers emotional support—no LLMs involved.
- **Safari Base**: An alternative UI for the mail merge data files (currently in extreme beta).
- **Safari Fed**: A calm, keyboard-driven Mastodon client styled after Pine and retro BBS readers. Queue-based reading, folder metaphors, thread view, and a direct handoff to Safari Writer.

## Roadmap

- **Safari Basic**: An Atari BASIC subset REPL.
- Maybe support for the old binary format of Atari Writer files. 

## Trademarks and stuff

I have no relationship to Atari. This is Safari Writer and has no relationship to Atari.

License is MIT.
