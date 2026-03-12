.DATA
I: .VAR

.TEXT
MAIN:
    LDA #1
    STA I

LOOP:
    LDA I
    CMP A, #5
    BGT DONE
    OUTLN A
    INC I
    JMP LOOP

DONE:
    HALT
