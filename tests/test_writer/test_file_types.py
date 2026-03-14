"""Tests for file type awareness (spec 10)."""

import pytest

from safari_writer.file_types import (
    FileProfile,
    HighlightProfile,
    StorageMode,
    resolve_file_profile,
)


class TestStorageModeResolution:
    """Storage mode is determined solely by the final suffix."""

    def test_sfw_is_formatted(self):
        p = resolve_file_profile("draft.sfw")
        assert p.storage_mode == StorageMode.FORMATTED

    def test_sfw_case_insensitive(self):
        p = resolve_file_profile("draft.SFW")
        assert p.storage_mode == StorageMode.FORMATTED

    def test_txt_is_plain(self):
        p = resolve_file_profile("draft.txt")
        assert p.storage_mode == StorageMode.PLAIN

    def test_py_is_plain(self):
        p = resolve_file_profile("script.py")
        assert p.storage_mode == StorageMode.PLAIN

    def test_md_is_plain(self):
        p = resolve_file_profile("outline.md")
        assert p.storage_mode == StorageMode.PLAIN

    def test_en_md_is_plain(self):
        p = resolve_file_profile("chapter.en.md")
        assert p.storage_mode == StorageMode.PLAIN

    def test_no_extension_is_plain(self):
        p = resolve_file_profile("README")
        assert p.storage_mode == StorageMode.PLAIN

    def test_json_is_plain(self):
        p = resolve_file_profile("config.json")
        assert p.storage_mode == StorageMode.PLAIN


class TestHighlightProfileResolution:
    """Highlight profile from suffix, with optional language overlay."""

    def test_sfw_profile(self):
        p = resolve_file_profile("letter.sfw")
        assert p.highlight_profile == HighlightProfile.SAFARI_WRITER

    def test_txt_profile(self):
        p = resolve_file_profile("notes.txt")
        assert p.highlight_profile == HighlightProfile.PLAIN_TEXT

    def test_md_profile(self):
        p = resolve_file_profile("outline.md")
        assert p.highlight_profile == HighlightProfile.MARKDOWN

    def test_py_profile(self):
        p = resolve_file_profile("script.py")
        assert p.highlight_profile == HighlightProfile.PYTHON

    def test_js_profile(self):
        p = resolve_file_profile("app.js")
        assert p.highlight_profile == HighlightProfile.JAVASCRIPT

    def test_ts_profile(self):
        p = resolve_file_profile("app.ts")
        assert p.highlight_profile == HighlightProfile.TYPESCRIPT

    def test_json_profile(self):
        p = resolve_file_profile("config.json")
        assert p.highlight_profile == HighlightProfile.JSON

    def test_toml_profile(self):
        p = resolve_file_profile("pyproject.toml")
        assert p.highlight_profile == HighlightProfile.TOML

    def test_yaml_profile(self):
        p = resolve_file_profile("config.yaml")
        assert p.highlight_profile == HighlightProfile.YAML

    def test_yml_profile(self):
        p = resolve_file_profile("config.yml")
        assert p.highlight_profile == HighlightProfile.YAML

    def test_ini_profile(self):
        p = resolve_file_profile("setup.ini")
        assert p.highlight_profile == HighlightProfile.INI

    def test_cfg_profile(self):
        p = resolve_file_profile("setup.cfg")
        assert p.highlight_profile == HighlightProfile.INI

    def test_bas_profile(self):
        p = resolve_file_profile("prog.bas")
        assert p.highlight_profile == HighlightProfile.SAFARI_BASIC

    def test_asm_profile(self):
        p = resolve_file_profile("prog.asm")
        assert p.highlight_profile == HighlightProfile.SAFARI_ASM

    def test_prg_profile(self):
        p = resolve_file_profile("prog.prg")
        assert p.highlight_profile == HighlightProfile.SAFARI_BASE

    def test_unknown_extension_falls_back(self):
        p = resolve_file_profile("data.xyz")
        assert p.highlight_profile == HighlightProfile.PLAIN_TEXT

    def test_no_extension_is_plain(self):
        p = resolve_file_profile("Makefile")
        assert p.highlight_profile == HighlightProfile.PLAIN_TEXT


class TestEnglishOverlays:
    """Natural-language overlays via penultimate suffix."""

    def test_en_txt_is_english_text(self):
        p = resolve_file_profile("chapter.en.txt")
        assert p.highlight_profile == HighlightProfile.ENGLISH_TEXT
        assert p.storage_mode == StorageMode.PLAIN

    def test_en_md_is_english_markdown(self):
        p = resolve_file_profile("chapter.en.md")
        assert p.highlight_profile == HighlightProfile.ENGLISH_MARKDOWN
        assert p.storage_mode == StorageMode.PLAIN

    def test_unsupported_lang_overlay_falls_back(self):
        p = resolve_file_profile("chapter.fr.txt")
        assert p.highlight_profile == HighlightProfile.PLAIN_TEXT

    def test_en_with_unknown_base_gets_english_text(self):
        # .en.xyz → unknown base maps to plain-text, then .en overlay applies
        p = resolve_file_profile("chapter.en.xyz")
        assert p.highlight_profile == HighlightProfile.ENGLISH_TEXT


class TestFileProfileProperties:
    """FileProfile convenience properties."""

    def test_allows_formatting_for_sfw(self):
        p = resolve_file_profile("doc.sfw")
        assert p.allows_formatting_codes is True

    def test_no_formatting_for_txt(self):
        p = resolve_file_profile("doc.txt")
        assert p.allows_formatting_codes is False

    def test_is_code_for_python(self):
        p = resolve_file_profile("main.py")
        assert p.is_code is True

    def test_is_code_false_for_txt(self):
        p = resolve_file_profile("notes.txt")
        assert p.is_code is False

    def test_is_english_for_en_txt(self):
        p = resolve_file_profile("chapter.en.txt")
        assert p.is_english is True

    def test_not_english_for_py(self):
        p = resolve_file_profile("main.py")
        assert p.is_english is False

    def test_pygments_lexer_for_python(self):
        p = resolve_file_profile("main.py")
        assert p.pygments_lexer == "python"

    def test_pygments_lexer_for_basic(self):
        p = resolve_file_profile("prog.bas")
        assert p.pygments_lexer == "basic"

    def test_pygments_lexer_for_asm(self):
        p = resolve_file_profile("prog.asm")
        assert p.pygments_lexer == "asm"

    def test_pygments_lexer_for_base(self):
        p = resolve_file_profile("prog.prg")
        assert p.pygments_lexer == "foxpro"

    def test_pygments_lexer_none_for_txt(self):
        p = resolve_file_profile("notes.txt")
        assert p.pygments_lexer is None


class TestDisplayNames:
    """Display names for status bar."""

    def test_sfw_display_name(self):
        assert resolve_file_profile("doc.sfw").display_name == "Safari Writer"

    def test_python_display_name(self):
        assert resolve_file_profile("main.py").display_name == "Python"

    def test_basic_display_name(self):
        assert resolve_file_profile("prog.bas").display_name == "Safari Basic"

    def test_asm_display_name(self):
        assert resolve_file_profile("prog.asm").display_name == "Safari ASM"

    def test_base_display_name(self):
        assert resolve_file_profile("prog.prg").display_name == "Safari Base"

    def test_english_text_display_name(self):
        assert resolve_file_profile("ch.en.txt").display_name == "English Text"

    def test_english_markdown_display_name(self):
        assert resolve_file_profile("ch.en.md").display_name == "English Markdown"

    def test_plain_text_display_name(self):
        assert resolve_file_profile("notes.txt").display_name == "Plain Text"


class TestAppStateFileProfile:
    """AppState file profile integration."""

    def test_default_state_is_sfw(self):
        from safari_writer.state import AppState

        state = AppState()
        assert state.storage_mode == StorageMode.FORMATTED
        assert state.allows_formatting is True

    def test_state_update_profile(self):
        from safari_writer.state import AppState

        state = AppState()
        state.filename = "script.py"
        state.update_file_profile()
        assert state.storage_mode == StorageMode.PLAIN
        assert state.highlight_profile == HighlightProfile.PYTHON
        assert state.allows_formatting is False


class TestDocumentIOFileProfile:
    """document_io integration with file profiles."""

    def test_load_state_sets_profile(self, tmp_path):
        from safari_writer.document_io import load_document_state

        f = tmp_path / "test.py"
        f.write_text("print('hello')")
        state = load_document_state(f)
        assert state.storage_mode == StorageMode.PLAIN
        assert state.highlight_profile == HighlightProfile.PYTHON

    def test_load_sfw_sets_formatted(self, tmp_path):
        from safari_writer.document_io import load_document_state
        from safari_writer.format_codec import encode_sfw

        f = tmp_path / "test.sfw"
        f.write_text(encode_sfw(["Hello \\Bworld"]))
        state = load_document_state(f)
        assert state.storage_mode == StorageMode.FORMATTED

    def test_load_plain_strips_controls(self, tmp_path):
        from safari_writer.document_io import load_document_state

        f = tmp_path / "test.txt"
        f.write_text("Hello\x01world")
        state = load_document_state(f)
        # Control chars should have been stripped for plain files
        assert "\x01" not in state.buffer[0]
        assert state.storage_mode == StorageMode.PLAIN
