# Safari Extended Modules Help

This document covers additional modules in the Safari Suite: Safari ASM, Safari Basic, Safari Reader, Safari REPL, Safari Slides, and Safari View.

---

## Safari ASM

**Safari ASM** is an assembly-flavored Python interpreter. It allows you to write Python logic using a syntax inspired by low-level assembly languages (like 6502 or x86), but with the power of Python's standard library.

Run **safari-asm** from the command line to start the interpreter.

- [How do I run an ASM file?](#Running ASM Files)
- [What is the syntax like?](#ASM Syntax)
- [Can I use it with Safari Writer?](#ASM Integration)

---

## Running ASM Files

To run a Safari ASM program, pass the filename as an argument:
`safari-asm my_program.asm`

If no file is provided, it reads from **stdin**. You can pipe assembly code directly into it:
`cat logic.asm | safari-asm`

- [Tell me about syntax](#ASM Syntax)
- [Go back to Safari ASM](#Safari ASM)

---

## ASM Syntax

Safari ASM uses **mnemonic-style** commands that map to Python operations. While it looks like assembly, it is executing Python under the hood.

**Example:**
```asm
MOV R1, 10
ADD R1, 5
PRINT R1
```

Common mnemonics include `MOV`, `ADD`, `SUB`, `MUL`, `DIV`, `JMP`, and `CALL`.

- [How does it integrate?](#ASM Integration)
- [Go back to Safari ASM](#Safari ASM)

---

## ASM Integration

Safari ASM can be used to write high-performance macros or data processing scripts that interact with Safari Writer documents. You can use it to automate complex formatting tasks or perform batch transformations on `.sfw` files.

- [Go back to Safari ASM](#Safari ASM)

---

## Safari Base

**Safari Base** is a dBASE-style shell for managing structured data. It provides a terminal-based interface for interacting with SQLite databases using a simplified command set inspired by classic database management systems.

Run **safari-base** to start the shell.

- [How do I load a database?](#Loading Databases)
- [What can I do in Safari Base?](#Base Operations)

---

## Loading Databases

You can open an existing SQLite database by passing the path as an argument:
`safari-base my_data.db`

If no database is specified, Safari Base will start with an in-memory session.

- [Tell me about operations](#Base Operations)
- [Go back to Safari Base](#Safari Base)

---

## Base Operations

Safari Base allows you to perform standard database operations through its TUI:
1.  **Browse** records in a table.
2.  **Edit** field values.
3.  **Search** and filter data.
4.  **Export** tables to Safari Writer or CSV format.

- [Go back to Safari Base](#Safari Base)

---

## Safari Basic

**Safari Basic** is an embedded Atari BASIC macro interpreter. It is used primarily for extending the functionality of Safari Writer and Safari DOS through small, fast scripts.

Unlike Safari REPL, Safari Basic is designed to be **embedded** within other applications.

- [What is Safari REPL?](#Safari REPL)
- [How do I write Basic macros?](#Basic Macros)

---

## Basic Macros

Macros in Safari Basic use a subset of Atari BASIC. They are often used for:
1. Customizing the **Main Menu**.
2. Automating **Mail Merge** setups.
3. Defining custom **Global Format** templates.

- [Go back to Safari Basic](#Safari Basic)

---

## Safari REPL

**Safari REPL** is a standalone Atari BASIC interpreter providing an interactive shell. It is a "Ready" prompt environment where you can type BASIC code and execute it immediately.

Run **safari-repl** to start the interactive session.

- [How do I load a BAS file?](#Loading BASIC Files)
- [Can I edit BASIC files in Safari Writer?](#BASIC Handoff)

---

## Loading BASIC Files

You can load a `.BAS` file directly into the REPL by passing it as a command-line argument:
`safari-repl game.bas`

Inside the REPL, use the `LOAD` and `SAVE` commands to manage your programs.

- [Tell me about handoff](#BASIC Handoff)
- [Go back to Safari REPL](#Safari REPL)

---

## BASIC Handoff

Safari REPL supports **Writer Handoff**. If you want to edit your BASIC code in a full-featured word processor, you can request to open the current buffer in Safari Writer.

This allows you to use Safari Writer's search/replace and formatting tools on your source code.

- [Go back to Safari REPL](#Safari REPL)

---

## Safari Reader

**Safari Reader** is a keyboard-first terminal e-book reader. It is designed for focused reading of long-form text, Markdown files, and documentation.

Run **safari-reader** to open your library.

- [How do I navigate?](#Reader Navigation)
- [Can I export to Safari Writer?](#Reader Handoff)

---

## Reader Navigation

Safari Reader uses standard Safari Suite navigation keys:
- **Up / Down** — scroll line by line
- **Page Up / Page Down** — scroll page by page
- **Home / End** — jump to start or end of the book
- **/** — search for text within the current book

- [Tell me about export](#Reader Handoff)
- [Go back to Safari Reader](#Safari Reader)

---

## Reader Handoff

Like Safari Fed and Safari REPL, Safari Reader can **handoff** to Safari Writer. If you find a passage you want to quote or a section of documentation you want to edit, you can open it directly in the Safari Writer editor.

- [Go back to Safari Reader](#Safari Reader)

---

## Safari Slides

**Safari Slides** is a presentation tool for **SlideMD** decks. It turns simple Markdown files into professional, keyboard-driven terminal presentations.

Run `safari-slides deck.md` to start a presentation.

- [How do I control the slides?](#Slides Navigation)
- [What is SlideMD?](#SlideMD Format)

---

## Slides Navigation

- **Right Arrow / Space** — next slide
- **Left Arrow / Backspace** — previous slide
- **Home** — first slide
- **End** — last slide
- **Esc / Q** — exit presentation

- [Tell me about the format](#SlideMD Format)
- [Go back to Safari Slides](#Safari Slides)

---

## SlideMD Format

**SlideMD** is standard Markdown with `---` used to separate slides.

**Example:**
```markdown
# Slide 1
Welcome to my talk.
---
# Slide 2
Here are some points.
- Point A
- Point B
```

- [Go back to Safari Slides](#Safari Slides)

---

## Safari View

**Safari View** is a retro image and document viewer. It uses a custom **retro pipeline** to render images in various vintage styles, including Atari 2600, Atari 800, and Atari ST modes.

Run `safari-view open image.png` to view a file.

- [What are the render modes?](#View Render Modes)
- [How do I use the TUI?](#View TUI)
- [Can I use it from the command line?](#View CLI)

---

## View Render Modes

Safari View supports several **Render Modes** that emulate classic hardware:
- **2600** — ultra-low resolution, limited palette.
- **800** — classic 8-bit computer aesthetics.
- **ST** — 16-bit era graphics.
- **Native** — high-quality rendering with retro dithering.

- [Tell me about the TUI](#View TUI)
- [Tell me about the CLI](#View CLI)
- [Go back to Safari View](#Safari View)

---

## View TUI

The **TUI (Terminal User Interface)** mode includes a file browser and a live preview pane.
- **Space** — toggle browser visibility
- **Arrows** — navigate folders
- **Enter** — view the selected image
- **M** — cycle through render modes live

- [Tell me about the CLI](#View CLI)
- [Go back to Safari View](#Safari View)

---

## View CLI

You can use Safari View to **render** images directly to files from the command line without opening the TUI:
`safari-view render input.png --mode 800 -o output.png`

This is useful for batch processing images into a retro aesthetic.

- [Go back to Safari View](#Safari View)
---
