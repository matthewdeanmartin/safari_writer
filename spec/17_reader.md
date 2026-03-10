Below is a product/specification document for a **terminal book reader** with the **UI feel of AtariWriter-era software**, but designed for a modern machine and keyboard. I’ve grounded the historical bits in AtariWriter’s menu-driven feel and Atari DOS’s menu model, and I’ve used Project Gutenberg as the obvious public-domain source because it offers search, categories, top downloads, and a large public-domain catalog. ([Atari Magazines][1])

---

# Safari Reader

## Product Specification

### A terminal e-book reader with AtariWriter-era UI vibes

## 1. Purpose

Safari Reader is a full-screen terminal reading application for modern computers. It is inspired by the **menu-first, keyboard-centric, low-distraction experience** of early 1980s word processors and DOS utilities, especially AtariWriter and Atari DOS, which emphasized a main work screen, a predictable menu system, and prominent command prompts. ([Atari Magazines][1])

This app is **not** a historical emulator. It is a modern reading system that asks:

> “If a serious, useful book reader had existed in the AtariWriter era, what would its UI patterns likely have been?”

The result should feel:

* calm
* deliberate
* keyboard-first
* legible
* “retro productive”
* constrained in a good way

It should also include a few carefully chosen modern conveniences:

* adjustable text size
* adjustable line spacing
* instant dictionary lookup on a selected word
* a local library/bookshelf
* downloading/browsing public-domain books from the web
* bookmarks, reading position, and annotations

---

## 2. Design Goals

### 2.1 Primary goals

* Provide a **pleasant long-form reading experience** in a terminal.
* Capture the **visual and interaction vocabulary** of AtariWriter-era productivity software.
* Keep the UI **simple enough to learn from a single help screen**.
* Support both **reading local books** and **fetching public-domain books** from online sources.
* Avoid “desktop app clutter.” No floating panes, no mouse-required UI, no modern ribbon nonsense.

### 2.2 Secondary goals

* Make book management feel like an old-school utility disk or document selector.
* Make dictionary lookup feel like a period-plausible “desk accessory” or “reference utility.”
* Allow both pure keyboard use and optional mouse support where terminals support it.
* Be pleasant for someone reading fiction, essays, reference texts, or manuals.

### 2.3 Non-goals

* Not a web browser.
* Not a full EPUB layout engine equivalent to a modern GUI e-reader.
* Not a historical Atari emulator.
* Not a social reading platform.
* Not a note-taking PKM monster.

---

## 3. Historical UI Direction

AtariWriter was known for being straightforward and menu-oriented, and Atari DOS was famously menu-driven rather than command-line first. The app should inherit those ideas: one dominant screen, obvious commands, reversible actions, and menus that feel like utility software rather than a modern app shell. ([Atari Magazines][1])

### 3.1 Core UI principles borrowed from old-school software

* **One main full-screen mode at a time**
* **A stable header/status area**
* **A stable footer/command legend**
* **Commands grouped into named menus**
* **Letter-driven or function-key-driven actions**
* **Modal but understandable screens**
* **Simple dialog boxes**
* **No deep nesting when avoidable**
* **Visible current state at all times**

### 3.2 What “AtariWriter vibes” means here

Not literal copying. Instead:

* crisp screen borders or inverse-text bars
* a work area surrounded by utility/status information
* text-heavy UI rather than icon-heavy UI
* keyboard shortcuts shown on screen
* “press a key to do a thing” confidence
* fast transitions between screens
* the feeling that the software was designed for someone who might read the manual once and then memorize the commands

---

## 4. Supported Content

### 4.1 Required input formats

* Plain text (`.txt`)
* Markdown (`.md`) as readable text
* HTML imported as simplified readable text
* Project Gutenberg plain text downloads
* EPUB import via conversion pipeline into internal chapter/text representation

### 4.2 Optional later formats

* PDF import via text extraction only
* RTF
* FB2
* MOBI via conversion

### 4.3 Internal representation

All imported books should be converted into an internal normalized structure:

* metadata
* sections/chapters
* paragraphs
* word index positions
* reading progress markers
* annotations/bookmarks

This keeps rendering simple and historically in spirit.

---

## 5. Overall App Structure

The application has six major areas:

1. **Reader Screen**
   Main reading experience.

2. **Library Screen**
   Local bookshelf / downloaded books / import management.

3. **Catalog Screen**
   Browse and search public-domain web catalogs.

4. **Dictionary Screen / Lookup Pop-up**
   Look up currently selected word.

5. **Bookmarks & Notes Screen**
   Jump points, highlights, notes.

6. **Preferences / Setup Screen**
   Reading display, controls, network/download preferences.

---

## 6. Screen Model

## 6.1 Boot / Splash Screen

On launch:

* retro title
* version
* short loading message
* last-read book shown if available

Example feel:

* centered title
* inverse bar at top or bottom
* “Press any key for Library / ENTER to resume last book”

### Actions

* Resume last book
* Open Library
* Open Catalog
* Help
* Quit

---

## 6.2 Main Reader Screen

This is the heart of the app.

### Layout

**Top status bar**

* app name
* current book title
* chapter/section name
* progress percent
* battery/clock optional if available
* online/offline indicator optional

**Main reading pane**

* rendered book text
* margins
* page or scroll mode
* selected word highlight when active
* bookmark markers in gutter if appropriate

**Bottom command bar**

* a compact legend like:

  * `Esc=Menu`
  * `PgUp/PgDn=Page`
  * `/=Find`
  * `D=Define`
  * `B=Bookmark`
  * `G=Go To`
  * `+=Bigger`
  * `-=Smaller`

This footer is historically appropriate because period software often kept essential commands visible or one keystroke away. ([Atarimania][2])

### Reader modes

The screen supports two reading modes:

#### A. Page Mode

* discrete pages
* fixed amount of text per page
* page number or “screen number” display
* more period-authentic feel

#### B. Flow Mode

* smooth scrolling
* modern convenience
* still rendered in a terminal-friendly way

Default: **Page Mode**

---

## 6.3 Library Screen

This is the “disk directory + bookshelf” hybrid.

### Purpose

* list local books
* show reading progress
* sort/filter
* import local files
* remove/archive books
* resume recent titles

### Layout

Top bar:

* `Library`
* current sort/filter

Main pane:

* one row per book
* columns:

  * title
  * author
  * format
  * progress
  * last opened
  * source

Bottom bar:

* commands such as

  * `R=Read`
  * `I=Import`
  * `C=Catalog`
  * `S=Sort`
  * `F=Filter`
  * `D=Details`
  * `A=Archive`

### View styles

* compact list
* large-title list
* “disk catalog” mode with short filenames and metadata
* “bookshelf” mode with richer metadata

---

## 6.4 Catalog Screen

This is the “download from web” subsystem.

Because Project Gutenberg provides a large catalog, category browsing, advanced search, and top downloads, it is a natural default online source for public-domain books. ([Project Gutenberg][3])

### Purpose

* browse online public-domain catalogs
* search by title/author/subject
* download selected books
* preview metadata before download

### Data sources

Required:

* Project Gutenberg

Optional later:

* Standard Ebooks
* Internet Archive text sources
* local OPDS feeds

### Catalog submodes

#### A. Top Titles

* mirrors “Top 100” / frequently downloaded feel
* easy for casual readers

#### B. Categories

* Fiction, Science, History, etc.
* mirrors Project Gutenberg main categories/bookshelves. ([Project Gutenberg][4])

#### C. Search

* title
* author
* subject
* language

#### D. Recent / New

* recently added items when source provides it

### Catalog item details

Selecting a title opens details:

* title
* author
* release date if available
* language
* subjects
* available formats
* short description if available
* download size

### Actions

* Download text
* Download EPUB
* Preview metadata
* Add to local library
* Open author search
* Open subject search

### Historical plausibility treatment

This should feel less like a browser and more like a “remote disk catalog” or “online library service terminal.”

That means:

* no embedded HTML browsing
* no arbitrary URL bar
* structured menus instead of browsing raw websites
* searches entered into forms
* results shown as sortable lists

---

## 6.5 Dictionary Lookup Screen

This is a major feature and should feel like a built-in reference utility.

### Trigger methods

* keyboard select current word and press `D`
* double-click word with mouse if terminal supports it
* move caret/highlight onto word and press Enter
* right-click optional, not required

### Behavior

When a word is selected:

* open a pop-up or overlay window
* show:

  * headword
  * pronunciation if available
  * part of speech
  * short definition
  * alternate definitions
  * etymology optional
  * synonyms optional

### Sources

Primary:

* local offline dictionary database

Optional:

* online dictionary fallback if enabled

### Historical UI style

This should feel like:

* a desk accessory
* a modal overlay
* a compact reference window
* dismiss with `Esc`

### Related actions

* add word to vocabulary list
* search the book for same word
* stemming/variant lookup
* “next meaning”
* “copy quote with word”

---

## 6.6 Book Details Screen

Accessible from Library or Catalog.

### Shows

* title
* author
* source
* format
* size
* language
* tags/subjects
* current progress
* bookmarks count
* notes count
* download/import date

### Actions

* Read
* Resume
* Restart
* Rename local entry
* Re-download
* Export metadata
* Archive/delete from library

---

## 6.7 Bookmarks & Notes Screen

### Purpose

* show all bookmarks in current book
* jump to any bookmark
* show note excerpts
* manage highlights

### UI style

A simple indexed list:

* bookmark name
* location/chapter
* short excerpt
* date added

### Actions

* Go to
* Rename
* Delete
* Convert bookmark to note
* Export notes

---

## 6.8 Preferences Screen

Should be menu/form based, not settings-panel modern.

### Categories

* Reading appearance
* Navigation
* Dictionary
* Downloads
* Library management
* Key bindings
* Accessibility

### UI pattern

Use form-like rows:

* label
* current value
* editable by arrows, Enter, or typed input

This is period-appropriate because configuration screens in older software were often field-editing forms rather than giant preference dashboards.

---

## 7. Reading Features

## 7.1 Paging and navigation

Required:

* next page
* previous page
* next chapter
* previous chapter
* jump to percent
* jump to chapter
* jump to bookmark
* return to prior location
* table of contents

## 7.2 Reading progress

The app must persist:

* current book
* current position
* percent complete
* total reading time
* last opened timestamp

## 7.3 Display controls

Required:

* increase text size
* decrease text size
* reset to default size
* line spacing: single / one-and-a-half / double
* margin width: narrow / normal / wide
* justification: ragged-right default, optional full justify
* theme: phosphor-dark / paper-light / blue-screen / amber-screen optional

### Note on “font size” in terminal

In a terminal, “font size” cannot always mean OS-level actual font size. Therefore the spec defines it functionally as:

* larger rendered layout
* fewer columns
* wider margins
* optional double-spacing
* optional bold/bright rendering
* alternate glyph/zoom modes where terminal supports it

So the user-facing control is “text size,” even if implementation varies by terminal capability.

## 7.4 Search inside book

* incremental find
* find next / previous
* search by phrase
* whole word toggle
* case sensitivity toggle
* results list with snippets

## 7.5 Section navigation

* chapter list
* section list
* page number if page model exists
* “go to location”
* “resume from last chapter start”

## 7.6 Bookmarks and notes

* quick bookmark
* named bookmark
* highlight passage
* attached note
* export notes to markdown/text

## 7.7 Readability helpers

* ruler line toggle
* current line emphasis optional
* progress bar
* estimated time left in chapter/book
* hyphenation toggle optional

---

## 8. Word Selection and Lookup

This feature is central.

## 8.1 Word selection model

The app supports a **reading cursor** independent of editing.

Ways to move selection:

* arrow keys move by word or line
* `Tab` jumps to next word group
* mouse click selects a word
* keyboard shortcut enters “lookup mode”

### Lookup mode

A special mode where:

* cursor snaps to words
* selected word shown in inverse video
* footer changes to lookup actions:

  * `Enter=Define`
  * `S=Search`
  * `N=Next occurrence`
  * `Esc=Back`

This is a strong old-school pattern: temporary mode, visible affordances, obvious exit.

## 8.2 Dictionary behavior

When defining a word:

* prefer exact match
* fallback to normalized form
* fallback to stem/lemma
* show “not found” gracefully
* allow add-on dictionaries

## 8.3 Dictionary pane style variants

Implementations may choose one of:

* modal pop-up
* split bottom pane
* temporary full-screen reference page

Preferred default: **modal pop-up**

---

## 9. Input Model

## 9.1 Keyboard-first

Everything must be usable by keyboard alone.

### Core keys

* `Esc` opens command menu / backs out
* arrows move selection/menus
* `Enter` activates selected item
* `Tab` cycles fields or modes
* `PgUp/PgDn` page
* `Home/End` start/end of chapter
* `/` search
* `D` define word
* `B` bookmark
* `G` go to
* `L` library
* `C` catalog
* `H` help
* `Q` quit/back

### Optional function-key mappings

Permit configurable F-key shortcuts for:

* Help
* Library
* Search
* Bookmark
* Dictionary
* Settings

## 9.2 Mouse support

Optional but useful:

* click word to select
* double-click to define
* click progress bar for approximate jump
* click menu items

Mouse support must never be mandatory.

---

## 10. Menus

Menus should feel like old productivity software: concise, named, and reliable.

## 10.1 Top-level menu groups

Pressing `Esc` from reader opens command menu:

* **Book**
* **Go To**
* **Search**
* **Mark**
* **Lookup**
* **View**
* **Library**
* **Online**
* **Setup**
* **Help**

## 10.2 Example menu contents

### Book

* Open Library
* Book Details
* Table of Contents
* Close Book
* Export Notes
* Quit

### Go To

* Next Chapter
* Previous Chapter
* Percentage
* Page
* Bookmark
* Last Position

### Search

* Find Text
* Find Next
* Find Previous
* Search Selected Word
* Chapter Search

### Mark

* Set Bookmark
* Name Bookmark
* Add Note
* Highlight Passage
* View Bookmarks

### Lookup

* Define Word
* Thesaurus
* Search in Book
* Add to Vocabulary

### View

* Bigger Text
* Smaller Text
* Line Spacing
* Margins
* Theme
* Page Mode / Flow Mode

### Library

* Local Books
* Recent Books
* Import File
* Archived Books

### Online

* Browse Categories
* Top Downloads
* Search Catalog
* Download by ID
* Sync Metadata

### Setup

* Preferences
* Key Bindings
* Dictionaries
* Downloads
* Accessibility

### Help

* Quick Help
* Keys
* Reading Tips
* About

---

## 11. Help System

The app needs a strong help system because old software expected users to read built-in help and quick reference screens.

### Types of help

* Quick help overlay
* Full help manual
* Context-sensitive help
* Key reference card

### Help style

* concise
* indexed
* pages you can scroll
* references to commands by exact key names

### Example

From reader:

* `H` = quick reader help
* `Shift+H` = full manual

---

## 12. Online Catalog and Download Behavior

## 12.1 Web source concept

The app presents supported online sources as curated catalogs, not arbitrary browsing.

### Default source

* Project Gutenberg

Because Project Gutenberg offers a broad public-domain collection, categories, advanced search, and top-download lists, it fits the use case cleanly. ([Project Gutenberg][3])

## 12.2 Browse modes

* by author
* by title
* by subject/category
* by popularity
* by language
* by recently added

## 12.3 Download workflow

1. User opens Catalog.
2. User browses/searches.
3. User selects title.
4. App shows metadata/details.
5. User chooses format.
6. App downloads.
7. App imports into local library.
8. App offers “Read now?”

## 12.4 Offline behavior

* cached catalog results allowed
* downloaded books always remain readable offline
* if network unavailable, catalog screen clearly indicates offline state

## 12.5 Safety and legality

* app only downloads from supported sources the user selects
* app stores source URL/ID in metadata
* app avoids pretending all books are copyright-free everywhere; source-provided rights metadata should be preserved where available

---

## 13. Accessibility and Comfort

Even with retro vibes, comfort matters.

### Required comfort features

* adjustable text size
* adjustable spacing
* dark and light themes
* low-glare theme
* optional progress bar off
* reduced flicker / no animated cursor requirement
* configurable key repeats
* optional “focus line” highlight

### Optional later

* read-aloud via system TTS
* dyslexia-friendly rendering mode if terminal/font allows
* high-contrast mode
* screen reader-optimized linear mode

---

## 14. Data and Persistence

## 14.1 Local data to persist

* library catalog
* download metadata
* reading position
* bookmarks
* notes/highlights
* dictionary history
* preferences
* recent searches

## 14.2 Book storage

Books should be stored in a managed local library directory with:

* imported source files
* normalized text/chapter representation
* metadata sidecar
* notes/bookmarks sidecar or DB record

## 14.3 Backup/export

Users should be able to export:

* notes
* bookmarks
* reading history
* library index

---

## 15. Error Handling Philosophy

The app should behave like trustworthy utility software.

### Principles

* never lose reading progress
* never corrupt local library silently
* always explain failed downloads
* do not dump stack traces into the reader UI
* offer retry/cancel choices
* keep error messages short and specific

### Example messages

* `NETWORK NOT AVAILABLE`
* `BOOK FORMAT NOT SUPPORTED`
* `DICTIONARY ENTRY NOT FOUND`
* `DOWNLOAD INTERRUPTED`
* `LOCAL COPY DAMAGED - REIMPORT?`

These short, declarative messages fit the old-school tone.

---

## 16. Visual Style Specification

## 16.1 Overall look

* monospaced layout first
* strong use of inverse text bars
* minimal border characters
* limited color palette
* no decorative clutter
* emphasis on rectangular regions

## 16.2 Themes

Required themes:

* **Classic Dark** — dark background, bright text
* **Paper** — light background, dark text
* **Blue Screen** — period-inspired
* **Amber Terminal** — nostalgic optional

## 16.3 Status language

Use compact status text:

* `BOOK: MOBY DICK`
* `CHAPTER: Loomings`
* `PAGE 014`
* `42% READ`

## 16.4 Motion

Minimal animation only:

* maybe tiny download progress movement
* otherwise instant screen changes
* avoid flashy transitions

---

## 17. Period-Plausible UI Patterns to Borrow

These are the old-school patterns that make sense here:

### 17.1 Footer command legend

Common, useful, and immediately readable.

### 17.2 Esc-to-menu

Very plausible for productivity software of the era.

### 17.3 Modal utility pop-ups

Perfect for dictionary, bookmarks, and help.

### 17.4 Indexed list screens

Great for library/catalog/bookmarks.

### 17.5 Form-entry search screens

Better than freeform browsing for historical feel.

### 17.6 “Current field” highlighting

Useful in settings and search forms.

### 17.7 Distinct work mode vs command mode

A classic pattern for text-centric software.

---

## 18. Suggested User Flows

## 18.1 Read a local book

1. Open app
2. Enter Library
3. Choose title
4. Resume reading
5. Adjust text size and spacing
6. Bookmark passage
7. Quit; position auto-saved

## 18.2 Look up a word

1. While reading, move to word
2. Press `D`
3. Dictionary pop-up appears
4. Read definition
5. `Esc` returns to same reading position

## 18.3 Download a public-domain novel

1. Open Catalog
2. Browse Top Titles or Search
3. Select title
4. Review metadata
5. Download text/EPUB
6. Add to library
7. Start reading

## 18.4 Browse by category

1. Open Catalog
2. Select Categories
3. Choose Fiction / Science / History / etc.
4. Scroll titles
5. Download or inspect details

---

## 19. Functional Requirements Summary

## 19.1 Must-have

* full-screen terminal UI
* library management
* local book import
* reading position persistence
* page navigation
* text search
* text size adjustment
* line spacing adjustment
* word selection
* dictionary lookup
* online public-domain catalog browsing
* downloading supported books
* bookmarks
* help screen

## 19.2 Should-have

* chapter list
* notes/highlights
* offline dictionary
* recent books
* category browsing
* popularity browsing
* light/dark themes
* export notes

## 19.3 Nice-to-have

* vocabulary builder
* read-aloud
* thesaurus
* reading stats
* multiple online sources
* cloud sync
* OPDS support

---

## 20. Implementation Constraints for the Agent

These are product constraints, not low-level coding instructions.

### 20.1 The app must feel fast

* startup should be quick
* opening a book should be quick
* page turns should feel instant

### 20.2 The UI must stay simple

* one main focus area
* no overloaded screen with five panes
* avoid excessive hotkeys

### 20.3 Modern features must be disguised in period-appropriate interaction

Example:

* don’t show a browser tab strip
* do show “Catalog Search” form and “Results” list

### 20.4 Dictionary lookup must not feel bolted on

It should feel like a built-in reference command.

---

## 21. Example Command Reference Card

### Reader

* `PgDn` Next page
* `PgUp` Previous page
* `Ctrl+PgDn` Next chapter
* `Ctrl+PgUp` Previous chapter
* `/` Search text
* `D` Define selected word
* `B` Set bookmark
* `G` Go to
* `+` Bigger text
* `-` Smaller text
* `]` More spacing
* `[` Less spacing
* `Esc` Menu
* `H` Help
* `L` Library
* `C` Catalog
* `Q` Back/Quit

---

## 22. Product Positioning

Safari Reader is for:

* people who want to read books in a terminal
* people who enjoy retro productivity aesthetics
* people who prefer keyboard navigation
* people who want a focused, distraction-light reading experience
* people who like the feeling of old software without the misery of old hardware limits

It should feel like:

* **AtariWriter met a personal library**
* **a disk utility turned into an e-reader**
* **a book machine from an alternate 1984**

---

## 23. One-Sentence Vision

**Safari Reader is a keyboard-first terminal e-book reader that combines AtariWriter-era menu-driven charm with modern conveniences like adjustable readability, dictionary lookup, and downloadable public-domain books.**

---


[1]: https://www.atarimagazines.com/startv1n3/STWriter.html?utm_source=chatgpt.com "ST Writer Secrets"
[2]: https://www.atarimania.com/documents/Atari_1050_disk_operating_system_II_reference_manual.pdf?utm_source=chatgpt.com "Disk Operating System II Reference Manual"
[3]: https://www.gutenberg.org/?utm_source=chatgpt.com "Project Gutenberg: Free eBooks"
[4]: https://www.gutenberg.org/ebooks/categories?utm_source=chatgpt.com "Main Categories"
