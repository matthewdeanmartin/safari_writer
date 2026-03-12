.TEXT
MAIN:
    LDA #"FIRST"
    PHA
    LDA #"SECOND"
    PHA

    PLA
    OUTLN A
    PLA
    OUTLN A
    HALT
