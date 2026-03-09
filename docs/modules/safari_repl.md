# Safari REPL

Safari REPL is a small Atari BASIC environment built for quick experiments, loading `.BAS` files, and handing code back to Safari Writer when you want to edit it as text.

## Starting Safari REPL

Launch the standalone REPL directly:

```bash
safari-repl
```

Load a BASIC program on startup:

```bash
safari-repl demo.bas
```

You can also open it inside Safari Writer from the main menu or with:

```bash
safari-writer tui safari-repl --file demo.bas
```

## Main Menu

- **R** - Run the interactive REPL.
- **L** - Load a `.BAS` file.
- **H** - Open the help screen.
- **Q / Esc** - Return to the previous menu or quit.

## REPL Commands

Safari REPL supports the classic immediate-mode workflow:

- Enter a numbered line such as `10 PRINT "HELLO"` to store it.
- Enter an unnumbered line to run it immediately.
- `LIST` - Show the current stored program.
- `RUN` - Execute the stored program.
- `NEW` - Clear the program and variables.
- `CLR` - Clear variables while keeping the program.
- `CONT` - Continue after `STOP` when possible.

## REPL Screen Shortcuts

- **Esc** - Return to the Safari REPL menu.
- **F2** - Run `LIST`.
- **F5** - Run `RUN`.
- **F9** - Open the loaded `.BAS` file in Safari Writer.

## Writer Handoff

When a file is loaded, press **F9** from the REPL screen to open that BASIC source in Safari Writer's editor. This is useful when you want to edit the program as plain text, save it elsewhere, or use Safari Writer features on the source file.
