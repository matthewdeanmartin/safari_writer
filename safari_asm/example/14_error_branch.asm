.TEXT
MAIN:
    OPEN IN, #"missing-file.txt", #"r"
    BERR FAIL

    OUTLN #"OPENED"
    HALT

FAIL:
    ERRMSG X
    ERRLN X
    HALT
