# Installation

Safari Writer is distributed as a Python package and can be installed with the standard Python tooling you already use.

## Requirements

- **Python**: 3.10 or later.
- **Dependencies**: Runtime dependencies such as Textual, Pygments, and optional extras like `pyenchant` are installed automatically by the package manager you choose.

## Install with pip

```bash
pip install safari-writer
```

## Install with pipx

`pipx` is a good fit if you want the Safari command-line apps available globally without managing a project-specific virtual environment.

```bash
pipx install safari-writer
```

## Install with uv

If you already use `uv`, you can install the app the same way:

```bash
uv tool install safari-writer
```

## Installed commands

Once installed, these entry points are available from your shell:

- `safari-writer` — Start the word processor and main suite hub.
- `safari-dos` — Open the file browser and launcher.
- `safari-chat` — Open the bundled help assistant.
- `safari-base` — Launch the dBASE-style SQLite shell.
- `safari-fed` — Launch the Mastodon client.
- `safari-asm` — Run a Safari ASM program from a file or stdin.
- `safari-repl` — Open the Atari BASIC REPL and file runner.
- `safari-reader` — Open the library and reading app.
- `safari-slides` — Open the SlideMD presentation viewer.
- `safari-view` — Open the retro image viewer and renderer.
- `safari-view-tk` — Launch the Tk-based Safari View frontend directly.

## First-run examples

```bash
safari-writer
safari-dos browse C:\work
safari-base address_book.db
safari-asm demo.asm -- demo-arg
safari-repl demo.bas
safari-view open images\frog.png --mode st
```
