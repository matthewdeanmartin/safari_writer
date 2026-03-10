"""Exercise script for program-mode execution with control flow.

Tests: IF/ELSE, DO WHILE, FOR, SCAN, DO CASE, program files, and
multi-line scripts via run_source().
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from safari_base.lang import Environment, Interpreter


def main() -> int:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        env = Environment(work_dir=tmpdir, default_dir=tmpdir, unsafe=True)
        interp = Interpreter(env)

        # -- Setup: create a table with data ---------------------------------
        setup = """\
CREATE TABLE products (name C(20), price N(10,2), qty N(6,0), active L)
APPEND BLANK
REPLACE name WITH "Widget", price WITH 9.99, qty WITH 100, active WITH .T.
APPEND BLANK
REPLACE name WITH "Gadget", price WITH 24.50, qty WITH 50, active WITH .T.
APPEND BLANK
REPLACE name WITH "Doohick", price WITH 3.25, qty WITH 200, active WITH .F.
APPEND BLANK
REPLACE name WITH "Thingam", price WITH 15.00, qty WITH 75, active WITH .T.
"""
        r = interp.run_source(setup, "setup")
        if not r.success:
            print(f"Setup failed: {r.message}")
            return 1
        print("Setup OK\n")

        # -- Test 1: IF / ELSEIF / ELSE -------------------------------------
        print("=== 1. IF / ELSEIF / ELSE ===")
        script = """\
GO 1
IF price > 20
    ? "Expensive"
ELSEIF price > 5
    ? "Medium"
ELSE
    ? "Cheap"
ENDIF
"""
        r = interp.run_source(script, "if_test")
        print(f"  Output: {r.data}")
        assert r.success
        assert "Medium" in (r.data or ""), f"Expected 'Medium', got: {r.data}"

        # -- Test 2: DO WHILE -----------------------------------------------
        print("\n=== 2. DO WHILE ===")
        script = """\
STORE 0 TO total
GO TOP
DO WHILE .NOT. EOF()
    total = total + price
    SKIP
ENDDO
? "Total:", total
"""
        r = interp.run_source(script, "while_test")
        print(f"  Output: {r.data}")
        assert r.success
        assert "52.74" in (r.data or ""), f"Expected total 52.74, got: {r.data}"

        # -- Test 3: FOR loop -----------------------------------------------
        print("\n=== 3. FOR loop ===")
        script = """\
STORE 0 TO mysum
FOR i = 1 TO 10
    mysum = mysum + i
ENDFOR
? "Sum 1-10:", mysum
"""
        r = interp.run_source(script, "for_test")
        print(f"  Output: {r.data}")
        assert r.success
        assert "55" in (r.data or ""), f"Expected 55, got: {r.data}"

        # -- Test 4: SCAN ---------------------------------------------------
        print("\n=== 4. SCAN ===")
        script = """\
STORE 0 TO active_count
SCAN FOR active
    active_count = active_count + 1
ENDSCAN
? "Active products:", active_count
"""
        r = interp.run_source(script, "scan_test")
        print(f"  Output: {r.data}")
        assert r.success
        assert "3" in (r.data or ""), f"Expected 3 active, got: {r.data}"

        # -- Test 5: DO CASE ------------------------------------------------
        print("\n=== 5. DO CASE ===")
        script = """\
GO 2
DO CASE
CASE price > 100
    ? "Premium"
CASE price > 20
    ? "Standard"
CASE price > 5
    ? "Budget"
OTHERWISE
    ? "Bargain"
ENDCASE
"""
        r = interp.run_source(script, "case_test")
        print(f"  Output: {r.data}")
        assert r.success
        assert "Standard" in (r.data or ""), f"Expected 'Standard', got: {r.data}"

        # -- Test 6: SCAN with REPLACE (the spec example pattern) -----------
        print("\n=== 6. SCAN + REPLACE (batch update) ===")
        script = """\
SCAN FOR active
    REPLACE price WITH price * 1.10
ENDSCAN
GO 1
? "New Widget price:", price
"""
        r = interp.run_source(script, "scan_replace")
        print(f"  Output: {r.data}")
        assert r.success
        # Widget was 9.99, 10% increase = 10.989
        assert "10.989" in (r.data or "") or "10.99" in (r.data or ""), f"Unexpected: {r.data}"

        # -- Test 7: .prg file execution ------------------------------------
        print("\n=== 7. .prg file execution ===")
        prg_path = Path(tmpdir) / "report.prg"
        prg_path.write_text("""\
* Report script
? "=== Product Report ==="
GO TOP
DO WHILE .NOT. EOF()
    ? name, STR(price, 10, 2)
    SKIP
ENDDO
? "=== End Report ==="
RETURN
""", encoding="utf-8")
        r = interp.run_program(prg_path)
        print(f"  Output:\n{r.data}")
        assert r.success
        assert "Product Report" in (r.data or "")
        assert "Widget" in (r.data or "")

        # -- Test 8: EXIT / LOOP in loops -----------------------------------
        print("\n=== 8. EXIT / LOOP ===")
        script = """\
STORE 0 TO found_at
FOR i = 1 TO 100
    IF i = 42
        found_at = i
        EXIT
    ENDIF
ENDFOR
? "Found at:", found_at
"""
        r = interp.run_source(script, "exit_test")
        print(f"  Output: {r.data}")
        assert r.success
        assert "42" in (r.data or "")

        script2 = """\
STORE 0 TO odd_sum
FOR i = 1 TO 10
    IF i / 2 = INT(i / 2)
        LOOP
    ENDIF
    odd_sum = odd_sum + i
ENDFOR
? "Odd sum:", odd_sum
"""
        r = interp.run_source(script2, "loop_test")
        print(f"  Output: {r.data}")
        assert r.success
        assert "25" in (r.data or ""), f"Expected 25, got: {r.data}"

        # -- Test 9: String functions combo ----------------------------------
        print("\n=== 9. String functions ===")
        script = """\
STORE "  Hello, World!  " TO s
? TRIM(s)
? LEFT(s, 7)
? RIGHT(s, 8)
? UPPER(TRIM(s))
? LEN(TRIM(s))
"""
        r = interp.run_source(script, "strings")
        print(f"  Output:\n{r.data}")
        assert r.success
        assert "Hello, World!" in (r.data or "")
        assert "HELLO, WORLD!" in (r.data or "")

        # -- Test 10: Comments -----------------------------------------------
        print("\n=== 10. Comments ===")
        script = """\
* This is a comment
? "Before"   && inline comment
? "After"
"""
        r = interp.run_source(script, "comments")
        print(f"  Output: {r.data}")
        assert r.success
        assert "Before" in (r.data or "")
        assert "After" in (r.data or "")

        env.close_all()
        print("\n=== ALL PROGRAM TESTS PASSED ===")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
