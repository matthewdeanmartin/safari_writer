"""Exercise script for user-defined functions and procedures.

Tests: FUNC/END FUNC, PROC/END PROC, DEF FN, recursion,
string functions, procedure calls as statements.
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

    # -- Test 1: Tiny math function (FUNC/END FUNC) -------------------------
    print("=== 1. FUNC ADD(A,B) ===")
    out = run(interp, """\
FUNC ADD(A,B)
    RETURN A+B
END FUNC
? "5 + 7 =", ADD(5,7)
""")
    print(f"  Output: {out}")
    assert "12" in out, f"Expected 12, got: {out}"

    # -- Test 2: Function in IF condition ------------------------------------
    print("\n=== 2. FUNC in IF ===")
    out = run(interp, """\
FUNC ISADULT(X)
    IF X>=18
        RETURN 1
    ENDIF
    RETURN 0
END FUNC
STORE 21 TO A
IF ISADULT(A)
    ? "ADULT"
ELSE
    ? "CHILD"
ENDIF
""")
    print(f"  Output: {out}")
    assert "ADULT" in out, f"Expected ADULT, got: {out}"

    # -- Test 3: String function -------------------------------------------
    print("\n=== 3. String FUNC ===")
    out = run(interp, """\
FUNC GREET(X)
    RETURN "HELLO, "+X+"!"
END FUNC
? GREET("WORLD")
""")
    print(f"  Output: {out}")
    assert "HELLO, WORLD!" in out, f"Expected HELLO, WORLD!, got: {out}"

    # -- Test 4: PROC (procedure) ------------------------------------------
    print("\n=== 4. PROC DOBOX ===")
    out = run(interp, """\
PROC DOBOX(N)
    ? "*****"
    ? "* ", N, " *"
    ? "*****"
END PROC
FOR I=1 TO 2
    DOBOX(I)
ENDFOR
""")
    print(f"  Output: {out}")
    assert out.count("*****") == 4, f"Expected 4 star lines, got: {out}"

    # -- Test 5: Squared function ------------------------------------------
    print("\n=== 5. FUNC SQR2 ===")
    out = run(interp, """\
FUNC SQR2(X)
    RETURN X*X
END FUNC
FOR I=1 TO 3
    ? I, " SQUARED =", SQR2(I)
ENDFOR
""")
    print(f"  Output: {out}")
    assert "4" in out
    assert "9" in out

    # -- Test 6: Recursive factorial ----------------------------------------
    print("\n=== 6. Recursive FACT ===")
    out = run(interp, """\
FUNC FACT(N)
    IF N<=1
        RETURN 1
    ENDIF
    RETURN N*FACT(N-1)
END FUNC
? "FACT(0) =", FACT(0)
? "FACT(5) =", FACT(5)
? "FACT(8) =", FACT(8)
""")
    print(f"  Output: {out}")
    assert "120" in out, f"Expected 120, got: {out}"
    assert "40320" in out, f"Expected 40320, got: {out}"

    # -- Test 7: Game-ish DAMAGE function -----------------------------------
    print("\n=== 7. FUNC DAMAGE ===")
    out = run(interp, """\
FUNC DAMAGE(POWER,ENEMY)
    STORE POWER*2-ENEMY TO BASE
    IF BASE<1
        RETURN 1
    ENDIF
    RETURN BASE
END FUNC
? "DAMAGE =", DAMAGE(10,3)
? "DAMAGE =", DAMAGE(1,5)
""")
    print(f"  Output: {out}")
    assert "17" in out, f"Expected 17, got: {out}"
    assert "1" in out

    # -- Test 8: DEF FN one-liners -----------------------------------------
    print("\n=== 8. DEF FN one-liners ===")
    out = run(interp, """\
DEF FN ADD(A,B) = A+B
DEF FN DOUBLE(X) = X*2
? FN ADD(3,4)
? FN DOUBLE(9)
""")
    print(f"  Output: {out}")
    assert "7" in out, f"Expected 7, got: {out}"
    assert "18" in out, f"Expected 18, got: {out}"

    # -- Test 9: MAX function -----------------------------------------------
    print("\n=== 9. FUNC MAX ===")
    out = run(interp, """\
FUNC MAX(A,B)
    IF A>B
        RETURN A
    ENDIF
    RETURN B
END FUNC
? "MAX =", MAX(42,17)
? "MAX =", MAX(3,99)
""")
    print(f"  Output: {out}")
    assert "42" in out
    assert "99" in out

    # -- Test 10: PROC with string arg (SAYHELLO) ---------------------------
    print("\n=== 10. PROC SAYHELLO ===")
    out = run(interp, """\
PROC SAYHELLO(X)
    ? "HELLO", X
    ? "WELCOME TO SAFARI BASIC"
END PROC
SAYHELLO("MATT")
""")
    print(f"  Output: {out}")
    assert "MATT" in out
    assert "SAFARI BASIC" in out

    # -- Test 11: Function scope isolation ----------------------------------
    print("\n=== 11. Scope isolation ===")
    out = run(interp, """\
FUNC ADDONE(X)
    RETURN X+1
END FUNC
STORE 100 TO X
? ADDONE(5)
? X
""")
    print(f"  Output: {out}")
    assert "6" in out, f"Expected 6, got: {out}"
    assert "100" in out, f"X should still be 100, got: {out}"

    print("\n=== ALL FUNCTION TESTS PASSED ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
