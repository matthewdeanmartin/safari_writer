"""Unit tests for safari_writer.locale_info (i18n Level 0, 1, 2)."""

from __future__ import annotations

import os
from datetime import datetime
from unittest.mock import patch

import pytest

from safari_writer.locale_info import (
    _normalize_tag,
    available_languages,
    format_datetime,
    get_locale,
    get_translation,
    refresh,
)


# ---------------------------------------------------------------------------
# _normalize_tag
# ---------------------------------------------------------------------------


class TestNormalizeTag:
    def test_ietf_underscore(self):
        assert _normalize_tag("fr_FR") == "fr_FR"

    def test_ietf_hyphen(self):
        assert _normalize_tag("fr-FR") == "fr_FR"

    def test_with_encoding(self):
        assert _normalize_tag("de_DE.UTF-8") == "de_DE"

    def test_with_at_modifier(self):
        assert _normalize_tag("sr_RS@latin") == "sr_RS"

    def test_bare_language(self):
        assert _normalize_tag("fr") == "fr"

    def test_garbage(self):
        assert _normalize_tag("???") == ""

    def test_empty(self):
        assert _normalize_tag("") == ""


# ---------------------------------------------------------------------------
# get_locale
# ---------------------------------------------------------------------------


class TestGetLocale:
    def test_env_var_override(self):
        with patch.dict(os.environ, {"SAFARI_LOCALE": "ja_JP"}):
            assert get_locale() == "ja_JP"

    def test_env_var_normalized(self):
        with patch.dict(os.environ, {"SAFARI_LOCALE": "pt-BR.UTF-8"}):
            assert get_locale() == "pt_BR"

    def test_env_var_invalid_falls_through(self):
        with patch.dict(os.environ, {"SAFARI_LOCALE": "???"}):
            result = get_locale()
            # Should still return a valid locale (from OS or fallback)
            assert len(result) >= 2

    def test_fallback_is_valid(self):
        with patch.dict(os.environ, {}, clear=True):
            result = get_locale()
            assert len(result) >= 2  # at minimum a 2-letter language code


class TestRefresh:
    def test_refresh_updates_module_vars(self):
        import safari_writer.locale_info as li

        with patch.dict(os.environ, {"SAFARI_LOCALE": "ko_KR"}):
            refresh()
            assert li.LOCALE == "ko_KR"
            assert li.LANGUAGE == "ko"
            assert li.REGION == "KR"
        # Restore
        refresh()


# ---------------------------------------------------------------------------
# format_datetime
# ---------------------------------------------------------------------------


class TestFormatDatetime:
    def test_full_returns_string(self):
        dt = datetime(2025, 6, 15, 14, 30, 45)
        result = format_datetime(dt, "full")
        assert isinstance(result, str)
        assert len(result) >= 8

    def test_short_returns_string(self):
        dt = datetime(2025, 6, 15, 14, 30, 45)
        result = format_datetime(dt, "short")
        assert isinstance(result, str)
        assert len(result) >= 8

    def test_date_returns_string(self):
        dt = datetime(2025, 6, 15, 14, 30, 45)
        result = format_datetime(dt, "date")
        assert isinstance(result, str)
        assert len(result) >= 6

    def test_time_returns_string(self):
        dt = datetime(2025, 6, 15, 14, 30, 45)
        result = format_datetime(dt, "time")
        assert isinstance(result, str)
        assert len(result) >= 4

    def test_unknown_style_uses_isoformat(self):
        dt = datetime(2025, 6, 15, 14, 30, 45)
        result = format_datetime(dt, "bogus")
        assert "2025" in result


# ---------------------------------------------------------------------------
# available_languages
# ---------------------------------------------------------------------------


class TestAvailableLanguages:
    def test_returns_list(self):
        result = available_languages()
        assert isinstance(result, list)

    def test_sorted(self):
        result = available_languages()
        assert result == sorted(result)


# ---------------------------------------------------------------------------
# get_translation (Level 3)
# ---------------------------------------------------------------------------


class TestGetTranslation:
    def test_english_passthrough(self):
        trans = get_translation("en")
        assert trans.gettext("Create File") == "Create File"

    def test_english_full_tag(self):
        trans = get_translation("en_US")
        assert trans.gettext("Quit") == "Quit"

    def test_french_known_string(self):
        trans = get_translation("fr")
        result = trans.gettext("Quit")
        assert result == "Quitter"

    def test_spanish_known_string(self):
        trans = get_translation("es")
        result = trans.gettext("Create File")
        assert result == "Crear archivo"

    def test_po_fallback_when_mo_missing(self, tmp_path, monkeypatch):
        locale_dir = tmp_path / "locales" / "fr" / "LC_MESSAGES"
        locale_dir.mkdir(parents=True)
        (locale_dir / "safari_writer.po").write_text(
            "\n".join(
                [
                    'msgid ""',
                    'msgstr ""',
                    "",
                    'msgid "Quit"',
                    'msgstr "Quitter"',
                    "",
                ]
            ),
            encoding="utf-8",
        )

        import safari_writer.locale_info as li

        monkeypatch.setattr(li, "_LOCALES_DIR", tmp_path / "locales")
        li._translation_cache.clear()

        trans = li.get_translation("fr")
        assert trans.gettext("Quit") == "Quitter"

        li._translation_cache.clear()

    def test_unknown_lang_falls_back_to_identity(self):
        trans = get_translation("xx")
        # NullTranslations returns the msgid unchanged
        assert trans.gettext("Quit") == "Quit"

    def test_none_uses_current_locale(self):
        import safari_writer.locale_info as li

        trans = get_translation(None)
        # Just verify we get a translation object back
        assert hasattr(trans, "gettext")

    def test_result_is_cached(self):
        t1 = get_translation("fr")
        t2 = get_translation("fr")
        assert t1 is t2
