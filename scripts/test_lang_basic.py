"""Basic exercise script for the Safari Base language processor.

Exercises: CREATE TABLE, USE, APPEND, REPLACE, navigation, LIST,
variables, expressions, control flow, functions.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

# Ensure the repo root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from safari_base.lang import CommandResult, Environment, Interpreter


def check(result: CommandResult, label: str) -> None:
    if not result.success:
        print(f"  FAIL {label}: {result.message}")
        sys.exit(1)
    print(f"  OK   {label}: {result.message}")


def main() -> int:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        env = Environment(work_dir=tmpdir, default_dir=tmpdir, unsafe=True)
        interp = Interpreter(env)

        print("=== 1. CREATE TABLE ===")
        r = interp.execute(
            "CREATE TABLE customers (cust_id C(10), name C(40), balance N(12,2), active L, joined D)"
        )
        check(r, "CREATE TABLE customers")

        print("\n=== 2. APPEND + REPLACE ===")
        r = interp.execute("APPEND BLANK")
        check(r, "APPEND BLANK #1")
        r = interp.execute(
            'REPLACE cust_id WITH "C001", name WITH "Alice", balance WITH 1500.50'
        )
        check(r, "REPLACE #1")
        r = interp.execute("REPLACE active WITH .T.")
        check(r, "REPLACE active #1")

        r = interp.execute("APPEND BLANK")
        check(r, "APPEND BLANK #2")
        r = interp.execute(
            'REPLACE cust_id WITH "C002", name WITH "Bob", balance WITH 800.00'
        )
        check(r, "REPLACE #2")
        r = interp.execute("REPLACE active WITH .T.")
        check(r, "REPLACE active #2")

        r = interp.execute("APPEND BLANK")
        check(r, "APPEND BLANK #3")
        r = interp.execute(
            'REPLACE cust_id WITH "C003", name WITH "Carol", balance WITH 2000.00'
        )
        check(r, "REPLACE #3")
        r = interp.execute("REPLACE active WITH .F.")
        check(r, "REPLACE active #3")

        print("\n=== 3. NAVIGATION ===")
        r = interp.execute("GO TOP")
        check(r, "GO TOP")
        r = interp.execute("SKIP")
        check(r, "SKIP")
        r = interp.execute("GO BOTTOM")
        check(r, "GO BOTTOM")
        r = interp.execute("GO 1")
        check(r, "GO 1")

        print("\n=== 4. LIST ===")
        r = interp.execute("LIST")
        check(r, "LIST")
        output = env.flush_output()
        print(output)

        print("\n=== 5. VARIABLES & EXPRESSIONS ===")
        r = interp.execute("STORE 42 TO myvar")
        check(r, "STORE 42")
        r = interp.execute("? myvar + 8")
        check(r, "? myvar + 8")
        output = env.flush_output()
        print(f"  Output: {output}")
        assert "50" in output, f"Expected 50 in output, got: {output}"

        print("\n=== 6. FUNCTIONS ===")
        r = interp.execute('? UPPER("hello")')
        output = env.flush_output()
        print(f"  UPPER: {output}")
        assert "HELLO" in output

        r = interp.execute('? LEN("test")')
        output = env.flush_output()
        print(f"  LEN: {output}")
        assert "4" in output

        r = interp.execute('? SUBSTR("abcdef", 2, 3)')
        output = env.flush_output()
        print(f"  SUBSTR: {output}")
        assert "bcd" in output

        r = interp.execute("? EOF()")
        output = env.flush_output()
        print(f"  EOF: {output}")

        r = interp.execute("? RECCOUNT()")
        output = env.flush_output()
        print(f"  RECCOUNT: {output}")
        assert "3" in output

        print("\n=== 7. LOCATE ===")
        r = interp.execute('LOCATE FOR name = "Bob"')
        check(r, "LOCATE FOR Bob")
        assert "2" in r.message, f"Expected record 2, got: {r.message}"

        r = interp.execute("? FOUND()")
        output = env.flush_output()
        print(f"  FOUND: {output}")
        assert "True" in output

        print("\n=== 8. COUNT / SUM / AVERAGE ===")
        r = interp.execute("COUNT TO cnt")
        check(r, "COUNT")
        output = env.flush_output()
        print(f"  {output}")
        assert env.variables.get("CNT") == 3.0

        r = interp.execute("SUM balance TO total")
        check(r, "SUM balance")
        output = env.flush_output()
        print(f"  {output}")
        assert env.variables.get("TOTAL") == 4300.5

        r = interp.execute("AVERAGE balance TO avg")
        check(r, "AVERAGE balance")
        output = env.flush_output()
        print(f"  {output}")

        print("\n=== 9. DELETE / RECALL / PACK ===")
        r = interp.execute("GO 3")
        check(r, "GO 3")
        r = interp.execute("DELETE")
        check(r, "DELETE")
        r = interp.execute("? DELETED()")
        output = env.flush_output()
        print(f"  DELETED: {output}")
        assert "True" in output

        r = interp.execute("RECALL")
        check(r, "RECALL")
        r = interp.execute("? DELETED()")
        output = env.flush_output()
        print(f"  After RECALL: {output}")
        assert "False" in output

        r = interp.execute("DELETE")
        check(r, "DELETE rec 3 again")
        r = interp.execute("PACK")
        check(r, "PACK")
        r = interp.execute("? RECCOUNT()")
        output = env.flush_output()
        print(f"  After PACK: {output}")
        assert "2" in output

        print("\n=== 10. DISPLAY STRUCTURE ===")
        r = interp.execute("DISPLAY STRUCTURE")
        check(r, "DISPLAY STRUCTURE")
        output = env.flush_output()
        print(output)

        print("\n=== 11. CLOSE ===")
        r = interp.execute("CLOSE")
        check(r, "CLOSE")

        env.close_all()
        print("\n=== ALL BASIC TESTS PASSED ===")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
