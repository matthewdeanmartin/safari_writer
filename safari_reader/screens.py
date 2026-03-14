"""Textual screens for Safari Reader."""

from __future__ import annotations

from datetime import datetime, timezone

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Vertical
from textual.screen import Screen
from textual.widgets import Input, Label, ListItem, ListView, Static
from textual.worker import Worker, WorkerState

from safari_reader.services import (add_book_to_library, delete_book,
                                    download_gutenberg_text, format_book_text,
                                    gutenberg_book_detail, import_local_file,
                                    load_library, open_book, save_library,
                                    save_reading_state, search_gutenberg,
                                    top_gutenberg)
from safari_reader.state import Bookmark, BookMeta, SafariReaderState

__all__ = [
    "SafariReaderMainMenuScreen",
    "SafariReaderLibraryScreen",
    "SafariReaderScreen",
    "SafariReaderCatalogScreen",
    "SafariReaderBookDetailScreen",
    "SafariReaderBookmarksScreen",
    "SafariReaderHelpScreen",
    "SafariReaderSearchScreen",
]


# ── Shared styling ───────────────────────────────────────────────

_STATUS_BAR_STYLE = "bold reverse"
_FOOTER_STYLE = "reverse"


def _progress_bar(percent: float, width: int = 20) -> str:
    filled = int(percent / 100 * width)
    return "[" + "#" * filled + "-" * (width - filled) + "]"


# ── Main Menu ────────────────────────────────────────────────────


class MenuItem(Static):
    """Menu item with selection highlighting."""

    def __init__(self, key: str, label: str, action: str) -> None:
        self.key_char = key
        self.label_text = label
        self.action_name = action
        super().__init__("", classes="menu-item")
        self._is_selected = False

    def set_selected(self, selected: bool) -> None:
        self._is_selected = selected
        self._update_markup()

    def _update_markup(self) -> None:
        markup = f"[bold underline]{self.key_char}[/]{self.label_text}"
        if self._is_selected:
            markup = f"[reverse]{markup}[/reverse]"
        self.update(markup)

    def on_mount(self) -> None:
        self._update_markup()


class SafariReaderMainMenuScreen(Screen):
    """Boot / splash screen for Safari Reader."""

    MENU_ITEMS = [
        ("R", "esume last book", "resume"),
        ("L", "ibrary", "library"),
        ("C", "atalog (online)", "catalog"),
        ("H", "elp", "help"),
        ("S", "ettings", "settings"),
        ("Q", "uit", "quit"),
    ]

    BINDINGS = [
        Binding("r", "menu('resume')", "Resume", show=False),
        Binding("l", "menu('library')", "Library", show=False),
        Binding("c", "menu('catalog')", "Catalog", show=False),
        Binding("h", "menu('help')", "Help", show=False),
        Binding("s", "menu('settings')", "Settings", show=False),
        Binding("q", "menu('quit')", "Quit", show=False),
        Binding("escape", "menu('quit')", "Quit", show=False),
        # Arrow navigation
        Binding("up", "cursor_up", "Up", show=False),
        Binding("down", "cursor_down", "Down", show=False),
        Binding("enter", "activate", "Activate", show=False),
    ]

    def __init__(self, state: SafariReaderState) -> None:
        super().__init__()
        self.state = state
        self._selected_index = 0
        self._menu_widgets: list[MenuItem] = []
        load_library(state)

    def compose(self) -> ComposeResult:
        last_book = ""
        for b in sorted(
            self.state.library,
            key=lambda x: x.last_opened or "",
            reverse=True,
        ):
            if b.last_opened:
                last_book = b.title
                break

        yield Static(
            f"[{_STATUS_BAR_STYLE}]  SAFARI READER  v1.0  [/{_STATUS_BAR_STYLE}]"
        )
        yield Static("")
        with Center():
            yield Static(
                "╔══════════════════════════════════════╗\n"
                "║                                      ║\n"
                "║         S A F A R I                   ║\n"
                "║         R E A D E R                   ║\n"
                "║                                      ║\n"
                "║   A keyboard-first book reader       ║\n"
                "║   with AtariWriter-era charm         ║\n"
                "║                                      ║\n"
                "╚══════════════════════════════════════╝"
            )
        yield Static("")
        if last_book:
            yield Static(f"  Last read: {last_book}")
            yield Static("")

        with Vertical(id="reader-menu-container"):
            for key, label, action in self.MENU_ITEMS:
                yield MenuItem(key, label, action)

        yield Static("")
        yield Static(
            f"[{_FOOTER_STYLE}]"
            "  R=Resume  L=Library  C=Catalog  H=Help  Q=Quit  "
            f"[/{_FOOTER_STYLE}]"
        )

    def on_mount(self) -> None:
        self._menu_widgets = list(self.query(MenuItem))
        self._refresh_menu()

    def _refresh_menu(self) -> None:
        for i, widget in enumerate(self._menu_widgets):
            widget.set_selected(i == self._selected_index)

    def action_cursor_up(self) -> None:
        if self._selected_index > 0:
            self._selected_index -= 1
            self._refresh_menu()

    def action_cursor_down(self) -> None:
        if self._selected_index < len(self._menu_widgets) - 1:
            self._selected_index += 1
            self._refresh_menu()

    def action_activate(self) -> None:
        if 0 <= self._selected_index < len(self._menu_widgets):
            action = self._menu_widgets[self._selected_index].action_name
            self.action_menu(action)

    def action_menu(self, choice: str) -> None:
        if choice == "library":
            self.app.push_screen(SafariReaderLibraryScreen(self.state))  # type: ignore[arg-type]
        elif choice == "catalog":
            self.app.push_screen(SafariReaderCatalogScreen(self.state))  # type: ignore[arg-type]
        elif choice == "resume":
            self._resume_last()
        elif choice == "help":
            self.app.push_screen(SafariReaderHelpScreen(self.state))  # type: ignore[arg-type]
        elif choice == "settings":
            self.app.push_screen(SafariReaderSettingsScreen(self.state))  # type: ignore[arg-type]
        elif choice == "quit":
            _quit_reader(self)

    def _resume_last(self) -> None:
        candidates = sorted(
            self.state.library,
            key=lambda x: x.last_opened or "",
            reverse=True,
        )
        for b in candidates:
            if b.last_opened and b.file_path and b.file_path.exists():
                open_book(b, self.state)
                self.app.push_screen(SafariReaderScreen(self.state))  # type: ignore[arg-type]
                return
        self.notify("NO BOOK TO RESUME", severity="warning")


# ── Library Screen ───────────────────────────────────────────────


class SafariReaderLibraryScreen(Screen):
    """Local bookshelf / downloaded books."""

    BINDINGS = [
        Binding("r", "read_selected", "Read", show=False),
        Binding("enter", "read_selected", "Read", show=False),
        Binding("i", "import_file", "Import", show=False),
        Binding("d", "details", "Details", show=False),
        Binding("a", "archive", "Archive", show=False),
        Binding("c", "catalog", "Catalog", show=False),
        Binding("escape", "go_back", "Back", show=False),
        Binding("q", "go_back", "Back", show=False),
    ]

    def __init__(self, state: SafariReaderState) -> None:
        super().__init__()
        self.state = state

    def compose(self) -> ComposeResult:
        yield Static(
            f"[{_STATUS_BAR_STYLE}]"
            "  LIBRARY                                              "
            f"[/{_STATUS_BAR_STYLE}]"
        )
        yield Static("")
        if not self.state.library:
            yield Static(
                "  No books in library. Press [C] for Online Catalog or [I] to Import."
            )
        else:
            items = []
            for i, book in enumerate(self.state.library):
                progress = (
                    f"{book.progress_percent:.0f}%" if book.progress_percent else "NEW"
                )
                author = book.author[:30] if book.author else "Unknown"
                label = f"  {i + 1:>3}. {book.title:<50} {author:<32} {progress:>5}"
                items.append(ListItem(Label(label), id=f"book-{i}"))
            yield ListView(*items, id="library-list")
        yield Static("")
        yield Static(
            f"[{_FOOTER_STYLE}]"
            "  R/Enter=Read  I=Import  D=Details  A=Archive  C=Catalog  Q=Back  "
            f"[/{_FOOTER_STYLE}]"
        )

    def _selected_book(self) -> BookMeta | None:
        """Return the currently highlighted book, or None."""
        matches = self.query("#library-list")
        if not matches:
            return None
        lv = matches.first(ListView)
        if lv.index is not None and 0 <= lv.index < len(self.state.library):
            return self.state.library[lv.index]
        return None

    def action_read_selected(self) -> None:
        book = self._selected_book()
        if book is None:
            return
        open_book(book, self.state)
        self.app.push_screen(SafariReaderScreen(self.state))  # type: ignore[arg-type]

    def action_import_file(self) -> None:
        self.app.push_screen(SafariReaderImportScreen(self.state))  # type: ignore[arg-type]

    def action_details(self) -> None:
        book = self._selected_book()
        if book is None:
            return
        self.app.push_screen(SafariReaderBookDetailScreen(self.state, book))  # type: ignore[arg-type]

    def action_archive(self) -> None:
        book = self._selected_book()
        if book is None:
            return
        delete_book(book, self.state)
        self.app.pop_screen()
        self.app.push_screen(SafariReaderLibraryScreen(self.state))  # type: ignore[arg-type]

    def action_catalog(self) -> None:
        self.app.push_screen(SafariReaderCatalogScreen(self.state))  # type: ignore[arg-type]

    def action_go_back(self) -> None:
        self.app.pop_screen()


# ── Reader Screen ────────────────────────────────────────────────


class SafariReaderScreen(Screen):
    """The main reading experience."""

    BINDINGS = [
        Binding("pagedown", "next_page", "Next", show=False),
        Binding("space", "next_page", "Next", show=False),
        Binding("pageup", "prev_page", "Prev", show=False),
        Binding("home", "chapter_start", "ChStart", show=False),
        Binding("end", "chapter_end", "ChEnd", show=False),
        Binding("ctrl+pagedown", "next_chapter", "NextCh", show=False),
        Binding("ctrl+pageup", "prev_chapter", "PrevCh", show=False),
        Binding("slash", "search", "Search", show=False),
        Binding("b", "bookmark", "Bookmark", show=False),
        Binding("g", "goto", "GoTo", show=False),
        Binding("h", "help", "Help", show=False),
        Binding("l", "library", "Library", show=False),
        Binding("plus_sign", "bigger", "Bigger", show=False),
        Binding("equals_sign", "bigger", "Bigger", show=False),
        Binding("hyphen_minus", "smaller", "Smaller", show=False),
        Binding("right_square_bracket", "more_spacing", "MoreSpace", show=False),
        Binding("left_square_bracket", "less_spacing", "LessSpace", show=False),
        Binding("t", "toggle_toc", "TOC", show=False),
        Binding("escape", "reader_menu", "Menu", show=False),
        Binding("q", "reader_quit", "Back", show=False),
    ]

    def __init__(self, state: SafariReaderState) -> None:
        super().__init__()
        self.state = state
        self._page_lines: list[str] = []
        self._total_lines: int = 0
        self._current_line: int = 0

    def compose(self) -> ComposeResult:
        book = self.state.current_book
        title = book.title[:40] if book else "NO BOOK"
        chapter = self._current_chapter_name()
        percent = self._percent()
        yield Static(
            f"[{_STATUS_BAR_STYLE}]"
            f"  SAFARI READER | {title} | {chapter} | {percent:.0f}% READ  "
            f"[/{_STATUS_BAR_STYLE}]",
            id="reader-status",
        )
        yield Static("", id="reader-body")
        yield Static(
            f"[{_FOOTER_STYLE}]"
            "  PgDn/Space=Next  PgUp=Prev  /=Find  B=Bookmark  G=GoTo  "
            "+/-=Size  T=TOC  Esc=Menu  Q=Back  "
            f"[/{_FOOTER_STYLE}]",
            id="reader-footer",
        )

    def on_mount(self) -> None:
        self._prepare_pages()
        self._render_page()

    def _prepare_pages(self) -> None:
        settings = self.state.settings
        try:
            term_width = self.size.width
        except Exception:
            term_width = 120
        term_width = max(40, term_width)
        # Text scale increases margins rather than shrinking the terminal
        extra_margin = [0, 2, 6, 12]
        base_margin = [2, 4, 6, 8]
        margin = (
            base_margin[min(settings.margin_width, 3)]
            + extra_margin[min(settings.text_scale, 3)]
        )
        width = max(40, term_width - 2)  # leave a little outer gutter
        text = format_book_text(self.state.current_text, width=width, margin=margin)
        spacing = settings.line_spacing
        if spacing >= 2:
            lines = text.split("\n")
            spaced: list[str] = []
            for line in lines:
                spaced.append(line)
                if spacing == 3:
                    spaced.append("")
                    spaced.append("")
                else:
                    spaced.append("")
            text = "\n".join(spaced)
        self._page_lines = text.split("\n")
        self._total_lines = len(self._page_lines)
        if self.state.current_position > 0 and self.state.current_text:
            char_ratio = self.state.current_position / max(
                len(self.state.current_text), 1
            )
            self._current_line = int(char_ratio * self._total_lines)

    def _page_height(self) -> int:
        try:
            return max(5, self.size.height - 4)
        except Exception:
            return 20

    def _render_page(self) -> None:
        height = self._page_height()
        start = self._current_line
        end = min(start + height, self._total_lines)
        page_text = "\n".join(self._page_lines[start:end])
        body = self.query_one("#reader-body", Static)
        body.update(page_text)
        self._sync_position()
        self._update_status()

    def _sync_position(self) -> None:
        if self._total_lines > 0:
            char_ratio = self._current_line / max(self._total_lines, 1)
            self.state.current_position = int(char_ratio * len(self.state.current_text))
            if self.state.current_book:
                total = self.state.current_book.total_chars or len(
                    self.state.current_text
                )
                self.state.current_book.progress_percent = (
                    self.state.current_position / max(total, 1) * 100
                )
                self.state.current_book.current_position = self.state.current_position

    def _update_status(self) -> None:
        book = self.state.current_book
        title = book.title[:40] if book else "NO BOOK"
        chapter = self._current_chapter_name()
        percent = self._percent()
        status = self.query_one("#reader-status", Static)
        status.update(
            f"[{_STATUS_BAR_STYLE}]"
            f"  SAFARI READER | {title} | {chapter} | {percent:.0f}% READ  "
            f"[/{_STATUS_BAR_STYLE}]"
        )

    def _percent(self) -> float:
        if self._total_lines == 0:
            return 0.0
        return self._current_line / max(self._total_lines - 1, 1) * 100

    def _current_chapter_name(self) -> str:
        if not self.state.current_chapters:
            return ""
        pos = self.state.current_position
        chapter = self.state.current_chapters[0][0]
        for name, offset in self.state.current_chapters:
            if offset <= pos:
                chapter = name
            else:
                break
        return chapter[:30]

    def action_next_page(self) -> None:
        height = self._page_height()
        self._current_line = min(
            self._current_line + height, max(self._total_lines - height, 0)
        )
        self._render_page()

    def action_prev_page(self) -> None:
        height = self._page_height()
        self._current_line = max(self._current_line - height, 0)
        self._render_page()

    def action_next_chapter(self) -> None:
        pos = self.state.current_position
        for _name, offset in self.state.current_chapters:
            if offset > pos + 10:
                char_ratio = offset / max(len(self.state.current_text), 1)
                self._current_line = int(char_ratio * self._total_lines)
                self._render_page()
                return

    def action_prev_chapter(self) -> None:
        pos = self.state.current_position
        prev_offset = 0
        for _name, offset in self.state.current_chapters:
            if offset >= pos - 10:
                break
            prev_offset = offset
        char_ratio = prev_offset / max(len(self.state.current_text), 1)
        self._current_line = int(char_ratio * self._total_lines)
        self._render_page()

    def action_chapter_start(self) -> None:
        pos = self.state.current_position
        current_offset = 0
        for _name, offset in self.state.current_chapters:
            if offset <= pos:
                current_offset = offset
            else:
                break
        char_ratio = current_offset / max(len(self.state.current_text), 1)
        self._current_line = int(char_ratio * self._total_lines)
        self._render_page()

    def action_chapter_end(self) -> None:
        pos = self.state.current_position
        for _name, offset in self.state.current_chapters:
            if offset > pos:
                char_ratio = max(0, offset - 100) / max(len(self.state.current_text), 1)
                self._current_line = int(char_ratio * self._total_lines)
                self._render_page()
                return
        self._current_line = max(0, self._total_lines - self._page_height())
        self._render_page()

    def action_search(self) -> None:
        self.app.push_screen(SafariReaderSearchScreen(self.state))  # type: ignore[arg-type]

    def action_bookmark(self) -> None:
        now = datetime.now(tz=timezone.utc).isoformat()
        excerpt = self.state.current_text[
            self.state.current_position : self.state.current_position + 60
        ].replace("\n", " ")
        bm = Bookmark(
            name=f"Bookmark {len(self.state.bookmarks) + 1}",
            position=self.state.current_position,
            chapter=self._current_chapter_name(),
            excerpt=excerpt,
            created=now,
        )
        self.state.bookmarks.append(bm)
        save_reading_state(self.state)
        self.notify("BOOKMARK SET")

    def action_goto(self) -> None:
        self.app.push_screen(SafariReaderGoToScreen(self.state))  # type: ignore[arg-type]

    def action_help(self) -> None:
        self.app.push_screen(SafariReaderHelpScreen(self.state))  # type: ignore[arg-type]

    def action_library(self) -> None:
        save_reading_state(self.state)
        save_library(self.state)
        self.app.pop_screen()

    def action_bigger(self) -> None:
        if self.state.settings.text_scale < 3:
            self.state.settings.text_scale += 1
            self._prepare_pages()
            self._render_page()

    def action_smaller(self) -> None:
        if self.state.settings.text_scale > 0:
            self.state.settings.text_scale -= 1
            self._prepare_pages()
            self._render_page()

    def action_more_spacing(self) -> None:
        if self.state.settings.line_spacing < 3:
            self.state.settings.line_spacing += 1
            self._prepare_pages()
            self._render_page()

    def action_less_spacing(self) -> None:
        if self.state.settings.line_spacing > 1:
            self.state.settings.line_spacing -= 1
            self._prepare_pages()
            self._render_page()

    def action_toggle_toc(self) -> None:
        if self.state.current_chapters:
            self.app.push_screen(SafariReaderTOCScreen(self.state))  # type: ignore[arg-type]

    def action_reader_menu(self) -> None:
        save_reading_state(self.state)
        save_library(self.state)
        self.app.pop_screen()

    def action_reader_quit(self) -> None:
        save_reading_state(self.state)
        save_library(self.state)
        self.app.pop_screen()


# ── Table of Contents ────────────────────────────────────────────


class SafariReaderTOCScreen(Screen):
    """Chapter / table of contents navigation."""

    BINDINGS = [
        Binding("enter", "jump", "Jump", show=False),
        Binding("escape", "go_back", "Back", show=False),
        Binding("q", "go_back", "Back", show=False),
    ]

    def __init__(self, state: SafariReaderState) -> None:
        super().__init__()
        self.state = state

    def compose(self) -> ComposeResult:
        yield Static(
            f"[{_STATUS_BAR_STYLE}]  TABLE OF CONTENTS  [/{_STATUS_BAR_STYLE}]"
        )
        yield Static("")
        items = []
        for i, (name, _offset) in enumerate(self.state.current_chapters):
            items.append(ListItem(Label(f"  {i + 1:>3}. {name}"), id=f"toc-{i}"))
        yield ListView(*items, id="toc-list")
        yield Static("")
        yield Static(f"[{_FOOTER_STYLE}]  Enter=Jump  Q/Esc=Back  [/{_FOOTER_STYLE}]")

    def action_jump(self) -> None:
        matches = self.query("#toc-list")
        if not matches:
            return
        lv = matches.first(ListView)
        if lv.index is not None and 0 <= lv.index < len(self.state.current_chapters):
            _name, offset = self.state.current_chapters[lv.index]
            self.state.current_position = offset
            self.app.pop_screen()

    def action_go_back(self) -> None:
        self.app.pop_screen()


# ── Catalog Screen ───────────────────────────────────────────────


class SafariReaderCatalogScreen(Screen):
    """Browse and search the Project Gutenberg catalog."""

    BINDINGS = [
        Binding("s", "search", "Search", show=False),
        Binding("t", "top", "Top Books", show=False),
        Binding("enter", "select_book", "Select", show=False),
        Binding("d", "download", "Download", show=False),
        Binding("escape", "go_back", "Back", show=False),
        Binding("q", "go_back", "Back", show=False),
    ]

    def __init__(self, state: SafariReaderState) -> None:
        super().__init__()
        self.state = state

    def compose(self) -> ComposeResult:
        yield Static(
            f"[{_STATUS_BAR_STYLE}]"
            "  ONLINE CATALOG — PROJECT GUTENBERG  "
            f"[/{_STATUS_BAR_STYLE}]"
        )
        yield Static("", id="catalog-status")
        yield Vertical(id="catalog-body")
        yield Static("")
        yield Static(
            f"[{_FOOTER_STYLE}]"
            "  S=Search  T=Top Books  Enter=Select  D=Download  Q=Back  "
            f"[/{_FOOTER_STYLE}]"
        )

    def on_mount(self) -> None:
        self._rebuild_list()

    def _rebuild_list(self) -> None:
        """Rebuild the catalog list from current results."""
        body = self.query_one("#catalog-body", Vertical)
        body.remove_children()
        if self.state.catalog_results:
            items = []
            for i, r in enumerate(self.state.catalog_results):
                title = r.get("title", "Untitled")[:50]
                author = r.get("author", "")[:30]
                dl = r.get("download_count", "")
                label = f"  {i + 1:>3}. {title:<50} {author:<32} DL:{dl}"
                items.append(ListItem(Label(label), id=f"cat-{i}"))
            body.mount(ListView(*items, id="catalog-list"))
        else:
            body.mount(Static("  Press [S] to Search or [T] for Top Downloads."))

    def _set_status(self, text: str) -> None:
        self.query_one("#catalog-status", Static).update(text)

    def action_search(self) -> None:
        self.app.push_screen(  # type: ignore[arg-type]
            SafariReaderCatalogSearchScreen(self.state, self)
        )

    def action_top(self) -> None:
        self._set_status("  FETCHING TOP BOOKS...")
        self.run_worker(self._fetch_top, thread=True)

    def _fetch_top(self) -> list[dict[str, str]]:
        return top_gutenberg()

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.state == WorkerState.SUCCESS:
            result = event.worker.result
            if isinstance(result, list):
                # Search or top results
                self.state.catalog_results = result
                count = len(result)
                self._set_status(f"  {count} BOOK{'S' if count != 1 else ''} FOUND")
                self._rebuild_list()
            elif isinstance(result, dict):
                # Detail fetch completed
                if result:
                    self.app.push_screen(  # type: ignore[arg-type]
                        SafariReaderCatalogDetailScreen(self.state, result)
                    )
                else:
                    self._set_status("  BOOK DETAILS NOT AVAILABLE")
            elif isinstance(result, str):
                # Download completed — result is title or empty on failure
                if result:
                    self._set_status(f"  ADDED: {result}")
                    self.notify(f"ADDED: {result}")
                else:
                    self._set_status("  DOWNLOAD FAILED")
                    self.notify("DOWNLOAD FAILED", severity="error")
        elif event.state == WorkerState.ERROR:
            self._set_status("  NETWORK ERROR — TRY AGAIN")

    def _selected_catalog_item(self) -> dict[str, str] | None:
        """Return the currently highlighted catalog result, or None."""
        matches = self.query("#catalog-list")
        if not matches:
            return None
        lv = matches.first(ListView)
        if lv.index is not None and 0 <= lv.index < len(self.state.catalog_results):
            return self.state.catalog_results[lv.index]
        return None

    def action_select_book(self) -> None:
        result = self._selected_catalog_item()
        if result is None:
            return
        book_id = result.get("id", "")
        if book_id:
            self._set_status(f"  LOADING DETAILS FOR PG#{book_id}...")
            self.run_worker(lambda: gutenberg_book_detail(book_id), thread=True)

    def action_download(self) -> None:
        result = self._selected_catalog_item()
        if result is None:
            return
        book_id = result.get("id", "")
        if not book_id:
            self.notify("NO BOOK ID", severity="error")
            return
        self._set_status(f"  DOWNLOADING PG#{book_id}...")
        self.run_worker(
            lambda: self._do_download_work(book_id), thread=True, group="download"
        )

    def _do_download_work(self, book_id: str) -> str:
        """Run download in a worker thread. Returns a status message."""
        path = download_gutenberg_text(book_id, self.state.library_dir)
        if path is None:
            return ""
        detail = gutenberg_book_detail(book_id)
        add_book_to_library(detail, path, self.state)
        return detail.get("title", "Book")

    def _on_download_done(self, event: Worker.StateChanged) -> None:
        # Handled by on_worker_state_changed via string result
        pass

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def do_search(self, query: str) -> None:
        """Called by the search screen to trigger a search."""
        self.state.catalog_query = query
        self._set_status(f"  SEARCHING: {query}...")
        self.run_worker(lambda: search_gutenberg(query), thread=True)


# ── Catalog Search ───────────────────────────────────────────────


class SafariReaderCatalogSearchScreen(Screen):
    """Form-entry search screen for the Gutenberg catalog."""

    BINDINGS = [
        Binding("escape", "go_back", "Back", show=False),
    ]

    def __init__(
        self,
        state: SafariReaderState,
        catalog_screen: SafariReaderCatalogScreen | None = None,
    ) -> None:
        super().__init__()
        self.state = state
        self._catalog_screen = catalog_screen

    def compose(self) -> ComposeResult:
        yield Static(f"[{_STATUS_BAR_STYLE}]  CATALOG SEARCH  [/{_STATUS_BAR_STYLE}]")
        yield Static("")
        yield Static("  Enter search query (title, author, or subject):")
        yield Static("")
        yield Input(
            placeholder="Search...",
            id="catalog-search-input",
        )
        yield Static("")
        yield Static(f"[{_FOOTER_STYLE}]  Enter=Search  Esc=Cancel  [/{_FOOTER_STYLE}]")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        query = event.value.strip()
        if not query:
            return
        self.app.pop_screen()
        if self._catalog_screen is not None:
            self._catalog_screen.do_search(query)

    def action_go_back(self) -> None:
        self.app.pop_screen()


# ── Catalog Detail ───────────────────────────────────────────────


class SafariReaderCatalogDetailScreen(Screen):
    """Metadata detail for a catalog item."""

    BINDINGS = [
        Binding("d", "download", "Download", show=False),
        Binding("enter", "download", "Download", show=False),
        Binding("escape", "go_back", "Back", show=False),
        Binding("q", "go_back", "Back", show=False),
    ]

    def __init__(self, state: SafariReaderState, detail: dict[str, str]) -> None:
        super().__init__()
        self.state = state
        self.detail = detail

    def compose(self) -> ComposeResult:
        d = self.detail
        yield Static(f"[{_STATUS_BAR_STYLE}]  BOOK DETAILS  [/{_STATUS_BAR_STYLE}]")
        yield Static("")
        yield Static(f"  Title:      {d.get('title', 'Untitled')}")
        yield Static(f"  Author:     {d.get('author', 'Unknown')}")
        yield Static(f"  Language:   {d.get('language', '')}")
        yield Static(f"  Subjects:   {d.get('subjects', '')}")
        yield Static(f"  Downloads:  {d.get('download_count', '')}")
        yield Static(f"  Source:     Project Gutenberg #{d.get('id', '')}")
        has_txt = "Yes" if d.get("txt_url") else "No"
        yield Static(f"  Text avail: {has_txt}")
        yield Static("")
        yield Static(
            f"[{_FOOTER_STYLE}]  D/Enter=Download  Q/Esc=Back  [/{_FOOTER_STYLE}]"
        )

    def action_download(self) -> None:
        book_id = self.detail.get("id", "")
        if not book_id:
            self.notify("NO BOOK ID", severity="error")
            return
        self.notify(f"DOWNLOADING PG#{book_id}...")
        detail = self.detail
        self.run_worker(lambda: self._download_work(book_id, detail), thread=True)

    def _download_work(self, book_id: str, detail: dict[str, str]) -> str:
        path = download_gutenberg_text(book_id, self.state.library_dir)
        if path is None:
            return ""
        add_book_to_library(detail, path, self.state)
        return detail.get("title", "Book")

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.state == WorkerState.SUCCESS:
            title = event.worker.result
            if title:
                self.notify(f"ADDED: {title}")
                self.app.pop_screen()
            else:
                self.notify("DOWNLOAD FAILED", severity="error")
        elif event.state == WorkerState.ERROR:
            self.notify("DOWNLOAD FAILED — NETWORK ERROR", severity="error")

    def action_go_back(self) -> None:
        self.app.pop_screen()


# ── Book Detail (Library) ────────────────────────────────────────


class SafariReaderBookDetailScreen(Screen):
    """Detailed view of a book in the local library."""

    BINDINGS = [
        Binding("r", "read", "Read", show=False),
        Binding("enter", "read", "Read", show=False),
        Binding("a", "archive", "Archive", show=False),
        Binding("escape", "go_back", "Back", show=False),
        Binding("q", "go_back", "Back", show=False),
    ]

    def __init__(self, state: SafariReaderState, book: BookMeta) -> None:
        super().__init__()
        self.state = state
        self.book = book

    def compose(self) -> ComposeResult:
        b = self.book
        yield Static(f"[{_STATUS_BAR_STYLE}]  BOOK DETAILS  [/{_STATUS_BAR_STYLE}]")
        yield Static("")
        yield Static(f"  Title:      {b.title}")
        yield Static(f"  Author:     {b.author or 'Unknown'}")
        yield Static(f"  Language:   {b.language}")
        yield Static(
            f"  Source:     {b.source} {'#' + b.source_id if b.source_id else ''}"
        )
        yield Static(f"  Format:     {b.format}")
        size_kb = b.size_bytes / 1024 if b.size_bytes else 0
        yield Static(f"  Size:       {size_kb:.0f} KB")
        yield Static(f"  Added:      {b.added[:10] if b.added else 'Unknown'}")
        yield Static(
            f"  Last read:  {b.last_opened[:10] if b.last_opened else 'Never'}"
        )
        yield Static(
            f"  Progress:   {b.progress_percent:.0f}% {_progress_bar(b.progress_percent)}"
        )
        if b.subjects:
            yield Static(f"  Subjects:   {'; '.join(b.subjects[:5])}")
        yield Static("")
        yield Static(
            f"[{_FOOTER_STYLE}]"
            "  R/Enter=Read  A=Archive  Q/Esc=Back  "
            f"[/{_FOOTER_STYLE}]"
        )

    def action_read(self) -> None:
        open_book(self.book, self.state)
        self.app.push_screen(SafariReaderScreen(self.state))  # type: ignore[arg-type]

    def action_archive(self) -> None:
        delete_book(self.book, self.state)
        self.notify(f"ARCHIVED: {self.book.title}")
        self.app.pop_screen()

    def action_go_back(self) -> None:
        self.app.pop_screen()


# ── Import Screen ────────────────────────────────────────────────


class SafariReaderImportScreen(Screen):
    """Import a local file into the library."""

    BINDINGS = [
        Binding("escape", "go_back", "Back", show=False),
    ]

    def __init__(self, state: SafariReaderState) -> None:
        super().__init__()
        self.state = state

    def compose(self) -> ComposeResult:
        yield Static(f"[{_STATUS_BAR_STYLE}]  IMPORT FILE  [/{_STATUS_BAR_STYLE}]")
        yield Static("")
        yield Static("  Enter path to a .txt, .md, or .html file:")
        yield Static("")
        yield Input(placeholder="File path...", id="import-path-input")
        yield Static("")
        yield Static(f"[{_FOOTER_STYLE}]  Enter=Import  Esc=Cancel  [/{_FOOTER_STYLE}]")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        from pathlib import Path

        path_str = event.value.strip()
        if not path_str:
            return
        path = Path(path_str).expanduser().resolve()
        if not path.exists():
            self.notify("FILE NOT FOUND", severity="error")
            return
        if not path.is_file():
            self.notify("NOT A FILE", severity="error")
            return
        try:
            meta = import_local_file(path, self.state)
            self.notify(f"IMPORTED: {meta.title}")
            self.app.pop_screen()
        except Exception as exc:
            self.notify(f"IMPORT ERROR: {exc}", severity="error")

    def action_go_back(self) -> None:
        self.app.pop_screen()


# ── Search Inside Book ───────────────────────────────────────────


class SafariReaderSearchScreen(Screen):
    """Find text inside the current book."""

    BINDINGS = [
        Binding("escape", "go_back", "Back", show=False),
    ]

    def __init__(self, state: SafariReaderState) -> None:
        super().__init__()
        self.state = state

    def compose(self) -> ComposeResult:
        yield Static(f"[{_STATUS_BAR_STYLE}]  FIND IN BOOK  [/{_STATUS_BAR_STYLE}]")
        yield Static("")
        yield Static("  Search for:")
        yield Static("")
        yield Input(
            placeholder="Find text...",
            value=self.state.last_search,
            id="search-input",
        )
        yield Static("")
        yield Static(f"[{_FOOTER_STYLE}]  Enter=Find  Esc=Cancel  [/{_FOOTER_STYLE}]")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        query = event.value.strip()
        if not query:
            return
        self.state.last_search = query
        text = self.state.current_text
        pos = text.lower().find(query.lower(), self.state.current_position + 1)
        if pos == -1:
            pos = text.lower().find(query.lower())
        if pos == -1:
            self.notify("NOT FOUND", severity="warning")
            self.app.pop_screen()
            return
        self.state.current_position = pos
        self.notify(f"FOUND AT POSITION {pos}")
        self.app.pop_screen()

    def action_go_back(self) -> None:
        self.app.pop_screen()


# ── Go To Screen ─────────────────────────────────────────────────


class SafariReaderGoToScreen(Screen):
    """Jump to a percentage, chapter, or bookmark."""

    MENU_ITEMS = [
        ("P", "ercentage", "percent"),
        ("C", "hapter", "chapter"),
        ("B", "ookmark", "bookmarks"),
    ]

    BINDINGS = [
        Binding("p", "goto_percent", "Percent", show=False),
        Binding("c", "goto_chapter", "Chapter", show=False),
        Binding("b", "goto_bookmarks", "Bookmarks", show=False),
        Binding("escape", "go_back", "Back", show=False),
        Binding("q", "go_back", "Back", show=False),
        # Arrow navigation
        Binding("up", "cursor_up", "Up", show=False),
        Binding("down", "cursor_down", "Down", show=False),
        Binding("enter", "activate", "Activate", show=False),
    ]

    def __init__(self, state: SafariReaderState) -> None:
        super().__init__()
        self.state = state
        self._selected_index = 0
        self._menu_widgets: list[MenuItem] = []

    def compose(self) -> ComposeResult:
        yield Static(f"[{_STATUS_BAR_STYLE}]  GO TO  [/{_STATUS_BAR_STYLE}]")
        yield Static("")
        with Vertical(id="goto-menu-container"):
            for key, label, action in self.MENU_ITEMS:
                # Add bookmark count to label if it's the bookmarks option
                display_label = label
                if action == "bookmarks":
                    display_label += f" ({len(self.state.bookmarks)} saved)"
                yield MenuItem(key, display_label, action)
        yield Static("")
        yield Static(
            f"[{_FOOTER_STYLE}]"
            "  P=Percent  C=Chapter  B=Bookmarks  Q/Esc=Back  "
            f"[/{_FOOTER_STYLE}]"
        )

    def on_mount(self) -> None:
        self._menu_widgets = list(self.query(MenuItem))
        self._refresh_menu()

    def _refresh_menu(self) -> None:
        for i, widget in enumerate(self._menu_widgets):
            widget.set_selected(i == self._selected_index)

    def action_cursor_up(self) -> None:
        if self._selected_index > 0:
            self._selected_index -= 1
            self._refresh_menu()

    def action_cursor_down(self) -> None:
        if self._selected_index < len(self._menu_widgets) - 1:
            self._selected_index += 1
            self._refresh_menu()

    def action_activate(self) -> None:
        if 0 <= self._selected_index < len(self._menu_widgets):
            action = self._menu_widgets[self._selected_index].action_name
            if action == "percent":
                self.action_goto_percent()
            elif action == "chapter":
                self.action_goto_chapter()
            elif action == "bookmarks":
                self.action_goto_bookmarks()

    def action_goto_percent(self) -> None:
        self.app.push_screen(SafariReaderGoToPercentScreen(self.state))  # type: ignore[arg-type]

    def action_goto_chapter(self) -> None:
        if self.state.current_chapters:
            self.app.pop_screen()
            self.app.push_screen(SafariReaderTOCScreen(self.state))  # type: ignore[arg-type]

    def action_goto_bookmarks(self) -> None:
        if self.state.bookmarks:
            self.app.push_screen(SafariReaderBookmarksScreen(self.state))  # type: ignore[arg-type]
        else:
            self.notify("NO BOOKMARKS SET")

    def action_go_back(self) -> None:
        self.app.pop_screen()


class SafariReaderGoToPercentScreen(Screen):
    """Jump to a position by percentage."""

    BINDINGS = [
        Binding("escape", "go_back", "Back", show=False),
    ]

    def __init__(self, state: SafariReaderState) -> None:
        super().__init__()
        self.state = state

    def compose(self) -> ComposeResult:
        yield Static(f"[{_STATUS_BAR_STYLE}]  GO TO PERCENTAGE  [/{_STATUS_BAR_STYLE}]")
        yield Static("")
        yield Static("  Enter percentage (0-100):")
        yield Static("")
        yield Input(placeholder="50", id="percent-input")
        yield Static("")
        yield Static(f"[{_FOOTER_STYLE}]  Enter=Go  Esc=Cancel  [/{_FOOTER_STYLE}]")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        try:
            pct = float(event.value.strip())
        except ValueError:
            self.notify("INVALID NUMBER", severity="error")
            return
        pct = max(0.0, min(100.0, pct))
        total = len(self.state.current_text)
        self.state.current_position = int(pct / 100.0 * total)
        self.app.pop_screen()
        self.app.pop_screen()

    def action_go_back(self) -> None:
        self.app.pop_screen()


# ── Bookmarks Screen ─────────────────────────────────────────────


class SafariReaderBookmarksScreen(Screen):
    """View and jump to bookmarks."""

    BINDINGS = [
        Binding("enter", "jump", "Jump", show=False),
        Binding("d", "delete_bm", "Delete", show=False),
        Binding("escape", "go_back", "Back", show=False),
        Binding("q", "go_back", "Back", show=False),
    ]

    def __init__(self, state: SafariReaderState) -> None:
        super().__init__()
        self.state = state

    def compose(self) -> ComposeResult:
        yield Static(f"[{_STATUS_BAR_STYLE}]  BOOKMARKS  [/{_STATUS_BAR_STYLE}]")
        yield Static("")
        if not self.state.bookmarks:
            yield Static("  No bookmarks set.")
        else:
            items = []
            for i, bm in enumerate(self.state.bookmarks):
                label = (
                    f"  {i + 1:>3}. {bm.name:<25} {bm.chapter:<30} {bm.excerpt[:50]}"
                )
                items.append(ListItem(Label(label), id=f"bm-{i}"))
            yield ListView(*items, id="bookmarks-list")
        yield Static("")
        yield Static(
            f"[{_FOOTER_STYLE}]  Enter=Jump  D=Delete  Q/Esc=Back  [/{_FOOTER_STYLE}]"
        )

    def _selected_bookmark_index(self) -> int | None:
        """Return the index of the highlighted bookmark, or None."""
        matches = self.query("#bookmarks-list")
        if not matches:
            return None
        lv = matches.first(ListView)
        if lv.index is not None and 0 <= lv.index < len(self.state.bookmarks):
            return lv.index
        return None

    def action_jump(self) -> None:
        idx = self._selected_bookmark_index()
        if idx is None:
            return
        bm = self.state.bookmarks[idx]
        self.state.current_position = bm.position
        self.app.pop_screen()

    def action_delete_bm(self) -> None:
        idx = self._selected_bookmark_index()
        if idx is None:
            return
        del self.state.bookmarks[idx]
        save_reading_state(self.state)
        self.app.pop_screen()
        self.app.push_screen(SafariReaderBookmarksScreen(self.state))  # type: ignore[arg-type]

    def action_go_back(self) -> None:
        self.app.pop_screen()


# ── Settings Screen ──────────────────────────────────────────────


class SafariReaderSettingsScreen(Screen):
    """Reading display preferences."""

    BINDINGS = [
        Binding("1", "set_scale_0", "Compact", show=False),
        Binding("2", "set_scale_1", "Normal", show=False),
        Binding("3", "set_scale_2", "Large", show=False),
        Binding("4", "set_scale_3", "XLarge", show=False),
        Binding("s", "toggle_spacing", "Spacing", show=False),
        Binding("m", "toggle_margin", "Margin", show=False),
        Binding("p", "toggle_page_mode", "PageMode", show=False),
        Binding("x", "style_switcher", "Theme", show=False),
        Binding("escape", "go_back", "Back", show=False),
        Binding("q", "go_back", "Back", show=False),
        # Arrow navigation
        Binding("up", "cursor_up", "Up", show=False),
        Binding("down", "cursor_down", "Down", show=False),
        Binding("enter", "activate", "Activate", show=False),
    ]

    def __init__(self, state: SafariReaderState) -> None:
        super().__init__()
        self.state = state
        self._selected_index = 0
        self._menu_widgets: list[MenuItem] = []

    def _get_menu_items(self) -> list[tuple[str, str, str]]:
        s = self.state.settings
        scale_names = ["Compact", "Normal", "Large", "X-Large"]
        spacing_names = {1: "Single", 2: "1.5x", 3: "Double"}
        margin_names = {0: "Narrow", 1: "Normal", 2: "Wide"}
        mode = "Page" if s.page_mode else "Flow"

        return [
            ("1", f" Text size: {scale_names[s.text_scale]} (Press 1-4)", "scale"),
            (
                "S",
                f" Line spacing: {spacing_names.get(s.line_spacing, 'Single')}",
                "spacing",
            ),
            ("M", f" Margins: {margin_names.get(s.margin_width, 'Normal')}", "margin"),
            ("P", f" Read mode: {mode}", "mode"),
            ("X", " Theme Switcher", "theme"),
        ]

    def compose(self) -> ComposeResult:
        yield Static(
            f"[{_STATUS_BAR_STYLE}]  READING PREFERENCES  [/{_STATUS_BAR_STYLE}]"
        )
        yield Static("")
        with Vertical(id="settings-menu-container"):
            for key, label, action in self._get_menu_items():
                yield MenuItem(key, label, action)
        yield Static("")
        yield Static(
            f"[{_FOOTER_STYLE}]"
            "  1-4=Size  S=Spacing  M=Margin  P=Mode  X=Theme  Q/Esc=Back  "
            f"[/{_FOOTER_STYLE}]"
        )

    def on_mount(self) -> None:
        self._menu_widgets = list(self.query(MenuItem))
        self._refresh_menu()

    def _refresh_menu(self) -> None:
        for i, widget in enumerate(self._menu_widgets):
            widget.set_selected(i == self._selected_index)

    def action_cursor_up(self) -> None:
        if self._selected_index > 0:
            self._selected_index -= 1
            self._refresh_menu()

    def action_cursor_down(self) -> None:
        if self._selected_index < len(self._menu_widgets) - 1:
            self._selected_index += 1
            self._refresh_menu()

    def action_activate(self) -> None:
        if 0 <= self._selected_index < len(self._menu_widgets):
            action = self._menu_widgets[self._selected_index].action_name
            if action == "scale":
                # Cycle scale if activated via enter
                self.state.settings.text_scale = (
                    self.state.settings.text_scale + 1
                ) % 4
                self._refresh_screen()
            elif action == "spacing":
                self.action_toggle_spacing()
            elif action == "margin":
                self.action_toggle_margin()
            elif action == "mode":
                self.action_toggle_page_mode()
            elif action == "theme":
                self.action_style_switcher()

    def _refresh_screen(self) -> None:
        self.app.pop_screen()
        self.app.push_screen(SafariReaderSettingsScreen(self.state))  # type: ignore[arg-type]

    def action_set_scale_0(self) -> None:
        self.state.settings.text_scale = 0
        self._refresh_screen()

    def action_set_scale_1(self) -> None:
        self.state.settings.text_scale = 1
        self._refresh_screen()

    def action_set_scale_2(self) -> None:
        self.state.settings.text_scale = 2
        self._refresh_screen()

    def action_set_scale_3(self) -> None:
        self.state.settings.text_scale = 3
        self._refresh_screen()

    def action_toggle_spacing(self) -> None:
        s = self.state.settings
        s.line_spacing = (s.line_spacing % 3) + 1
        self._refresh_screen()

    def action_toggle_margin(self) -> None:
        s = self.state.settings
        s.margin_width = (s.margin_width + 1) % 3
        self._refresh_screen()

    def action_toggle_page_mode(self) -> None:
        self.state.settings.page_mode = not self.state.settings.page_mode
        self._refresh_screen()

    def action_style_switcher(self) -> None:
        from safari_writer.screens.style_switcher import StyleSwitcherScreen

        self.app.push_screen(StyleSwitcherScreen(self.app.theme))

    def action_go_back(self) -> None:
        self.app.pop_screen()


# ── Help Screen ──────────────────────────────────────────────────


class SafariReaderHelpScreen(Screen):
    """Quick reference / help screen."""

    BINDINGS = [
        Binding("escape", "go_back", "Back", show=False),
        Binding("q", "go_back", "Back", show=False),
    ]

    def __init__(self, state: SafariReaderState) -> None:
        super().__init__()
        self.state = state

    def compose(self) -> ComposeResult:
        yield Static(
            f"[{_STATUS_BAR_STYLE}]  SAFARI READER — QUICK HELP  [/{_STATUS_BAR_STYLE}]"
        )
        yield Static("")
        yield Static(
            "  ── READER COMMANDS ──\n"
            "\n"
            "  PgDn / Space    Next page\n"
            "  PgUp            Previous page\n"
            "  Ctrl+PgDn       Next chapter\n"
            "  Ctrl+PgUp       Previous chapter\n"
            "  Home            Start of chapter\n"
            "  End             End of chapter\n"
            "  /               Search text\n"
            "  B               Set bookmark\n"
            "  G               Go to (percent / chapter / bookmark)\n"
            "  T               Table of contents\n"
            "  + / =           Bigger text\n"
            "  - (hyphen)      Smaller text\n"
            "  ]               More line spacing\n"
            "  [               Less line spacing\n"
            "  Esc             Back / Menu\n"
            "  Q               Back / Quit\n"
            "\n"
            "  ── LIBRARY ──\n"
            "\n"
            "  R / Enter       Read selected book\n"
            "  I               Import local file\n"
            "  D               Book details\n"
            "  A               Archive (remove) book\n"
            "  C               Online catalog\n"
            "\n"
            "  ── CATALOG ──\n"
            "\n"
            "  S               Search Gutenberg\n"
            "  T               Top downloads\n"
            "  Enter           View book details\n"
            "  D               Download selected\n"
            "\n"
            "  ── GENERAL ──\n"
            "\n"
            "  H               Help (this screen)\n"
            "  L               Return to library\n"
            "  Q / Esc         Back / Quit\n"
        )
        yield Static("")
        yield Static(f"[{_FOOTER_STYLE}]  Press Q or Esc to return  [/{_FOOTER_STYLE}]")

    def action_go_back(self) -> None:
        self.app.pop_screen()


# ── Helper ───────────────────────────────────────────────────────


def _quit_reader(screen: Screen) -> None:
    """Exit the reader back to the parent app or standalone."""
    app = screen.app
    if hasattr(app, "quit_reader"):
        app.quit_reader()  # type: ignore[attr-defined]
    else:
        app.pop_screen()
