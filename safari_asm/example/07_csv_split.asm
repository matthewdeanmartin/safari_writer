.TEXT
MAIN:
    INP A
    BEQ DONE

    SPLIT X, A, #","
    GET Y, X, #0
    GET A, X, #1

    OUT #"LEFT="
    OUT Y
    OUT #" RIGHT="
    OUTLN A
    HALT

DONE:
    HALT
