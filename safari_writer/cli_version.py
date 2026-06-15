"""Shared CLI version helper."""

from __future__ import annotations

from importlib import metadata

__all__ = ["version_string"]


def version_string(distribution: str = "safari-writer") -> str:
    """Return the installed distribution version, or a local fallback."""

    try:
        return metadata.version(distribution)
    except metadata.PackageNotFoundError:
        return "0.1.0"
