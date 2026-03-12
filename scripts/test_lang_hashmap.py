"""Exercise script for hashmaps (DIM/FOR EACH) and PRINT keyword.

Tests: DIM FOO{}, FOO("key") = val, FOO("key") read, FOR EACH,
HLEN, HHAS, HDEL, HKEYS, PRINT keyword, nested usage.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from safari_base.lang import Environment, Interpreter


def run(interp: Interpreter, source: str, name: str = "test") -> str:
    r = interp.run_source(source, name)
    if not r.success:
        print(f"  FAIL: {r.message}")
        sys.exit(1)
    return r.data or ""


def main() -> int:
    env = Environment(unsafe=True)
    interp = Interpreter(env)

    # -- Test 1: Basic DIM and assign/read ----------------------------------
    print("=== 1. DIM + assign + read ===")
    out = run(interp, """\
DIM PRICES{}
PRICES("APPLES") = 1.29
PRICES("BREAD") = 3.49
PRICES("MILK") = 4.99
? "APPLES:", PRICES("APPLES")
? "BREAD:", PRICES("BREAD")
? "MILK:", PRICES("MILK")
""")
    print(f"  Output: {out}")
    assert "1.29" in out, f"Expected 1.29, got: {out}"
    assert "3.49" in out
    assert "4.99" in out

    # -- Test 2: FOR EACH iteration ----------------------------------------
    print("\n=== 2. FOR EACH K$ IN PRICES ===")
    out = run(interp, """\
DIM PRICES{}
PRICES("APPLES") = 1.29
PRICES("BREAD") = 3.49
PRICES("MILK") = 4.99
FOR EACH K IN PRICES
    PRINT K, PRICES(K)
NEXT
""")
    print(f"  Output: {out}")
    assert "APPLES" in out
    assert "BREAD" in out
    assert "MILK" in out

    # -- Test 3: HLEN, HHAS ------------------------------------------------
    print("\n=== 3. HLEN, HHAS ===")
    out = run(interp, """\
DIM INV{}
INV("SWORD") = 1
INV("SHIELD") = 1
INV("POTION") = 3
? "COUNT:", HLEN("INV")
? "HAS SWORD:", HHAS("INV", "SWORD")
? "HAS AXE:", HHAS("INV", "AXE")
""")
    print(f"  Output: {out}")
    assert "3" in out
    assert "True" in out
    assert "False" in out

    # -- Test 4: HDEL ------------------------------------------------------
    print("\n=== 4. HDEL ===")
    out = run(interp, """\
DIM BAG{}
BAG("KEY") = 1
BAG("MAP") = 1
? "BEFORE:", HLEN("BAG")
STORE HDEL("BAG", "KEY") TO removed
? "REMOVED:", removed
? "AFTER:", HLEN("BAG")
? "HAS KEY:", HHAS("BAG", "KEY")
""")
    print(f"  Output: {out}")
    assert "BEFORE: 2" in out
    assert "REMOVED: True" in out
    assert "AFTER: 1" in out

    # -- Test 5: HKEYS -----------------------------------------------------
    print("\n=== 5. HKEYS ===")
    out = run(interp, """\
DIM COLORS{}
COLORS("RED") = 1
COLORS("GREEN") = 2
COLORS("BLUE") = 3
? HKEYS("COLORS")
""")
    print(f"  Output: {out}")
    assert "RED" in out
    assert "GREEN" in out
    assert "BLUE" in out

    # -- Test 6: Overwrite existing key ------------------------------------
    print("\n=== 6. Overwrite key ===")
    out = run(interp, """\
DIM SCORES{}
SCORES("ALICE") = 100
SCORES("ALICE") = 250
? SCORES("ALICE")
""")
    print(f"  Output: {out}")
    assert "250" in out

    # -- Test 7: Hash with string values -----------------------------------
    print("\n=== 7. String values ===")
    out = run(interp, """\
DIM NAMES{}
NAMES("P1") = "ALICE"
NAMES("P2") = "BOB"
FOR EACH K IN NAMES
    ? K, "=", NAMES(K)
NEXT
""")
    print(f"  Output: {out}")
    assert "ALICE" in out
    assert "BOB" in out

    # -- Test 8: Hash inside a FUNC ----------------------------------------
    print("\n=== 8. Hash + FUNC ===")
    out = run(interp, """\
DIM PRICES{}
PRICES("A") = 10
PRICES("B") = 20
PRICES("C") = 30

FUNC TOTAL(H)
    STORE 0 TO S
    FOR EACH K IN PRICES
        S = S + PRICES(K)
    NEXT
    RETURN S
END FUNC

? "TOTAL:", TOTAL("PRICES")
""")
    print(f"  Output: {out}")
    assert "60" in out

    # -- Test 9: PRINT keyword works like ? --------------------------------
    print("\n=== 9. PRINT keyword ===")
    out = run(interp, """\
PRINT "HELLO WORLD"
PRINT 1+2+3
""")
    print(f"  Output: {out}")
    assert "HELLO WORLD" in out
    assert "6" in out

    # -- Test 10: FOR EACH with EXIT/LOOP ----------------------------------
    print("\n=== 10. FOR EACH with EXIT ===")
    out = run(interp, """\
DIM DATA{}
DATA("A") = 1
DATA("B") = 2
DATA("C") = 3
DATA("D") = 4
STORE 0 TO found
FOR EACH K IN DATA
    IF DATA(K) = 3
        found = 1
        EXIT
    ENDIF
NEXT
? "FOUND:", found
""")
    print(f"  Output: {out}")
    assert "FOUND: 1" in out

    # -- Test 11: Empty hash iteration -------------------------------------
    print("\n=== 11. Empty hash FOR EACH ===")
    out = run(interp, """\
DIM EMPTY{}
STORE 0 TO count
FOR EACH K IN EMPTY
    count = count + 1
NEXT
? "COUNT:", count
""")
    print(f"  Output: {out}")
    assert "COUNT: 0" in out

    # -- Test 12: Hash with computed keys ----------------------------------
    print("\n=== 12. Computed keys ===")
    out = run(interp, """\
DIM MAP{}
FOR I = 1 TO 3
    MAP(STR(I, 1)) = I * I
ENDFOR
? MAP("1"), MAP("2"), MAP("3")
""")
    print(f"  Output: {out}")
    assert "1" in out
    assert "4" in out
    assert "9" in out

    print("\n=== ALL HASHMAP TESTS PASSED ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
