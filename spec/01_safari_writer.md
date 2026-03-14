**Safari Writer**, adapted from the original AtariWriter 80 feature set.

______________________________________________________________________

# Product Specification: Safari Writer

## 1. Overview

Safari Writer is a UI-compatible clone of the classic word processing software, offering a distraction-free,
terminal-style interface. It combines straightforward text editing with built-in spelling verification (Proofreader) and
database integration (Mail Merge). The application maps classic legacy modifiers to a modern keyboard (e.g., replacing
Atari's `[Option]`, `[Select]`, and `[Start]` keys with standard modern modifiers like `Alt`, `Ctrl`, and Function
keys).

## 2. Main Menu Interface

The main menu acts as the hub for all operations. Users navigate and select options by pressing the highlighted first
letter of the command.

-

**C**reate File: Starts a new document.

-

**E**dit File: Returns to the active document in memory.

-

**V**erify Spelling: Launches the Proofreader module.

-

**P**rint File: Initiates the print sequence.

-

**G**lobal Format: Opens the layout settings screen.

-

**M**ail Merge: Launches the database module.

-

**1** Index Current Folder / **2** Index External Drive: Displays a directory listing. "1" shows the current working folder; "2" scans for removable/external drives (USB thumb drives, secondary disks) and shows their contents.

-

**L**oad File: Retrieves a file from storage.

-

**S**ave File: Stores the current file.

-

**D**elete File: Erases a file from storage.

-

**F**older (New): Creates a new folder in the current directory.

## 3. The Text Screen (UI)

The editing screen maintains a clean, functional layout with a status header at the top.

-

**Message Window**: Displays prompts, questions, and error messages at the very top.

-

**System Status**: Displays available memory (Bytes Free), the current Edit Mode (Insert/Type-over), and the
Capitalization Mode (Lowercase/Uppercase).

-

**Tab Indicators**: 16 downward-pointing arrows indicating current tab stops across the top margin.

-

**Cursor**: A blinking block indicating the current typing position.

## 4. Editing & Navigation Features

-

**Typing Basics**: Features automatic word wrap; standard carriage returns are only used for new paragraphs or blank
lines.

-

**Paragraph Marking**: Users can insert a non-printing paragraph symbol to automatically indent lines during printing
without using a carriage return.

-

**Edit Modes**: Toggling between "Insert" (pushes text right) and "Type-over" (replaces text).

- **Text Manipulation**:

- Character/Line deletion.

- Undelete (restores the last deleted line at the cursor).

- **Modern Keyboard Navigation Strategy**:

-

*Word Jump*: `Ctrl + Left/Right Arrow` (Adapts Atari `[Select] + Arrow`).

-

*Line Ends*: `Home/End` (Adapts Atari `[Control] + A/Z`).

-

*Top/Bottom of File*: `Ctrl + Home/End` (Adapts Atari `[Select] + T/B`).

-

*Page Scroll*: `Page Up/Down` (Adapts Atari `[Option] + Arrow`).

## 5. Advanced Editing (Block Operations)

Block operations utilize a "failsafe buffer" (clipboard) that holds cut or copied text.

-

**Define Block**: Users drop a "Beginning Marked" anchor at the start of a passage.

-

**Delete/Move (Cut)**: Removes the block and stores it in the failsafe buffer.

-

**Duplicate (Copy)**: Copies the block to the buffer without deleting.

-

**Paste**: Inserts the buffer contents at the cursor location.

-

**Utility Operations**: Includes features to count the words in a defined block/file, and to automatically alphabetize a
selected list of words.

-

**Search & Replace**: Supports searching for strings up to 37 characters, case-by-case replacement, global replacement,
and wildcard (?) characters.

## 6. Formatting & Layout

Safari Writer uses a dual-layer formatting system: Global parameters and Inline control codes.

### Global Format Screen

Accessed from the Main Menu, this screen sets the master layout using 1-letter codes:

-

**Margins**: Top (T), Bottom (B), Left (L), Right (R).

-

**Double Column**: 2nd Left (M), 2nd Right (N) for newspaper-style columns.

-

**Spacing**: Line Spacing (S), Paragraph Spacing (D).

-

**Styling**: Type Font (G), Paragraph Indentation (I), Justification (J).

-

**Pagination**: Page Number start (Q), Page Length (Y), Page Wait for single-sheet feeding (W).

### Inline Formatting

Formatting variations can be embedded directly into the text stream. These display as special non-printing control
characters on screen.

-

**Text Styles**: Bold, Elongated (double-width), Underline, Subscripts, and Superscripts.

-

**Alignment**: Center line, Block Right.

- **Structure**:

- Headers/Footers (supports multi-line and auto-page numbering using `@`).

- Section Headings (auto-numbered, outline-style heading levels 1-9).

- Form Printing (inserts blanks that prompt the user to type in data at print time).

## 7. Proofreader Module (Spelling)

An integrated module for verifying spelling against a master dictionary and user-defined personal dictionaries.

-

**Highlight Errors**: Scans the file and highlights unrecognized words in inverse video.

-

**Correct Errors**: Stops at each error, offering a menu to: Correct Word, Search Dictionary, or Keep This Spelling.

-

**Personal Dictionary**: Words saved via "Keep This Spelling" can be compiled and saved as a personal dictionary file
for future proofing sessions.

## 8. Mail Merge Module (Database)

A built-in data management tool used primarily for generating form letters or managing contacts.

-

**Record Creation**: Users can use a default 15-field template (Name, Address, etc.) or design a custom format with up
to 15 fields (max 20 characters per field).

-

**Data Entry/Editing**: Allows users to input, flip through, update, or delete records.

-

**Subsets**: Users can filter records by setting a "LOW VALUE" and "HIGH VALUE" (e.g., A through E) on a specific field
to isolate a group of records.

- **Integration**: Users drop a database merge character (`@` followed by the field number) into standard text
  documents. During printing, Safari Writer pulls the corresponding data from the Mail Merge file.

______________________________________________________________________

Would you like me to map out a complete proposed shortcut key matrix matching the classic Atari functions to standard
Windows/Mac keyboard shortcuts for this spec?
