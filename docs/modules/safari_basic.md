# Safari Basic

Safari Basic is a modern REPL and interpreter for a subset of the classic Atari BASIC.

## Features
- **Line-Oriented Editing**: Numbered program lines with classic insert/replace behavior.
- **Immediate Mode**: Execute statements directly from the prompt.
- **Numeric Precision**: Uses modern floating-point precision.
- **Mandatory DIM**: Strings and arrays must be explicitly dimensioned before use.

## Core Commands
- **LIST** — Display your program lines.
- **RUN** — Execute the current program.
- **NEW** — Delete the current program and reset state.
- **CONT** — Continue after a `STOP`.
- **CLR** — Clear variables without deleting the program.

## Sample Program
```basic
10 DIM NAME$(20)
20 PRINT "WHAT IS YOUR NAME?"
30 INPUT NAME$
40 IF NAME$="" THEN END
50 PRINT "HELLO, ";NAME$
60 GOTO 20
```
