"""Tests for syntax highlighting (spec 10 §9–10)."""

import pytest
from rich.text import Text

from safari_writer.file_types import resolve_file_profile
from safari_writer.syntax_highlight import (
    Highlighter,
    create_highlighter,
    highlight_buffer,
    highlight_line,
)


class TestHighlighterCreation:
    def test_create_for_python(self):
        profile = resolve_file_profile("main.py")
        h = create_highlighter(profile)
        assert isinstance(h, Highlighter)

    def test_create_for_plain_text(self):
        profile = resolve_file_profile("notes.txt")
        h = create_highlighter(profile)
        assert isinstance(h, Highlighter)

    def test_create_for_sfw(self):
        profile = resolve_file_profile("doc.sfw")
        h = create_highlighter(profile)
        assert isinstance(h, Highlighter)


class TestPygmentsHighlighting:
    """Code files get Pygments syntax highlighting."""

    def test_python_returns_text_objects(self):
        profile = resolve_file_profile("main.py")
        lines = ["def hello():", "    print('world')"]
        result = highlight_buffer(lines, profile)
        assert len(result) == 2
        assert all(isinstance(t, Text) for t in result)

    def test_python_has_spans(self):
        profile = resolve_file_profile("main.py")
        result = highlight_line("def hello():", profile)
        assert isinstance(result, Text)
        # Pygments should produce spans for keywords
        assert len(result._spans) > 0

    def test_json_highlighting(self):
        profile = resolve_file_profile("config.json")
        result = highlight_line('{"key": "value"}', profile)
        assert isinstance(result, Text)
        assert len(result._spans) > 0

    def test_markdown_highlighting(self):
        profile = resolve_file_profile("readme.md")
        result = highlight_line("# Heading", profile)
        assert isinstance(result, Text)


class TestEnglishHighlighting:
    """English prose files get function-word and punctuation styling."""

    def test_english_text_returns_text(self):
        profile = resolve_file_profile("chapter.en.txt")
        result = highlight_line("The quick brown fox.", profile)
        assert isinstance(result, Text)

    def test_english_text_has_spans(self):
        profile = resolve_file_profile("chapter.en.txt")
        result = highlight_line(
            "The quick brown fox jumped over the lazy dog.", profile
        )
        # Should have spans for function words (the, over) and punctuation
        assert len(result._spans) > 0

    def test_editorial_markers_highlighted(self):
        profile = resolve_file_profile("chapter.en.txt")
        result = highlight_line("TODO fix this bug", profile)
        assert len(result._spans) > 0

    def test_urls_highlighted(self):
        profile = resolve_file_profile("chapter.en.txt")
        result = highlight_line("Visit https://example.com today", profile)
        assert len(result._spans) > 0

    def test_numbers_highlighted(self):
        profile = resolve_file_profile("chapter.en.txt")
        result = highlight_line("The year 2024 was good", profile)
        assert len(result._spans) > 0

    def test_english_markdown_has_heading_style(self):
        profile = resolve_file_profile("chapter.en.md")
        result = highlight_line("# Introduction", profile)
        assert len(result._spans) > 0

    def test_english_markdown_has_list_style(self):
        profile = resolve_file_profile("chapter.en.md")
        result = highlight_line("- item one", profile)
        assert len(result._spans) > 0


class TestPlainTextHighlighting:
    """Plain text files get no highlighting."""

    def test_plain_text_no_spans(self):
        profile = resolve_file_profile("notes.txt")
        result = highlight_line("Just some plain text.", profile)
        assert isinstance(result, Text)
        assert len(result._spans) == 0


class TestSafariWriterHighlighting:
    """SFW files return unstyled text (Safari Writer handles its own rendering)."""

    def test_sfw_no_spans(self):
        profile = resolve_file_profile("doc.sfw")
        result = highlight_line("Some text with \\Bformatting", profile)
        assert isinstance(result, Text)
        assert len(result._spans) == 0


class TestHighlighterCache:
    def test_cache_returns_same_result(self):
        profile = resolve_file_profile("main.py")
        h = create_highlighter(profile)
        lines = ["x = 1"]
        r1 = h.highlight_buffer(lines)
        r2 = h.highlight_buffer(lines)
        assert r1 is r2  # Same object, not recomputed

    def test_invalidate_forces_recompute(self):
        profile = resolve_file_profile("main.py")
        h = create_highlighter(profile)
        lines = ["x = 1"]
        r1 = h.highlight_buffer(lines)
        h.invalidate()
        r2 = h.highlight_buffer(lines)
        assert r1 is not r2  # Different object after invalidation


class TestEditorPlainModeFormatGuard:
    """Formatting commands are rejected in plain mode."""

    def test_insert_control_rejected_in_plain_mode(self):
        from unittest.mock import MagicMock, patch
        from safari_writer.state import AppState
        from safari_writer.screens.editor import EditorArea, CTRL_BOLD

        state = AppState()
        state.filename = "test.txt"
        state.update_file_profile()
        state.buffer = ["hello world"]

        ed = EditorArea(state)
        mock_screen = MagicMock()
        with patch.object(
            type(ed), "screen", new_callable=lambda: property(lambda self: mock_screen)
        ):
            ed._insert_control(CTRL_BOLD)

        # Buffer should be unchanged (no control char inserted)
        assert state.buffer == ["hello world"]
        # Should have shown a message
        mock_screen.set_message.assert_called_once()
        assert ".sfw" in mock_screen.set_message.call_args[0][0]

    def test_insert_control_allowed_in_sfw_mode(self):
        from unittest.mock import MagicMock, patch
        from safari_writer.state import AppState
        from safari_writer.screens.editor import EditorArea, CTRL_BOLD

        state = AppState()
        state.filename = "test.sfw"
        state.update_file_profile()
        state.buffer = ["hello world"]
        state.cursor_col = 5

        ed = EditorArea(state)
        mock_screen = MagicMock()
        with patch.object(
            type(ed), "screen", new_callable=lambda: property(lambda self: mock_screen)
        ):
            ed._insert_control(CTRL_BOLD)

        # Buffer should have control char inserted
        assert CTRL_BOLD in state.buffer[0]
