* demo_create.prg
* Illustrates table creation, insertion, and sorting.

? "Creating customers table..."
CREATE TABLE customers (id C 10, name C 30, balance N 10 2)

? "Inserting records using APPEND BLANK and REPLACE..."
APPEND BLANK
REPLACE id WITH "C001", name WITH "Alice Smith", balance WITH 1250.50

APPEND BLANK
REPLACE id WITH "C002", name WITH "Bob Jones", balance WITH 850.00

APPEND BLANK
REPLACE id WITH "C003", name WITH "Charlie Brown", balance WITH 2100.75

? ""
? "Listing original records:"
LIST ALL

? ""
? "Sorting by balance (INDEX ON balance)..."
INDEX ON balance TAG bal_idx

? "Listing sorted records:"
LIST ALL

? ""
? "Finding Charlie (SEEK)..."
SEEK 2100.75
IF FOUND()
    ? "Found: " + name + " with balance " + STR(balance)
ELSE
    ? "Charlie not found!"
ENDIF

? ""
? "Calculating summary stats:"
COUNT FOR balance > 1000 TO high_bal_count
SUM balance TO total_bal
AVERAGE balance TO avg_bal

? "Records > 1000: " + STR(high_bal_count)
? "Total Balance:  " + STR(total_bal)
? "Average Balance: " + STR(avg_bal)

CLOSE ALL
? ""
? "Demo completed."
