"""Shared fixtures and markers for integration tests."""

from __future__ import annotations

import pytest


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "live: marks tests that hit live network services (deselect with '-m \"not live\"')",
    )
