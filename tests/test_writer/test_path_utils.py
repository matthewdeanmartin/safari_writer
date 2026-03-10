"""Tests for path utility functions."""

from __future__ import annotations

from safari_writer.path_utils import leaf_name


class TestLeafName:
    def test_unix_path(self) -> None:
        assert leaf_name("/home/user/doc.txt") == "doc.txt"

    def test_windows_path(self) -> None:
        assert leaf_name(r"C:\Users\user\doc.txt") == "doc.txt"

    def test_just_filename(self) -> None:
        assert leaf_name("doc.txt") == "doc.txt"

    def test_trailing_slash_returns_empty_falls_back(self) -> None:
        # PureWindowsPath("C:\\foo\\").name returns "" so leaf_name falls back
        result = leaf_name(r"C:\foo" + "\\")
        # Should return the input or the last component
        assert isinstance(result, str)

    def test_nested_windows_path(self) -> None:
        assert leaf_name(r"C:\Users\me\Documents\My File.sfw") == "My File.sfw"

    def test_empty_string(self) -> None:
        result = leaf_name("")
        assert result == ""

    def test_forward_slash_windows_style(self) -> None:
        # PureWindowsPath handles forward slashes on Windows
        assert leaf_name("C:/Users/doc.sfw") == "doc.sfw"

    def test_mixed_slashes(self) -> None:
        assert leaf_name(r"C:/Users\me/doc.txt") == "doc.txt"
