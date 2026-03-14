"""Built-in functions for the dBASE language processor."""

from __future__ import annotations

import datetime
import math
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from safari_base.lang.environment import Environment

from safari_base.lang.errors import DBaseError


def call_function(name: str, args: list[Any], env: "Environment") -> Any:
    """Dispatch a built-in function call."""
    name_upper = name.upper()
    fn = _FUNCTIONS.get(name_upper)
    if fn is None:
        raise DBaseError(f"Unknown function: {name}", code="FUNC_NOT_FOUND")
    return fn(args, env)


# -- Database/navigation functions -------------------------------------------


def _eof(args: list[Any], env: "Environment") -> bool:
    wa = env.current_work_area()
    return wa.eof if wa else True


def _bof(args: list[Any], env: "Environment") -> bool:
    wa = env.current_work_area()
    return wa.bof if wa else True


def _found(args: list[Any], env: "Environment") -> bool:
    wa = env.current_work_area()
    return wa.found if wa else False


def _recno(args: list[Any], env: "Environment") -> int:
    wa = env.current_work_area()
    return wa.recno if wa else 0


def _reccount(args: list[Any], env: "Environment") -> int:
    wa = env.current_work_area()
    return wa.record_count if wa else 0


def _deleted(args: list[Any], env: "Environment") -> bool:
    wa = env.current_work_area()
    return wa.is_deleted() if wa else False


# -- String functions --------------------------------------------------------


def _len(args: list[Any], env: "Environment") -> int:
    _check_args("LEN", args, 1)
    return len(str(args[0]))


def _substr(args: list[Any], env: "Environment") -> str:
    _check_args("SUBSTR", args, 2, 3)
    s = str(args[0])
    start = max(1, int(args[1])) - 1  # dBASE is 1-based
    length = int(args[2]) if len(args) > 2 else len(s) - start
    return s[start : start + length]


def _left(args: list[Any], env: "Environment") -> str:
    _check_args("LEFT", args, 2)
    return str(args[0])[: int(args[1])]


def _right(args: list[Any], env: "Environment") -> str:
    _check_args("RIGHT", args, 2)
    s = str(args[0])
    n = int(args[1])
    return s[-n:] if n > 0 else ""


def _ltrim(args: list[Any], env: "Environment") -> str:
    _check_args("LTRIM", args, 1)
    return str(args[0]).lstrip()


def _rtrim(args: list[Any], env: "Environment") -> str:
    _check_args("RTRIM", args, 1)
    return str(args[0]).rstrip()


def _trim(args: list[Any], env: "Environment") -> str:
    _check_args("TRIM", args, 1)
    return str(args[0]).strip()


def _upper(args: list[Any], env: "Environment") -> str:
    _check_args("UPPER", args, 1)
    return str(args[0]).upper()


def _lower(args: list[Any], env: "Environment") -> str:
    _check_args("LOWER", args, 1)
    return str(args[0]).lower()


# -- Conversion functions ----------------------------------------------------


def _str_fn(args: list[Any], env: "Environment") -> str:
    _check_args("STR", args, 1, 3)
    val = float(args[0])
    if len(args) >= 2:
        width = int(args[1])
        decimals = int(args[2]) if len(args) > 2 else 0
        if decimals > 0:
            return f"{val:{width}.{decimals}f}"
        return f"{val:{width}.0f}"
    return str(int(val)) if val == int(val) else str(val)


def _val(args: list[Any], env: "Environment") -> float:
    _check_args("VAL", args, 1)
    try:
        return float(str(args[0]).strip())
    except ValueError:
        return 0.0


def _dtoc(args: list[Any], env: "Environment") -> str:
    _check_args("DTOC", args, 1)
    val = args[0]
    if isinstance(val, datetime.date):
        return val.strftime("%m/%d/%Y")
    return str(val)


def _ctod(args: list[Any], env: "Environment") -> datetime.date:
    _check_args("CTOD", args, 1)
    s = str(args[0]).strip()
    # Try YYYY-MM-DD first, then MM/DD/YYYY
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"):
        try:
            return datetime.datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    raise DBaseError(f"Cannot convert '{s}' to date")


# -- Date functions ----------------------------------------------------------


def _date(args: list[Any], env: "Environment") -> datetime.date:
    return datetime.date.today()


def _year(args: list[Any], env: "Environment") -> int:
    _check_args("YEAR", args, 1)
    val = args[0]
    if isinstance(val, datetime.date):
        return val.year
    return 0


def _month(args: list[Any], env: "Environment") -> int:
    _check_args("MONTH", args, 1)
    val = args[0]
    if isinstance(val, datetime.date):
        return val.month
    return 0


def _day(args: list[Any], env: "Environment") -> int:
    _check_args("DAY", args, 1)
    val = args[0]
    if isinstance(val, datetime.date):
        return val.day
    return 0


# -- Math functions (bonuses) ------------------------------------------------


def _int_fn(args: list[Any], env: "Environment") -> int:
    _check_args("INT", args, 1)
    return int(float(args[0]))


def _abs_fn(args: list[Any], env: "Environment") -> float:
    _check_args("ABS", args, 1)
    return abs(float(args[0]))


def _round_fn(args: list[Any], env: "Environment") -> float:
    _check_args("ROUND", args, 2)
    return round(float(args[0]), int(args[1]))


def _type_fn(args: list[Any], env: "Environment") -> str:
    """TYPE() — return single-char type indicator."""
    _check_args("TYPE", args, 1)
    val = args[0]
    if isinstance(val, bool):
        return "L"
    if isinstance(val, (int, float)):
        return "N"
    if isinstance(val, datetime.date):
        return "D"
    if isinstance(val, str):
        return "C"
    if isinstance(val, dict):
        return "H"
    return "U"


# -- Hash functions ----------------------------------------------------------


def _hlen(args: list[Any], env: "Environment") -> int:
    """HLEN(hashname$) — return number of keys in a hashmap."""
    _check_args("HLEN", args, 1)
    name = str(args[0]).upper()
    val = env.variables.get(name)
    if not isinstance(val, dict):
        raise DBaseError(f"HLEN: {name} is not a hashmap")
    return len(val)


def _hhas(args: list[Any], env: "Environment") -> bool:
    """HHAS(hashname$, key$) — return .T. if key exists."""
    _check_args("HHAS", args, 2)
    name = str(args[0]).upper()
    key = str(args[1])
    val = env.variables.get(name)
    if not isinstance(val, dict):
        raise DBaseError(f"HHAS: {name} is not a hashmap")
    return key in val


def _hdel(args: list[Any], env: "Environment") -> bool:
    """HDEL(hashname$, key$) — delete a key, return .T. if existed."""
    _check_args("HDEL", args, 2)
    name = str(args[0]).upper()
    key = str(args[1])
    val = env.variables.get(name)
    if not isinstance(val, dict):
        raise DBaseError(f"HDEL: {name} is not a hashmap")
    if key in val:
        del val[key]
        return True
    return False


def _hkeys(args: list[Any], env: "Environment") -> str:
    """HKEYS(hashname$) — return comma-separated list of keys."""
    _check_args("HKEYS", args, 1)
    name = str(args[0]).upper()
    val = env.variables.get(name)
    if not isinstance(val, dict):
        raise DBaseError(f"HKEYS: {name} is not a hashmap")
    return ",".join(str(k) for k in val.keys())


# -- Helpers -----------------------------------------------------------------


def _check_args(
    name: str, args: list[Any], min_args: int, max_args: int | None = None
) -> None:
    if max_args is None:
        max_args = min_args
    if len(args) < min_args or len(args) > max_args:
        if min_args == max_args:
            raise DBaseError(
                f"{name}() requires {min_args} argument(s), got {len(args)}"
            )
        raise DBaseError(
            f"{name}() requires {min_args}-{max_args} arguments, got {len(args)}"
        )


# -- Function dispatch table ------------------------------------------------

_FUNCTIONS: dict[str, Any] = {
    # Database
    "EOF": _eof,
    "BOF": _bof,
    "FOUND": _found,
    "RECNO": _recno,
    "RECCOUNT": _reccount,
    "DELETED": _deleted,
    # String
    "LEN": _len,
    "SUBSTR": _substr,
    "LEFT": _left,
    "RIGHT": _right,
    "LTRIM": _ltrim,
    "RTRIM": _rtrim,
    "TRIM": _trim,
    "UPPER": _upper,
    "LOWER": _lower,
    # Conversion
    "STR": _str_fn,
    "VAL": _val,
    "DTOC": _dtoc,
    "CTOD": _ctod,
    # Date
    "DATE": _date,
    "YEAR": _year,
    "MONTH": _month,
    "DAY": _day,
    # Math
    "INT": _int_fn,
    "ABS": _abs_fn,
    "ROUND": _round_fn,
    # Meta
    "TYPE": _type_fn,
    # Hash
    "HLEN": _hlen,
    "HHAS": _hhas,
    "HDEL": _hdel,
    "HKEYS": _hkeys,
}
