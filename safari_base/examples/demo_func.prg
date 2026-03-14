* demo_func.prg
* Illustrates user defined functions and procedures.

? "--- Safari Base Function/Procedure Demo ---"
? ""

FUNC Square(x)
    RETURN x * x
END FUNC

PROC Greet(name)
    ? "Hello, " + name + "!"
    ? "Welcome to Safari Base."
END PROC

DEF FN Cube(x) = x * x * x

? "Calling user-defined function Square(5):"
? "Square of 5 is: " + STR(Square(5))

? ""
? "Calling user-defined procedure Greet('User'):"
DO Greet WITH "User"

? ""
? "Calling inline DEF FN Cube(3):"
? "Cube of 3 is: " + STR(FN Cube(3))

? ""
? "Functions and procedures enable modular code."
? "Demo completed."
