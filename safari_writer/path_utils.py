"""Helpers for working with path strings across Windows and POSIX hosts."""

from pathlib import PureWindowsPath


def leaf_name(filename: str) -> str:
    """Return the final path component from either Windows or POSIX-style paths."""
    return PureWindowsPath(filename).name or filename
