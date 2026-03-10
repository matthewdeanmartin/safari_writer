"""Safari Base dBASE III+ language processor.

This package provides a standalone, headless dBASE III+ interpreter
that can be used independently of the Safari Base UI.

Three execution modes:
    1. Command mode:  interpreter.execute("USE customers")
    2. Program mode:  interpreter.run_program("myscript.prg")
    3. Embedded mode:  interpreter.run_source("...")
"""

from safari_base.lang.environment import Environment
from safari_base.lang.errors import DBaseError, NoTableError, ParseError
from safari_base.lang.interpreter import Interpreter
from safari_base.lang.types import CommandResult

__all__ = [
    "CommandResult",
    "DBaseError",
    "Environment",
    "Interpreter",
    "NoTableError",
    "ParseError",
]
