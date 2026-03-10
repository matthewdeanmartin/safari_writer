"""Tests for Safari Chat app, default help loading, and transcript export."""

from __future__ import annotations

from pathlib import Path

from safari_chat.app import SafariChatApp, _DEFAULT_HELP
from safari_chat.engine import parse_document
from safari_chat.state import SafariChatState


class TestDefaultHelp:
    def test_default_help_file_exists(self) -> None:
        assert _DEFAULT_HELP.is_file()

    def test_default_help_parses(self) -> None:
        text = _DEFAULT_HELP.read_text(encoding="utf-8")
        chunks = parse_document(text)
        assert len(chunks) > 10  # should have many sections

    def test_default_help_has_safari_writer_content(self) -> None:
        text = _DEFAULT_HELP.read_text(encoding="utf-8")
        assert "Safari Writer" in text

    def test_default_help_has_safari_dos_content(self) -> None:
        text = _DEFAULT_HELP.read_text(encoding="utf-8")
        assert "Safari DOS" in text

    def test_default_help_has_safari_chat_content(self) -> None:
        text = _DEFAULT_HELP.read_text(encoding="utf-8")
        assert "Safari Chat" in text


class TestSafariChatAppInit:
    def test_no_args_loads_default_help(self) -> None:
        app = SafariChatApp()
        assert app.state.document_path == _DEFAULT_HELP
        assert len(app.state.chunks) > 0

    def test_explicit_none_loads_default(self) -> None:
        app = SafariChatApp(document_path=None)
        assert len(app.state.chunks) > 0

    def test_nonexistent_file_falls_back_to_default(self) -> None:
        fake = Path("/totally/fake/path/nope.md")
        app = SafariChatApp(document_path=fake)
        assert app.state.document_path == _DEFAULT_HELP
        assert len(app.state.chunks) > 0

    def test_explicit_document_used(self, tmp_path: Path) -> None:
        doc = tmp_path / "custom.md"
        doc.write_text("# Custom\n\nContent here.\n", encoding="utf-8")
        app = SafariChatApp(document_path=doc)
        assert app.state.document_path == doc
        assert len(app.state.chunks) == 1
        assert app.state.chunks[0].heading == "Custom"

    def test_state_initialized(self) -> None:
        app = SafariChatApp()
        assert isinstance(app.state, SafariChatState)
        assert app.state.conversation == []
        assert app.state.distress_score == 0.0


class TestLoadDocument:
    def test_load_replaces_chunks(self, tmp_path: Path) -> None:
        app = SafariChatApp()
        original_count = len(app.state.chunks)
        assert original_count > 0

        doc = tmp_path / "new.md"
        doc.write_text("# Only One\n\nSection.\n", encoding="utf-8")
        app.load_document(doc)
        assert len(app.state.chunks) == 1
        assert app.state.document_path == doc

    def test_load_updates_path(self, tmp_path: Path) -> None:
        app = SafariChatApp()
        doc = tmp_path / "test.md"
        doc.write_text("# Test\n\nHello.\n", encoding="utf-8")
        app.load_document(doc)
        assert app.state.document_path == doc


class TestExportTranscript:
    def test_empty_transcript(self, tmp_path: Path) -> None:
        app = SafariChatApp()
        out = tmp_path / "transcript.txt"
        app.export_transcript(out)
        assert out.read_text(encoding="utf-8") == ""

    def test_transcript_with_conversation(self, tmp_path: Path) -> None:
        app = SafariChatApp()
        app.state.add_node("user", "Hello there")
        app.state.add_node("bot", "Hi! How can I help?")
        out = tmp_path / "transcript.txt"
        app.export_transcript(out)
        content = out.read_text(encoding="utf-8")
        assert "USER> Hello there" in content
        assert " BOT> Hi! How can I help?" in content

    def test_transcript_preserves_order(self, tmp_path: Path) -> None:
        app = SafariChatApp()
        app.state.add_node("user", "First")
        app.state.add_node("bot", "Second")
        app.state.add_node("user", "Third")
        out = tmp_path / "transcript.txt"
        app.export_transcript(out)
        content = out.read_text(encoding="utf-8")
        lines = content.strip().split("\n")
        assert len(lines) == 3
        assert "First" in lines[0]
        assert "Second" in lines[1]
        assert "Third" in lines[2]


class TestChatMain:
    def test_main_with_valid_doc(self, tmp_path: Path) -> None:
        from safari_chat.main import parse_args

        doc = tmp_path / "help.md"
        doc.write_text("# Help\n\nContent.\n", encoding="utf-8")
        args = parse_args([str(doc)])
        assert args.document == str(doc)

    def test_main_no_args(self) -> None:
        from safari_chat.main import parse_args

        args = parse_args([])
        assert args.document is None

    def test_main_nonexistent_doc_returns_error(self, tmp_path: Path) -> None:
        from safari_chat.main import main

        result = main([str(tmp_path / "nonexistent.md")])
        assert result == 1
