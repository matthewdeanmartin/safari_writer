10 REM Show document statistics at the cursor position
20 PRINT "=== Document Statistics ==="
30 PRINT "Lines:     "; STR$(DOCLINES)
40 PRINT "Cursor:    row "; STR$(CURSORROW); ", col "; STR$(CURSORCOL)
50 IF SELCOUNT > 0 THEN PRINT "Selection: "; STR$(SELCOUNT); " lines"
60 PRINT "==========================="
