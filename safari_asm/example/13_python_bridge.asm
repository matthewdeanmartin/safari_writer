.DATA
ITEMS: .LIST "pear", "apple", "banana"
NAME:  .VAR "matt"

.TEXT
MAIN:
    PYCALL X, #"len", NAME
    PYCALL Y, #"sorted", ITEMS

    JOIN A, Y, #","
    CAT A, #" LEN="
    CAT A, X
    OUTLN A
    HALT
