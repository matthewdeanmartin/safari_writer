# Safari ASM Specification

## 1. Purpose

Safari ASM is a retro-styled programming language with the look and feel of 6502-era Atari assembler, but designed for practical modern scripting on top of a Python runtime.

Safari ASM is intended for:

- terminal applications
- stdin/stdout tools
- file and text processing
- simple automation
- educational and nostalgic programming
- playful “assembler-feeling” development without true hardware limits

Safari ASM is not a CPU emulator, not a real assembler, and not constrained by the numeric, memory, or device limits of vintage hardware.

Its aesthetic goals are:

- mnemonic-heavy source code
- labels
- semicolon comments
- directives
- registers
- branch-oriented control flow
- source that looks like assembly language
- output and examples that preserve the same retro feel

Its usability goals are:

- easier writing over strict authenticity

- first-class strings and text handling

- strong stdin/stdout support

- symbolic variables instead of raw memory addresses

- multiple mnemonics for the same operation:

  - one traditional
  - one friendly / longer form

Safari ASM is expected to be interpreted, though an implementation may also transpile to Python internally.

______________________________________________________________________

## 2. Design Principles

### 2.1 Retro surface, modern behavior

Safari ASM should look like an assembler, but act like a practical scripting language.

Example:

```asm
START:              ; label marking the entry point
    LDA #"HELLO"    ; LDA = load accumulator A with immediate string
    OUTLN A         ; OUTLN = print A followed by newline
    HALT            ; HALT = stop program execution
```

### 2.2 Easier writing wins

When there is a choice between strict assembler realism and easier authoring, Safari ASM chooses the easier authoring model.

Examples of this principle:

- registers may hold strings, integers, booleans, lists, maps, or other runtime values
- variables are symbolic by name
- branch instructions may work on modern comparison results
- string handling is built in
- aliases are supported for user friendliness

### 2.3 Terminal-first language

Safari ASM favors:

- reading from stdin
- writing to stdout and stderr
- line-oriented processing
- command-line arguments
- text files
- practical console tools

### 2.4 Python runtime

Safari ASM runs on a Python implementation. The runtime may internally represent values as Python values.

Safari ASM also provides `PYCALL` for invoking Python callables. Compatibility of return values is implementation-defined and may be handwaved where reasonable.

______________________________________________________________________

## 3. Lexical Structure

## 3.1 Case

Safari ASM source is case-insensitive for mnemonics, directives, and labels, but implementations may preserve original case for display.

These are equivalent:

```asm
LDA #"HELLO"        ; uppercase mnemonic
lda #"HELLO"        ; lowercase mnemonic
LdA #"HELLO"        ; mixed case mnemonic
```

String values preserve their own case.

## 3.2 Comments

Comments begin with a semicolon `;` and continue to the end of the line.

Examples:

```asm
JMP LOOP            ; JMP = jump unconditionally to label LOOP
LDA #42             ; load A with immediate integer 42
OUTLN A             ; print register A with trailing newline
```

## 3.3 Labels

A label marks a position in code and ends with a colon.

Example:

```asm
LOOP:               ; label named LOOP
    JMP LOOP        ; jump back to LOOP
```

## 3.4 Whitespace

Whitespace separates tokens. Extra spaces are allowed for readability.

Example:

```asm
LDA    #"HELLO"     ; extra spaces are allowed
OUTLN  A            ; aligned style is encouraged
```

## 3.5 Strings

String literals are written in double quotes. Immediate string literals are written with `#`.

Example:

```asm
LDA #"HELLO"        ; immediate string literal
STA NAME            ; store A into variable NAME
```

## 3.6 Numbers

Numeric literals may be written as decimal integers or implementation-supported numeric forms.

Example:

```asm
LDA #10             ; immediate integer 10
ADD #5              ; add 5 to A
```

Safari ASM is not restricted to 8-bit numeric ranges.

______________________________________________________________________

## 4. Program Structure

A Safari ASM source file consists of:

- optional directives
- zero or more variable / constant declarations
- one or more labels and instructions

Typical structure:

```asm
.DATA                   ; begin data-oriented declarations
NAME:   .VAR            ; declare variable NAME
COUNT:  .VAR            ; declare variable COUNT
PROMPT: .CONST "NAME? " ; declare constant PROMPT

.TEXT                   ; begin executable text section
MAIN:                   ; label MAIN
    LDA PROMPT          ; load constant PROMPT into A
    OUT A               ; print A with no newline
    INP A               ; read a line from stdin into A
    STA NAME            ; store A into NAME
    HALT                ; stop execution
```

Sections are mostly stylistic and organizational rather than true memory segments.

______________________________________________________________________

## 5. Values and Data Model

Safari ASM supports modern dynamic values.

A register, variable, or Python bridge call may hold:

- integer
- floating point number
- string
- boolean
- list
- map / dictionary
- null-like value
- implementation-defined runtime object

Safari ASM does not require the programmer to manually manage bytes, addresses, or real hardware memory.

Example:

```asm
LDA #"APPLE"        ; A holds a string
LDX #3              ; X holds an integer
LDY #TRUE           ; Y holds a boolean
```

______________________________________________________________________

## 6. Registers

Safari ASM defines the following primary registers:

- `A` — accumulator, preferred default working register
- `X` — index / auxiliary register
- `Y` — index / auxiliary register

These registers are general-purpose and may hold any runtime value.

Example:

```asm
LDA #"HELLO"        ; load string into A
TAX                 ; copy A into X
OUTLN X             ; print X
```

### 6.1 Register transfer examples

```asm
LDA #"HELLO"        ; load A with string HELLO
TAX                 ; TAX = transfer A to X
TXA                 ; TXA = transfer X to A
TAY                 ; TAY = transfer A to Y
TYA                 ; TYA = transfer Y to A
```

______________________________________________________________________

## 7. Flags and Conditions

Safari ASM maintains logical condition state for branching.

An implementation should support at least the following branch-relevant states:

- equality / inequality result
- ordering comparisons where meaningful
- truthy / falsy or empty / non-empty tests
- error state for operations that can fail

The exact internal flag model need not match real 6502 semantics.

Example:

```asm
CMP A, #"YES"       ; compare A with string YES
BEQ OK              ; BEQ = branch if equal to label OK
BNE NOPE            ; BNE = branch if not equal to label NOPE
```

______________________________________________________________________

## 8. Addressing Style

Safari ASM preserves assembler-like addressing style in appearance, but with modern semantics.

## 8.1 Immediate values

Immediate values use `#`.

```asm
LDA #42             ; immediate integer 42
LDA #"HELLO"        ; immediate string HELLO
LDA #TRUE           ; immediate boolean TRUE
```

## 8.2 Symbolic variables

Variables are referenced by name.

```asm
LDA NAME            ; load variable NAME into A
STA RESULT          ; store A into RESULT
```

## 8.3 Indexed access

Indexed syntax may be used for sequence access.

```asm
LDA ITEMS,X         ; load ITEMS at index X into A
STA ROW,Y           ; store A into ROW at index Y
```

This is a modern indexed collection operation, not raw memory indexing.

______________________________________________________________________

## 9. Multiple Mnemonics

Safari ASM supports two mnemonic styles for many instructions:

- a traditional short form
- a friendly longer form

Both forms are equivalent.

Example:

```asm
LDA #"HELLO"        ; traditional short mnemonic
LOADA #"HELLO"      ; friendly longer mnemonic, same meaning
```

Implementations should accept both forms. Documentation may show both.

### 9.1 Examples of mnemonic pairs

| Traditional | Friendly | Meaning |
| ----------- | ---------- | ------------------------------- |
| `LDA` | `LOADA` | load value into A |
| `LDX` | `LOADX` | load value into X |
| `LDY` | `LOADY` | load value into Y |
| `STA` | `STOREA` | store A into destination |
| `STX` | `STOREX` | store X into destination |
| `STY` | `STOREY` | store Y into destination |
| `JMP` | `JUMP` | unconditional jump |
| `JSR` | `CALL` | call subroutine |
| `RTS` | `RETURN` | return from subroutine |
| `CMP` | `COMPARE` | compare values |
| `OUT` | `PRINT` | output without newline |
| `OUTLN` | `PRINTLN` | output with newline |
| `INP` | `INPUT` | read line from stdin |
| `ERR` | `EPRINT` | write to stderr without newline |
| `ERRLN` | `EPRINTLN` | write to stderr with newline |
| `HALT` | `STOP` | stop program |
| `BRA` | `BRANCH` | unconditional branch |
| `MOV` | `MOVE` | move one value to another |
| `CAT` | `CONCAT` | concatenate values |

Example:

```asm
PRINT #"HELLO"      ; friendly mnemonic, print without newline
OUTLN #" WORLD"     ; traditional mnemonic, print with newline
```

______________________________________________________________________

## 10. Directives

Safari ASM supports directives for structure, declarations, constants, and readability.

Directives begin with a period.

## 10.1 Core directives

### `.DATA`

Marks the data declaration section.

```asm
.DATA               ; begin data section
NAME: .VAR          ; declare variable NAME
```

### `.TEXT`

Marks the executable code section.

```asm
.TEXT               ; begin code section
MAIN:               ; main entry label
    HALT            ; stop execution
```

### `.VAR`

Declares a symbolic variable.

```asm
COUNT: .VAR         ; declare variable COUNT
```

### `.CONST`

Declares a symbolic constant.

```asm
PROMPT: .CONST "ENTER NAME: " ; declare constant PROMPT
```

### `.LIST`

Declares a list literal or list-valued symbol.

```asm
COLORS: .LIST "RED", "GREEN", "BLUE" ; declare list COLORS
```

### `.MAP`

Declares a map / dictionary value.

```asm
SETTINGS: .MAP "MODE", "FAST", "DEBUG", TRUE ; declare map-like data
```

### `.BYTE`

Provides retro-styled byte-oriented declaration syntax for aesthetics. Implementations may interpret it as numeric data, string code units, or simply a declaration convenience.

```asm
MASK: .BYTE 1, 2, 3 ; retro-style numeric declaration
```

### `.WORD`

Provides retro-styled word-oriented declaration syntax.

```asm
TABLE: .WORD 100, 200, 300 ; retro-style word declaration
```

### `.PROC` and `.ENDPROC`

Mark a subroutine region for readability.

```asm
GREET: .PROC        ; begin procedure GREET
    OUTLN #"HI"     ; print HI
    RTS             ; return
.ENDPROC            ; end procedure
```

### `.ENTRY`

Optionally declares the entry label.

```asm
.ENTRY MAIN         ; set MAIN as entry point
```

If `.ENTRY` is omitted, the implementation may use the first executable label.

______________________________________________________________________

## 11. Variables and Constants

Variables are symbolic names. Constants are immutable symbolic names.

Example:

```asm
.DATA
NAME:   .VAR                    ; NAME is a mutable variable
PROMPT: .CONST "WHAT IS NAME? " ; PROMPT is a constant string
```

Use `STA` or `STOREA` to save from `A` into a variable.

Example:

```asm
LDA #"MATT"         ; load immediate string MATT into A
STA NAME            ; store A into variable NAME
```

______________________________________________________________________

## 12. Instruction Set

## 12.1 Load and store instructions

### `LDA` / `LOADA`

Load a value into register `A`.

```asm
LDA #42             ; load immediate integer 42 into A
LOADA NAME          ; load variable NAME into A
```

### `LDX` / `LOADX`

Load a value into register `X`.

```asm
LDX #0              ; load immediate integer 0 into X
LOADX COUNT         ; load variable COUNT into X
```

### `LDY` / `LOADY`

Load a value into register `Y`.

```asm
LDY #"DONE"         ; load immediate string DONE into Y
LOADY STATUS        ; load variable STATUS into Y
```

### `STA` / `STOREA`

Store `A` into a destination.

```asm
STA NAME            ; store A into variable NAME
STOREA RESULT       ; friendly form, store A into RESULT
```

### `STX` / `STOREX`

Store `X` into a destination.

```asm
STX INDEX           ; store X into variable INDEX
```

### `STY` / `STOREY`

Store `Y` into a destination.

```asm
STY FLAG            ; store Y into variable FLAG
```

### `MOV` / `MOVE`

Move a value from source to destination without privileging `A`.

```asm
MOV NAME, A         ; move A into NAME
MOVE RESULT, X      ; move X into RESULT
```

Implementations may define exact source/destination operand ordering, but should document it clearly. The preferred ordering is:

`MOV destination, source`

because it is easier for most people to write and read.

______________________________________________________________________

## 12.2 Register transfer instructions

### `TAX`

Transfer `A` to `X`.

```asm
TAX                 ; copy A into X
```

### `TAY`

Transfer `A` to `Y`.

```asm
TAY                 ; copy A into Y
```

### `TXA`

Transfer `X` to `A`.

```asm
TXA                 ; copy X into A
```

### `TYA`

Transfer `Y` to `A`.

```asm
TYA                 ; copy Y into A
```

______________________________________________________________________

## 12.3 Arithmetic instructions

Arithmetic operates on `A` by default unless otherwise specified.

### `ADD`

Add value to `A`.

```asm
LDA #10             ; load 10 into A
ADD #5              ; add 5 to A, result A = 15
```

### `SUB`

Subtract value from `A`.

```asm
LDA #10             ; load 10 into A
SUB #3              ; subtract 3 from A, result A = 7
```

### `MUL`

Multiply `A` by value.

```asm
LDA #6              ; load 6 into A
MUL #7              ; multiply A by 7, result A = 42
```

### `DIV`

Divide `A` by value.

```asm
LDA #20             ; load 20 into A
DIV #4              ; divide A by 4, result A = 5
```

### `MOD`

Remainder of `A` divided by value.

```asm
LDA #20             ; load 20 into A
MOD #6              ; remainder of 20 / 6, result A = 2
```

### `INC`

Increment value by 1.

Preferred easier form:

```asm
INC A               ; increment A by 1
INC COUNT           ; increment variable COUNT by 1
```

Friendly synonym may be supported as `INCREMENT`.

### `DEC`

Decrement value by 1.

```asm
DEC A               ; decrement A by 1
DEC COUNT           ; decrement variable COUNT by 1
```

Friendly synonym may be supported as `DECREMENT`.

______________________________________________________________________

## 12.4 Comparison and testing instructions

### `CMP` / `COMPARE`

Compare two values and update condition state.

```asm
CMP A, #"YES"       ; compare A with immediate string YES
COMPARE COUNT, #10  ; friendly form, compare COUNT with 10
```

### `TEST`

Test a value for emptiness / falsiness.

```asm
TEST A              ; test A for empty / false / zero-like value
BEQ EMPTY           ; branch if tested value was empty / false
```

This instruction is preferred for text-oriented programs.

### `TYPE`

Optionally obtain or test runtime type.

```asm
TYPE A              ; inspect the type of A, implementation-defined result
```

______________________________________________________________________

## 12.5 Branch and jump instructions

### `JMP` / `JUMP`

Unconditional jump to label.

```asm
JMP LOOP            ; jump unconditionally to LOOP
JUMP START          ; friendly form, jump to START
```

### `BRA` / `BRANCH`

Unconditional branch to nearby or ordinary label. In Safari ASM, `BRA` may simply be an alias of `JMP`.

```asm
BRA RETRY           ; branch unconditionally to RETRY
BRANCH DONE         ; friendly form, branch to DONE
```

### `BEQ`

Branch if equal or if last test indicated emptiness / truthy-equal success.

```asm
CMP A, #"YES"       ; compare A to YES
BEQ OK              ; branch to OK if equal
```

### `BNE`

Branch if not equal.

```asm
CMP A, #"YES"       ; compare A to YES
BNE NOPE            ; branch to NOPE if not equal
```

### `BGT`

Branch if greater than.

```asm
CMP COUNT, #10      ; compare COUNT to 10
BGT BIG             ; branch if COUNT > 10
```

### `BLT`

Branch if less than.

```asm
CMP COUNT, #10      ; compare COUNT to 10
BLT SMALL           ; branch if COUNT < 10
```

### `BGE`

Branch if greater than or equal.

```asm
CMP COUNT, #10      ; compare COUNT to 10
BGE OK              ; branch if COUNT >= 10
```

### `BLE`

Branch if less than or equal.

```asm
CMP COUNT, #10      ; compare COUNT to 10
BLE OK              ; branch if COUNT <= 10
```

### `BERR`

Branch if the previous operation produced an error condition.

```asm
OPEN FH, #"missing.txt", #"r" ; open file for reading
BERR OPENFAIL                 ; branch if open failed
```

______________________________________________________________________

## 12.6 Call and return instructions

### `JSR` / `CALL`

Call a subroutine.

```asm
JSR GREET           ; JSR = jump to subroutine GREET
CALL GREET          ; friendly form, call subroutine GREET
```

### `RTS` / `RETURN`

Return from a subroutine.

```asm
RTS                 ; RTS = return from subroutine
RETURN              ; friendly form, return from subroutine
```

Safari ASM subroutines commonly pass inputs via registers or symbolic variables. Return values commonly come back in `A`.

Example:

```asm
MAIN:
    LDA #"MATT"         ; load string MATT into A as argument
    JSR GREET           ; call GREET
    HALT                ; stop program

GREET:
    STA NAME            ; store incoming A into NAME
    LDA #"HELLO, "      ; load greeting prefix into A
    CAT A, NAME         ; concatenate NAME onto A
    OUTLN A             ; print completed greeting
    RTS                 ; return

.DATA
NAME: .VAR              ; variable NAME
```

______________________________________________________________________

## 12.7 Stack instructions

Safari ASM may provide a symbolic stack for retro flavor and practical control flow.

### `PHA`

Push `A` onto stack.

```asm
PHA                 ; push A onto stack
```

### `PLA`

Pop top of stack into `A`.

```asm
PLA                 ; pop top of stack into A
```

### `PHX`

Push `X` onto stack.

```asm
PHX                 ; push X onto stack
```

### `PLX`

Pop top of stack into `X`.

```asm
PLX                 ; pop top of stack into X
```

### `PHY`

Push `Y` onto stack.

```asm
PHY                 ; push Y onto stack
```

### `PLY`

Pop top of stack into `Y`.

```asm
PLY                 ; pop top of stack into Y
```

### `PUSH`

Push arbitrary value or named value to stack or list, implementation-defined by operand pattern. For simplicity, implementations should prefer stack usage when the first operand is omitted.

```asm
PUSH A              ; push A onto stack
```

### `POP`

Pop a value into a register or destination.

```asm
POP A               ; pop top of stack into A
```

______________________________________________________________________

## 12.8 Text and collection instructions

### `CAT` / `CONCAT`

Concatenate source value onto destination value. Preferred easier form:

`CAT destination, source`

```asm
LDA #"HELLO, "      ; load HELLO, into A
CAT A, #"MATT"      ; concatenate MATT onto A
OUTLN A             ; print HELLO, MATT
```

Friendly form:

```asm
CONCAT A, NAME      ; concatenate NAME onto A
```

Implementations should auto-stringify values when reasonable.

### `LEN`

Get length of a value.

Preferred easier form: put result into `A` if only one operand is supplied.

```asm
LEN NAME            ; length of NAME goes into A
OUTLN A             ; print the length
```

Optional explicit two-operand form:

```asm
LEN X, NAME         ; length of NAME goes into X
```

### `TRIM`

Trim leading and trailing whitespace.

```asm
TRIM A              ; trim whitespace from A
```

### `UPPER`

Convert to uppercase.

```asm
UPPER A             ; uppercase string in A
```

### `LOWER`

Convert to lowercase.

```asm
LOWER A             ; lowercase string in A
```

### `SPLIT`

Split a string into a list.

Preferred easier form:

`SPLIT destination, source, delimiter`

```asm
SPLIT X, A, #","    ; split A on commas, store list in X
```

### `JOIN`

Join a list into a string.

```asm
JOIN A, X, #"|"     ; join list X using | and store result in A
```

### `GET`

Get an item from a list or map.

```asm
GET A, ITEMS, #0    ; get index 0 from ITEMS into A
GET X, SETTINGS, #"MODE" ; get key MODE from SETTINGS into X
```

### `PUT`

Set an item in a list or map.

```asm
PUT SETTINGS, #"MODE", #"FAST" ; put MODE=FAST into SETTINGS
```

### `MATCH`

Pattern or regex-style match. Exact pattern semantics are implementation-defined.

```asm
MATCH X, A, #"ERROR" ; test whether A matches or contains ERROR, result in X
```

### `REPL`

Replace text in a string.

```asm
REPL A, A, #"CAT", #"DOG" ; replace CAT with DOG in A
```

______________________________________________________________________

## 12.9 Input and output instructions

### `INP` / `INPUT`

Read one line from stdin.

Preferred easier forms:

```asm
INP A               ; read one line into A
INPUT NAME          ; friendly form, read one line into NAME
```

On EOF, the implementation should update condition state so EOF-sensitive loops are easy to write.

### `OUT` / `PRINT`

Write value to stdout without newline.

```asm
OUT #"NAME? "       ; print prompt with no newline
PRINT A             ; friendly form, print A with no newline
```

### `OUTLN` / `PRINTLN`

Write value to stdout with newline.

```asm
OUTLN #"DONE"       ; print DONE with newline
PRINTLN A           ; friendly form, print A with newline
```

### `ERR` / `EPRINT`

Write value to stderr without newline.

```asm
ERR #"ERROR: "      ; write ERROR: to stderr with no newline
```

### `ERRLN` / `EPRINTLN`

Write value to stderr with newline.

```asm
ERRLN #"BAD INPUT"  ; write BAD INPUT to stderr with newline
```

______________________________________________________________________

## 12.10 File instructions

### `OPEN`

Open a file.

Preferred operand ordering:

`OPEN handle, path, mode`

```asm
OPEN FH, #"notes.txt", #"r" ; open notes.txt for reading as handle FH
BERR FAIL                   ; branch if open failed
```

### `READLN`

Read one line from file handle.

```asm
READLN A, FH         ; read one line from FH into A
BEQ DONE             ; branch if EOF or empty-as-EOF condition
```

### `WRITELN`

Write line to file handle.

```asm
WRITELN FH, A        ; write A plus newline to file handle FH
```

### `CLOSE`

Close a file handle.

```asm
CLOSE FH             ; close file handle FH
```

______________________________________________________________________

## 12.11 Runtime and utility instructions

### `ARGV`

Load all command-line arguments or argument list.

```asm
ARGV A               ; load all command-line arguments into A
```

### `ARG`

Load a specific command-line argument by index.

```asm
ARG A, #0            ; load first command-line argument into A
```

### `ENV`

Read an environment variable.

```asm
ENV A, #"HOME"       ; load environment variable HOME into A
```

### `NOP`

Do nothing.

```asm
NOP                  ; no operation
```

### `HALT` / `STOP`

Stop program execution.

```asm
HALT                 ; stop execution immediately
STOP                 ; friendly form, stop execution
```

______________________________________________________________________

## 12.12 Python bridge instruction

### `PYCALL`

Invoke a Python callable from Safari ASM.

Safari ASM includes `PYCALL` as an escape hatch into Python functionality.

The implementation may support one or more of these forms:

- `PYCALL destination, callable_name`
- `PYCALL destination, callable_name, arg1, arg2, ...`
- `PYCALL A, #"module:function", X, Y`

The exact callable-resolution rules are implementation-defined.

Return values are accepted if they are compatible with the Safari ASM runtime. If compatibility is unclear, the implementation may handwave, wrap, stringify, or otherwise adapt the result.

Example:

```asm
PYCALL A, #"len", NAME        ; call Python len(NAME), store result in A
OUTLN A                       ; print returned length
```

Example:

```asm
PYCALL A, #"math:sqrt", #144  ; call Python math.sqrt(144), store result in A
OUTLN A                       ; print the result
```

Example:

```asm
PYCALL X, #"sorted", ITEMS    ; call Python sorted(ITEMS), store result in X
```

If the call fails, the implementation should set error state so `BERR` may be used.

```asm
PYCALL A, #"missing:thing"    ; attempt Python callable
BERR PYFAIL                   ; branch if Python call failed
```

______________________________________________________________________

## 13. Output Aesthetics

Safari ASM source and examples should preserve retro aesthetics:

- uppercase-friendly style
- labels at left margin
- aligned operands where practical
- semicolon comments explaining instructions
- compact vertical rhythm
- mnemonic-heavy feel

Preferred style:

```asm
MAIN:
    LDA #"HELLO"      ; load HELLO into A
    OUTLN A           ; print A with newline
    HALT              ; stop execution
```

Friendly-mnemonic style is also valid, but examples should still preserve the same visual feel:

```asm
MAIN:
    LOADA #"HELLO"    ; friendly form: load HELLO into A
    PRINTLN A         ; friendly form: print A with newline
    STOP              ; friendly form: stop execution
```

______________________________________________________________________

## 14. Errors

Operations that fail should set an error condition visible to control flow.

Example operations that may fail:

- `OPEN`
- `READLN`
- `WRITELN`
- `PYCALL`
- collection access
- conversions

Preferred branch:

```asm
OPEN FH, #"missing.txt", #"r" ; attempt to open missing file
BERR FAIL                     ; branch if previous operation failed
```

Optional error message retrieval may be supported through a helper instruction or runtime variable.

Example, implementation-defined:

```asm
ERRMSG A            ; load most recent error message into A
ERRLN A             ; print error message to stderr
```

______________________________________________________________________

## 15. Recommended Calling Convention

Safari ASM recommends the following simple convention:

- input arguments may be passed in `A`, `X`, `Y`, or named variables
- return value should be placed in `A`
- subroutines may preserve or clobber registers unless documented otherwise
- stack usage is allowed when helpful

Example:

```asm
MAIN:
    LDA #"MATT"          ; place argument in A
    JSR MAKEGREETING     ; call subroutine
    OUTLN A              ; print returned greeting from A
    HALT                 ; stop execution

MAKEGREETING:
    STA NAME             ; save input argument from A
    LDA #"HELLO, "       ; load greeting prefix
    CAT A, NAME          ; append name
    CAT A, #"!"          ; append exclamation point
    RTS                  ; return with result in A

.DATA
NAME: .VAR               ; scratch variable NAME
```

______________________________________________________________________

## 16. Example Programs

## 16.1 Hello World

### Traditional style

```asm
.TEXT
MAIN:
    LDA #"HELLO, WORLD!" ; load HELLO, WORLD! into A
    OUTLN A              ; print A with newline
    HALT                 ; stop execution
```

### Friendly style

```asm
.TEXT
MAIN:
    LOADA #"HELLO, WORLD!" ; friendly form: load string into A
    PRINTLN A              ; friendly form: print A with newline
    STOP                   ; friendly form: stop execution
```

______________________________________________________________________

## 16.2 Prompt for a name

```asm
.DATA
NAME:   .VAR                        ; declare mutable variable NAME
PROMPT: .CONST "ENTER YOUR NAME: "  ; declare constant PROMPT

.TEXT
MAIN:
    LDA PROMPT          ; load PROMPT into A
    OUT A               ; print prompt without newline
    INP A               ; read one line from stdin into A
    TRIM A              ; trim surrounding whitespace from A
    STA NAME            ; store trimmed name into NAME

    LDA #"HELLO, "      ; load greeting prefix into A
    CAT A, NAME         ; append NAME to A
    CAT A, #"!"         ; append exclamation mark to A
    OUTLN A             ; print greeting with newline
    HALT                ; stop execution
```

______________________________________________________________________

## 16.3 Echo stdin until EOF

```asm
.TEXT
MAIN:
LOOP:
    INP A               ; read one line from stdin into A
    BEQ DONE            ; if EOF or empty termination condition, branch to DONE
    OUTLN A             ; print A with newline
    JMP LOOP            ; jump back to LOOP
DONE:
    HALT                ; stop execution
```

______________________________________________________________________

## 16.4 Count lines from stdin

```asm
.DATA
COUNT: .VAR            ; declare mutable variable COUNT

.TEXT
MAIN:
    LDA #0             ; load 0 into A
    STA COUNT          ; initialize COUNT to 0

READ:
    INP A              ; read one line from stdin into A
    BEQ REPORT         ; if EOF or termination condition, branch to REPORT
    INC COUNT          ; increment variable COUNT by 1
    JMP READ           ; jump back to READ

REPORT:
    LDA #"LINES: "     ; load prefix LINES: into A
    CAT A, COUNT       ; append COUNT onto A
    OUTLN A            ; print result
    HALT               ; stop execution
```

______________________________________________________________________

## 16.5 Numeric loop

```asm
.DATA
I: .VAR               ; declare variable I

.TEXT
MAIN:
    LDA #1            ; load 1 into A
    STA I             ; store 1 into I

LOOP:
    LDA I             ; load I into A
    CMP A, #10        ; compare A with 10
    BGT DONE          ; if A > 10, branch to DONE

    OUTLN A           ; print current value of A
    INC I             ; increment I
    JMP LOOP          ; repeat loop

DONE:
    HALT              ; stop execution
```

______________________________________________________________________

## 16.6 File copy

```asm
.DATA
SRC: .VAR             ; source path variable
DST: .VAR             ; destination path variable

.TEXT
MAIN:
    ARG A, #0         ; load first command-line argument into A
    BEQ USAGE         ; if missing, branch to USAGE
    STA SRC           ; store source path into SRC

    ARG A, #1         ; load second command-line argument into A
    BEQ USAGE         ; if missing, branch to USAGE
    STA DST           ; store destination path into DST

    OPEN IN, SRC, #"r" ; open source file for reading as handle IN
    BERR FAILSRC       ; if open failed, branch to FAILSRC

    OPEN OUT, DST, #"w" ; open destination file for writing as handle OUT
    BERR FAILDST        ; if open failed, branch to FAILDST

COPYLOOP:
    READLN A, IN      ; read one line from IN into A
    BEQ DONE          ; if EOF, branch to DONE
    WRITELN OUT, A    ; write A plus newline to OUT
    JMP COPYLOOP      ; continue copying

DONE:
    CLOSE IN          ; close input handle
    CLOSE OUT         ; close output handle
    HALT              ; stop execution

FAILSRC:
    ERRLN #"CANNOT OPEN SOURCE FILE" ; print source-file error
    HALT                            ; stop execution

FAILDST:
    ERRLN #"CANNOT OPEN DESTINATION FILE" ; print destination-file error
    CLOSE IN                              ; close input if already open
    HALT                                  ; stop execution

USAGE:
    ERRLN #"USAGE: COPY <SRC> <DST>" ; print usage message
    HALT                             ; stop execution
```

______________________________________________________________________

## 16.7 Split CSV-like input

```asm
.TEXT
MAIN:
READ:
    INP A                ; read one line from stdin into A
    BEQ DONE             ; if EOF or termination condition, branch to DONE

    SPLIT X, A, #","     ; split A on commas and store list in X
    GET Y, X, #0         ; get first field from X into Y
    GET A, X, #1         ; get second field from X into A

    OUT #"LEFT="         ; print literal LEFT=
    OUT Y                ; print first field
    OUT #" RIGHT="       ; print literal RIGHT=
    OUTLN A              ; print second field and newline

    JMP READ             ; repeat

DONE:
    HALT                 ; stop execution
```

______________________________________________________________________

## 16.8 PYCALL example with Python `len`

```asm
.DATA
NAME: .VAR              ; declare variable NAME

.TEXT
MAIN:
    OUT #"NAME? "       ; print prompt with no newline
    INP A               ; read one line into A
    TRIM A              ; trim whitespace from A
    STA NAME            ; store name into NAME

    PYCALL X, #"len", NAME ; call Python len(NAME), store result in X

    LDA #"LENGTH="         ; load prefix LENGTH= into A
    CAT A, X               ; append returned Python result
    OUTLN A                ; print final message
    HALT                   ; stop execution
```

______________________________________________________________________

## 16.9 PYCALL example with Python module function

```asm
.TEXT
MAIN:
    PYCALL A, #"math:sqrt", #144 ; call Python math.sqrt(144), store result in A
    BERR FAIL                    ; if Python call failed, branch to FAIL
    OUTLN A                      ; print result in A
    HALT                         ; stop execution

FAIL:
    ERRLN #"PYCALL FAILED"       ; print Python call failure message
    HALT                         ; stop execution
```

______________________________________________________________________

## 16.10 Friendly-style example

```asm
.DATA
NAME: .VAR                      ; declare variable NAME

.TEXT
MAIN:
    PRINT #"WHAT IS YOUR NAME? " ; friendly form: print prompt
    INPUT NAME                   ; friendly form: read line into NAME
    TRIM NAME                    ; trim whitespace from NAME
    TEST NAME                    ; test whether NAME is empty
    BEQ NONAME                   ; if empty, branch to NONAME

    LOADA #"HELLO, "             ; friendly form: load greeting prefix
    CONCAT A, NAME               ; append NAME to A
    CONCAT A, #"!"               ; append exclamation point
    PRINTLN A                    ; print greeting with newline
    STOP                         ; stop execution

NONAME:
    EPRINTLN #"NO NAME ENTERED"  ; print error message to stderr
    STOP                         ; stop execution
```

______________________________________________________________________

## 17. Implementation Guidance

An implementation of Safari ASM should prefer:

- forgiving parsing
- line-oriented execution model
- clear runtime errors
- branchable error state
- dynamic values
- simple calling conventions
- modern text/file semantics
- nostalgic output formatting in examples and diagnostics where possible

An implementation may:

- interpret directly
- transpile to Python AST or Python source
- internally normalize friendly mnemonics into traditional mnemonics
- internally represent labels, variables, and registers as Python objects

An implementation should not require:

- real machine code generation
- true memory addresses
- cycle accuracy
- hardware registers
- 8-bit overflow behavior unless in an optional compatibility mode

______________________________________________________________________

## 18. Summary

Safari ASM is a retro assembly-flavored scripting language with:

- Atari/6502-inspired source aesthetics
- symbolic variables
- registers `A`, `X`, `Y`
- directives such as `.DATA`, `.TEXT`, `.VAR`, `.CONST`
- multiple mnemonic styles
- terminal-first design
- file and text handling
- Python escape hatch via `PYCALL`
- easier modern semantics chosen over strict historical fidelity

Minimal example:

```asm
.TEXT
MAIN:
    LDA #"HELLO FROM SAFARI ASM" ; load greeting into A
    OUTLN A                      ; print A with newline
    HALT                         ; stop execution
```

If you want, I can turn this next into a **formal grammar plus opcode table**, or into an **implementation plan for a Python interpreter for Safari ASM**.
