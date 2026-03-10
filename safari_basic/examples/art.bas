10 REM -- ASCII Art Pattern --
20 FOR Y = 1 TO 10
30 DIM L$(80)
40 L$ = ""
50 FOR X = 1 TO 20
60 IF (X + Y) / 2 = INT((X + Y) / 2) THEN L$ = L$ + "* "
70 IF (X + Y) / 2 <> INT((X + Y) / 2) THEN L$ = L$ + "  "
80 NEXT X
90 PRINT L$
100 NEXT Y
110 END
