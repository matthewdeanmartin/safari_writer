# Safari Basic

Safari Basic is the Atari BASIC-compatible language runtime used by Safari Writer macros, Safari Fed macros, and Safari REPL.

## Features

- **Macro Runtime**: Used by Safari Writer and Safari Fed to run `.BAS` automation scripts.
- **Atari-Style Language**: Supports a subset of classic Atari BASIC syntax.
- **Numeric Precision**: Uses modern floating-point precision.
- **Mandatory DIM**: Strings and arrays must be explicitly dimensioned before use.

Safari Basic is not a separate end-user TUI. If you want an interactive shell, use **Safari REPL**.

## Where You Use It

- **Safari Writer** — Press **Ctrl + Backslash** to open the macro picker.
- **Safari Fed** — Press **~** to run a macro against the current post and save the output as a draft.
- **Safari REPL** — Use the standalone REPL when you want to experiment with BASIC interactively.

## Using Safari Basic as a Macro System

Safari Basic is also the macro engine for Safari Writer and Safari Fed. You can write `.BAS` files that read document and post context, then `PRINT` text that gets inserted at the cursor or saved as a draft.

- **Editor:** Press **Ctrl+Backslash** to open the macro picker.
- **Safari Fed:** Press **~** to run a macro against the current post (output saved as a draft).

See the full how-to guide: [docs/usage/macros.md](../usage/macros.md)
