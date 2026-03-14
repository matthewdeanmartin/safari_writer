"""Unit tests for Safari Chat retrieval across all modules."""

from __future__ import annotations

from pathlib import Path
import pytest

from safari_chat.engine import parse_document, retrieve_chunks
from safari_chat.state import TopicChunk

@pytest.fixture(scope="module")
def help_chunks() -> list[TopicChunk]:
    """Load and parse the full default help document."""
    help_path = Path(__file__).parent.parent.parent / "safari_chat" / "default_help.md"
    text = help_path.read_text(encoding="utf-8")
    return parse_document(text)

def assert_module_retrieval(query: str, chunks: list[TopicChunk], expected_keywords: list[str]):
    """Helper to assert that a query returns a chunk containing expected keywords in heading."""
    results = retrieve_chunks(query, chunks)
    assert len(results) > 0, f"No results found for query: {query}"
    
    top_chunk = results[0][0]
    heading = top_chunk.heading.lower()
    
    found = any(kw.lower() in heading or kw.lower() in top_chunk.body.lower() for kw in expected_keywords)
    assert found, f"Query '{query}' returned '{top_chunk.heading}', which does not match expected keywords {expected_keywords}"

class TestSafariWriterRetrieval:
    def test_writer_save(self, help_chunks):
        assert_module_retrieval("how do I save my file", help_chunks, ["Save", "Document Actions"])

    def test_writer_bold(self, help_chunks):
        assert_module_retrieval("how to make text bold", help_chunks, ["Formatting", "Bold"])

    def test_writer_margins(self, help_chunks):
        assert_module_retrieval("change the page margins", help_chunks, ["Global Format", "Margins"])

class TestSafariDOSRetrieval:
    def test_dos_garbage(self, help_chunks):
        assert_module_retrieval("recover a deleted file", help_chunks, ["Garbage", "DOS"])

    def test_dos_rename(self, help_chunks):
        assert_module_retrieval("how to rename a file", help_chunks, ["Rename", "DOS"])

    def test_dos_favorites(self, help_chunks):
        assert_module_retrieval("how to bookmark a folder", help_chunks, ["Favorites", "DOS"])

class TestSafariFedRetrieval:
    def test_fed_compose(self, help_chunks):
        assert_module_retrieval("write a new mastodon post", help_chunks, ["Compose", "Fed"])

    def test_fed_accounts(self, help_chunks):
        assert_module_retrieval("how to add multiple accounts", help_chunks, ["Accounts", "Fed"])

    def test_fed_boost(self, help_chunks):
        assert_module_retrieval("how to boost a post", help_chunks, ["Boost", "Fed"])

class TestSafariChatRetrieval:
    def test_chat_commands(self, help_chunks):
        assert_module_retrieval("what are the slash commands", help_chunks, ["Commands", "Chat"])

    def test_chat_distress(self, help_chunks):
        assert_module_retrieval("what is the distress meter", help_chunks, ["Distress", "Chat"])

    def test_chat_safety(self, help_chunks):
        assert_module_retrieval("is this bot a therapist", help_chunks, ["Safety", "Chat"])

class TestSafariASMRetrieval:
    def test_asm_run(self, help_chunks):
        assert_module_retrieval("how to run an asm file", help_chunks, ["ASM", "Running"])

    def test_asm_syntax(self, help_chunks):
        assert_module_retrieval("what is the assembly syntax", help_chunks, ["ASM", "Syntax"])

    def test_asm_integration(self, help_chunks):
        assert_module_retrieval("automate writer with asm", help_chunks, ["ASM", "Integration"])

class TestSafariBaseRetrieval:
    def test_base_load(self, help_chunks):
        assert_module_retrieval("open a sqlite database", help_chunks, ["Base", "Databases"])

    def test_base_ops(self, help_chunks):
        assert_module_retrieval("how to browse records", help_chunks, ["Base", "Operations"])

    def test_base_export(self, help_chunks):
        assert_module_retrieval("export table to csv", help_chunks, ["Base", "Export"])

class TestSafariBasicRetrieval:
    def test_basic_embedded(self, help_chunks):
        assert_module_retrieval("what is safari basic used for", help_chunks, ["Basic", "Embedded"])

    def test_basic_macros(self, help_chunks):
        assert_module_retrieval("how to write basic macros", help_chunks, ["Basic", "Macros"])

    def test_basic_difference(self, help_chunks):
        assert_module_retrieval("difference between basic and repl", help_chunks, ["Basic", "REPL"])

class TestSafariREPLRetrieval:
    def test_repl_start(self, help_chunks):
        assert_module_retrieval("start the interactive basic shell", help_chunks, ["REPL", "BASIC"])

    def test_repl_load(self, help_chunks):
        assert_module_retrieval("load a bas file into repl", help_chunks, ["REPL", "Loading"])

    def test_repl_handoff(self, help_chunks):
        assert_module_retrieval("edit basic code in writer", help_chunks, ["REPL", "Handoff"])

class TestSafariReaderRetrieval:
    def test_reader_nav(self, help_chunks):
        assert_module_retrieval("how to scroll in the reader", help_chunks, ["Reader", "Navigation"])

    def test_reader_search(self, help_chunks):
        assert_module_retrieval("find text in a book", help_chunks, ["Reader", "Search"])

    def test_reader_handoff(self, help_chunks):
        assert_module_retrieval("quote a passage in writer", help_chunks, ["Reader", "Handoff"])

class TestSafariSlidesRetrieval:
    def test_slides_start(self, help_chunks):
        assert_module_retrieval("how to start a presentation", help_chunks, ["Slides", "Presentation"])

    def test_slides_nav(self, help_chunks):
        assert_module_retrieval("navigate between slides", help_chunks, ["Slides", "Navigation"])

    def test_slides_format(self, help_chunks):
        assert_module_retrieval("how to format slidemd", help_chunks, ["Slides", "SlideMD"])

class TestSafariViewRetrieval:
    def test_view_modes(self, help_chunks):
        assert_module_retrieval("what are the retro render modes", help_chunks, ["View", "Render"])

    def test_view_tui(self, help_chunks):
        assert_module_retrieval("how to use the image browser", help_chunks, ["View", "TUI"])

    def test_view_cli(self, help_chunks):
        assert_module_retrieval("render an image from command line", help_chunks, ["View", "CLI"])
