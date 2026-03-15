"""Small helpers for Windows-only API access."""

from __future__ import annotations

import ctypes
from typing import Any


def get_kernel32() -> Any | None:
    """Return the Windows kernel32 handle when available."""
    windll = getattr(ctypes, "windll", None)
    if windll is None:
        return None
    return windll.kernel32
