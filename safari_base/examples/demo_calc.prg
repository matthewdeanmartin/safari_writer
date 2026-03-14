* demo_calc.prg
* Illustrates control flow, loops, and calculations.

? "--- Safari Base Calculation Demo ---"
? ""

total = 0
count = 10

? "Counting up from 1 to 10 using FOR loop..."
FOR i = 1 TO count
    total = total + i
    ? "Current i: " + STR(i) + "  Running total: " + STR(total)
ENDFOR

? ""
? "Final sum: " + STR(total)
? ""

? "Using DO WHILE to find powers of 2..."
pow = 1
limit = 100
DO WHILE pow < limit
    ? "Power: " + STR(pow)
    pow = pow * 2
ENDDO

? ""
? "Demo of DO CASE statement:"
val = 42
DO CASE
    CASE val < 10
        ? "Value is small"
    CASE val < 50
        ? "Value is medium: " + STR(val)
    CASE val < 100
        ? "Value is large"
    OTHERWISE
        ? "Value is huge"
ENDCASE

? ""
? "Demo completed."
