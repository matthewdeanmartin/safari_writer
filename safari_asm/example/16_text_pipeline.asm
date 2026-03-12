.DATA
RAW: .VAR

.TEXT
MAIN:
    INPUT RAW
    TEST RAW
    BEQ DONE

    LOADA RAW
    TRIM A
    UPPER A
    REPL A, A, #"CAT", #"DOG"
    LEN X, A

    OUT A
    OUT #" LEN="
    OUTLN X
    HALT

DONE:
    HALT
