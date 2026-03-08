"""Tests for the Style Switcher screen logic."""

from __future__ import annotations

from safari_writer.screens.style_switcher import THEME_NAMES, StyleSwitcherScreen
from safari_writer.themes import THEMES, DEFAULT_THEME


class TestThemeNames:
    def test_theme_names_matches_themes(self) -> None:
        assert set(THEME_NAMES) == set(THEMES.keys())

    def test_theme_names_is_a_list(self) -> None:
        assert isinstance(THEME_NAMES, list)
        assert len(THEME_NAMES) >= 4


class TestStyleSwitcherInit:
    def test_valid_theme_selects_correct_index(self) -> None:
        screen = StyleSwitcherScreen("amber")
        assert screen._selected == THEME_NAMES.index("amber")

    def test_default_theme_selects_correctly(self) -> None:
        screen = StyleSwitcherScreen(DEFAULT_THEME)
        assert screen._selected == THEME_NAMES.index(DEFAULT_THEME)

    def test_unknown_theme_defaults_to_zero(self) -> None:
        screen = StyleSwitcherScreen("nonexistent-theme")
        assert screen._selected == 0

    def test_each_theme_selectable(self) -> None:
        for i, name in enumerate(THEME_NAMES):
            screen = StyleSwitcherScreen(name)
            assert screen._selected == i
