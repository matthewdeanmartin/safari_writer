"""Tests for the Index screen and format_size utility."""

from __future__ import annotations

from pathlib import Path

from safari_writer.screens.index_screen import _format_size


class TestFormatSize:
    def test_bytes(self) -> None:
        assert _format_size(512).strip() == "512"

    def test_zero(self) -> None:
        assert _format_size(0).strip() == "0"

    def test_kilobytes(self) -> None:
        result = _format_size(2048)
        assert "K" in result
        assert "2" in result

    def test_megabytes(self) -> None:
        result = _format_size(5 * 1024 * 1024)
        assert "MB" in result
        assert "5" in result

    def test_gigabytes(self) -> None:
        result = _format_size(3 * 1024 * 1024 * 1024)
        assert "GB" in result
        assert "3" in result

    def test_boundary_1023(self) -> None:
        result = _format_size(1023)
        assert "K" not in result

    def test_boundary_1024(self) -> None:
        result = _format_size(1024)
        assert "K" in result

    def test_boundary_1mb(self) -> None:
        result = _format_size(1024 * 1024)
        assert "MB" in result

    def test_boundary_1gb(self) -> None:
        result = _format_size(1024 * 1024 * 1024)
        assert "GB" in result

    def test_large_bytes_below_1k(self) -> None:
        result = _format_size(999)
        assert "K" not in result
        assert "999" in result.strip()
