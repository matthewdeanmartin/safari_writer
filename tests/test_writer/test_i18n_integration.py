"""Integration tests for i18n Levels 0-2."""

from __future__ import annotations

from pathlib import Path

import pytest

from safari_writer.document_io import (load_document_buffer, load_sfw_language,
                                       serialize_document_buffer)
from safari_writer.format_codec import (decode_sfw, encode_sfw,
                                        extract_sfw_metadata,
                                        inject_sfw_metadata)
from safari_writer.proofing import make_checker
from safari_writer.state import AppState

# ---------------------------------------------------------------------------
# Metadata header round-trip (Level 1)
# ---------------------------------------------------------------------------


class TestSfwMetadata:
    def test_extract_lang(self):
        text = "%%lang: de_DE\nHello world"
        meta, body = extract_sfw_metadata(text)
        assert meta == {"lang": "de_DE"}
        assert body == "Hello world"

    def test_extract_multiple_headers(self):
        text = "%%lang: fr_FR\n%%author: Test\nBody text"
        meta, body = extract_sfw_metadata(text)
        assert meta["lang"] == "fr_FR"
        assert meta["author"] == "Test"
        assert body == "Body text"

    def test_extract_no_headers(self):
        text = "Just plain text\nWith lines"
        meta, body = extract_sfw_metadata(text)
        assert meta == {}
        assert body == text

    def test_inject_empty_metadata(self):
        body = "Hello"
        assert inject_sfw_metadata({}, body) == body

    def test_inject_lang(self):
        body = "Hello"
        result = inject_sfw_metadata({"lang": "es_ES"}, body)
        assert result.startswith("%%lang: es_ES\n")
        assert result.endswith("Hello")

    def test_round_trip(self):
        meta = {"lang": "pt_BR"}
        body = encode_sfw(["Hello \\B bold"])
        full = inject_sfw_metadata(meta, body)
        extracted_meta, extracted_body = extract_sfw_metadata(full)
        assert extracted_meta == meta
        assert decode_sfw(extracted_body) == decode_sfw(body)


# ---------------------------------------------------------------------------
# Document I/O with language (Level 1)
# ---------------------------------------------------------------------------


class TestDocumentLanguageIO:
    def test_load_sfw_language(self, tmp_path: Path):
        doc = tmp_path / "test.sfw"
        doc.write_text("%%lang: de_DE\nHello world")
        assert load_sfw_language(doc) == "de_DE"

    def test_load_sfw_no_language(self, tmp_path: Path):
        doc = tmp_path / "test.sfw"
        doc.write_text("Hello world")
        assert load_sfw_language(doc) == ""

    def test_load_non_sfw_returns_empty(self, tmp_path: Path):
        doc = tmp_path / "test.txt"
        doc.write_text("Hello world")
        assert load_sfw_language(doc) == ""

    def test_serialize_with_language(self, tmp_path: Path):
        path = tmp_path / "test.sfw"
        text = serialize_document_buffer(["Hello"], path, doc_language="fr_FR")
        assert "%%lang: fr_FR" in text

    def test_serialize_without_language(self, tmp_path: Path):
        path = tmp_path / "test.sfw"
        text = serialize_document_buffer(["Hello"], path, doc_language="")
        assert "%%" not in text

    def test_serialize_plain_ignores_language(self, tmp_path: Path):
        path = tmp_path / "test.txt"
        text = serialize_document_buffer(["Hello"], path, doc_language="fr_FR")
        assert "%%" not in text

    def test_load_buffer_with_metadata_header(self, tmp_path: Path):
        doc = tmp_path / "test.sfw"
        doc.write_text("%%lang: de_DE\nHello world")
        buf = load_document_buffer(doc)
        # The metadata line should NOT appear in the buffer
        assert "%%lang" not in buf[0]
        assert "Hello world" in buf[0]


# ---------------------------------------------------------------------------
# AppState.doc_language (Level 1)
# ---------------------------------------------------------------------------


class TestAppStateLanguage:
    def test_default_language_empty(self):
        state = AppState()
        assert state.doc_language == ""

    def test_set_language(self):
        state = AppState()
        state.doc_language = "es_ES"
        assert state.doc_language == "es_ES"


# ---------------------------------------------------------------------------
# make_checker language parameter (Level 1)
# ---------------------------------------------------------------------------


class TestMakeCheckerLang:
    def test_default_returns_checker_or_none(self):
        # Should not raise regardless of installed dictionaries
        result = make_checker()
        assert result is None or hasattr(result, "check")

    def test_explicit_lang_returns_checker_or_none(self):
        result = make_checker("en_US")
        assert result is None or hasattr(result, "check")

    def test_nonexistent_lang_returns_none(self):
        result = make_checker("zz_ZZ")
        assert result is None
