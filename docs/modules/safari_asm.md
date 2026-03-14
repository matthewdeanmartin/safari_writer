# Safari ASM

Safari ASM is an assembly-flavored interpreter for `.asm` source files. It runs text programs directly on a Python runtime and can be launched on its own or from other Safari tools.

## Starting Safari ASM

```bash
safari-asm demo.asm
type demo.asm | safari-asm
safari-asm demo.asm -- level1 level2
```

You can pass a file path or pipe source in through standard input. Any arguments after `--` are forwarded to the program.

## What it is for

- Running `.asm` programs from the command line.
- Launching `.asm` files from **Safari DOS**.
- Running the current `.asm` buffer from **Safari Writer** with **F5**.

## Input and output

- **Input file** — optional `.asm` file path.
- **Standard input** — used when no file is provided.
- **Program args** — forwarded after `--`.
- **Standard output / error** — used for program output and parse/runtime errors.

## Error handling

Safari ASM reports parse and runtime failures directly to standard error and exits with a non-zero status. Missing files are reported before execution starts.
