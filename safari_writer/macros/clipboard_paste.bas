10 REM Paste clipboard contents as a quoted block
20 IF LEN(CLIPBOARD$) = 0 THEN GOTO 60
30 PRINT "> "; CLIPBOARD$
40 GOTO 70
60 PRINT "(clipboard is empty)"
70 REM done
