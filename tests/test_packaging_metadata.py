"""Tests for published packaging metadata."""

from __future__ import annotations

import tomllib
from pathlib import Path


def test_pyproject_requires_supported_pillow_on_python_314_plus() -> None:
    pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    project = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))["project"]
    dependencies = project["dependencies"]

    assert "Pillow>=10.0.0; python_version < '3.14'" in dependencies
    assert "Pillow>=12.0.0; python_version >= '3.14'" in dependencies
    assert not any(dependency.startswith("term-image") for dependency in dependencies)
