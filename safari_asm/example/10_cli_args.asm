.TEXT
MAIN:
    ARG X, #0
    BEQ USAGE
    ARG Y, #1
    BEQ USAGE

    LDA #"LEFT="
    CAT A, X
    CAT A, #" RIGHT="
    CAT A, Y
    OUTLN A
    HALT

USAGE:
    ERRLN #"USAGE: safari-asm 10_cli_args.asm -- <LEFT> <RIGHT>"
    HALT
