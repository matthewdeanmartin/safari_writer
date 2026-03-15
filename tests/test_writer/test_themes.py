"""Tests for theme definitions and settings persistence."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from safari_writer.themes import (
    DEFAULT_THEME,
    THEME_LABELS,
    THEMES,
    load_settings,
    save_settings,
)


class TestThemeDefinitions:
    def test_default_theme_exists(self) -> None:
        assert DEFAULT_THEME in THEMES

    def test_all_themes_have_labels(self) -> None:
        for name in THEMES:
            assert name in THEME_LABELS, f"Missing label for theme '{name}'"

    def test_at_least_four_themes(self) -> None:
        assert len(THEMES) >= 4

    def test_all_themes_are_dark(self) -> None:
        for name, theme in THEMES.items():
            assert theme.dark, f"Theme '{name}' should be dark"

    def test_theme_names_match_keys(self) -> None:
        for key, theme in THEMES.items():
            assert theme.name == key

    def test_classic_blue_is_default(self) -> None:
        assert DEFAULT_THEME == "classic-blue"

    def test_expected_themes_present(self) -> None:
        expected = {"classic-blue", "green-phosphor", "amber", "high-contrast"}
        assert expected == set(THEMES.keys())


class TestSettingsPersistence:
    def test_load_returns_empty_dict_when_missing(self, tmp_path: Path) -> None:
        fake_path = tmp_path / "nonexistent" / "settings.json"
        with patch("safari_writer.themes._settings_path", return_value=fake_path):
            result = load_settings()
        assert result == {}

    def test_save_and_load_roundtrip(self, tmp_path: Path) -> None:
        fake_path = tmp_path / "settings.json"
        with patch("safari_writer.themes._settings_path", return_value=fake_path):
            save_settings({"theme": "amber", "custom_key": 42})
            result = load_settings()
        assert result["theme"] == "amber"
        assert result["custom_key"] == 42

    def test_load_handles_corrupt_json(self, tmp_path: Path) -> None:
        fake_path = tmp_path / "settings.json"
        fake_path.write_text("{invalid json!!!", encoding="utf-8")
        with patch("safari_writer.themes._settings_path", return_value=fake_path):
            result = load_settings()
        assert result == {}

    def test_load_handles_non_dict_json(self, tmp_path: Path) -> None:
        fake_path = tmp_path / "settings.json"
        fake_path.write_text('"just a string"', encoding="utf-8")
        with patch("safari_writer.themes._settings_path", return_value=fake_path):
            result = load_settings()
        assert result == {}

    def test_save_creates_valid_json(self, tmp_path: Path) -> None:
        fake_path = tmp_path / "settings.json"
        with patch("safari_writer.themes._settings_path", return_value=fake_path):
            save_settings({"theme": "green-phosphor"})
        data = json.loads(fake_path.read_text(encoding="utf-8"))
        assert data == {"theme": "green-phosphor"}

    def test_save_overwrites_existing(self, tmp_path: Path) -> None:
        fake_path = tmp_path / "settings.json"
        with patch("safari_writer.themes._settings_path", return_value=fake_path):
            save_settings({"theme": "amber"})
            save_settings({"theme": "high-contrast"})
            result = load_settings()
        assert result["theme"] == "high-contrast"
