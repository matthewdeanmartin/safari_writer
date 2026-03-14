# Safari Writer Help

Welcome to Safari Writer, a word processor inspired by AtariWriter 80.
This document covers Safari Writer, Safari DOS, Safari Chat, and Safari Fed.
If something is frustrating, that is okay. Take it one step at a time.

---

## Getting Started

Safari Writer is a text-mode word processor. You type, format,
save, and print documents from your keyboard. No mouse required.

To start the program, run **safari-writer** from the command line.
You will see the Main Menu. From there you can create a new file,
load an existing one, or explore other features.

If you are new, try pressing **T** from the Main Menu to load a
demo document. This will show you what formatted text looks like
in the editor.
---

## Main Menu

The Main Menu is the central hub. Press the highlighted letter
to activate each option.

**Document Actions:**
- **C** **Create** File — start a blank document
- **E** **Edit** File — return to your active document
- **L** **Load** File — open a document from disk
- **S** **Save** File — save your current document
- **A** **Save As** — save with a new filename
- **D** **Delete** File — move a file to Garbage (recoverable)

**Need help with saving?**
- [I am getting a Disk Full error](#Disk Full Error)
- [I do not know where my file went](#Finding Files)

**Modules:**
- **V** **Verify Spelling** — launch the Proofreader
- **P** **Print** File — print or export your document
- **G** **Global Format** — set margins, spacing, and layout
- **M** **Mail Merge** — database and form letters

---

## Disk Full Error

If you see a "Disk Full" error, your storage device has no more
room for new data. You have a few options:

1.  **Delete** old files using the **D** command from the Main Menu.
2.  **Insert** a different disk or use a different folder.
3.  **Compress** your document by removing large images or unneeded text.

---

## Finding Files

If you saved a file but cannot find it, check the following:

1.  **Current Folder:** Use the **1** command to see files in the current folder.
2.  **External Drives:** Use the **2** command to check other drives.
3.  **Search:** Use the Search function in **Safari DOS** (press **O**).

---

**File Browsing:**
- **1** **Index** Current Folder — browse files here
- **2** **Index** External Drive — browse other drives
- **O** Open **Safari DOS** — full file manager
- **F** **Folder** (New) — create a new directory

**Other:**
- **T** Try **Demo Mode** — load a sample document
- **X** **Style Switcher** — choose a color theme
- **Q** **Quit** — exit the program

---

## Editor Basics

The editor is where you write. The screen has three zones:
a status bar at the top, the text area in the middle, and a
tab-stop indicator row.

**The status bar** shows: bytes free, Insert or Type-over mode,
and Uppercase or Lowercase mode.

**Insert mode** pushes existing text to the right as you type.
**Type-over mode** replaces the character under the cursor.
Press **Insert** to toggle between them.

Press **Enter** for a new line. Press **Tab** to jump to the
next tab stop. Press **Escape** to return to the Main Menu.

---

## Cursor Movement

- **Arrow Keys** — move one character or line at a time
- **Ctrl + Left/Right** — jump word by word
- **Home / End** — jump to start or end of the current line
- **Ctrl + Home / Ctrl + End** — jump to top or bottom of the file
- **Page Up / Page Down** — scroll one page at a time

---

## Selecting Text

Hold **Shift** while pressing movement keys to select text.

- **Shift + Arrows** — extend selection character by character or line by line
- **Shift + Home / End** — extend selection to line start or end
- **Shift + Ctrl + Home / End** — extend selection to file start or end

Selected text is shown highlighted. Many commands act on the
selection when one exists.

---

## Deleting Text

- **Backspace** — delete the character before the cursor (or the selection)
- **Delete** — delete the character at the cursor (or the selection)
- **Shift + Delete** — delete from cursor to end of the line
- **Ctrl + Shift + Delete** — delete from cursor to end of the file
- **Ctrl + Z** — undo the last action

---

## Cut, Copy, and Paste

- **Ctrl + X** — cut selection to clipboard (or cut the whole line if nothing is selected)
- **Ctrl + C** — copy selection to clipboard (or copy the whole line)
- **Ctrl + V** — paste clipboard contents at the cursor

These work like any word processor. The clipboard holds one
item at a time. Cutting or copying replaces whatever was there.

---

## Word Count and Alphabetize

- **Alt + W** — count words in the selection (or the whole file)
- **Alt + A** — sort the selected lines alphabetically (A to Z)

Word count shows a message in the status bar. Alphabetize
rearranges lines, which is useful for lists and glossaries.

---

## Search and Replace

**Finding text:**
- **Ctrl + F** — prompts for a search string, then jumps to the first match
- **F3** — find the next occurrence of the last search string

**Replacing text:**
- **Alt + H** — set the replacement string
- **Alt + N** — replace the current match and find the next one
- **Alt + R** — replace all occurrences from the cursor to the end of the file

The search is case-sensitive. If no match is found, the status
bar will say so.

---

## Inline Formatting

Formatting codes appear as visible markers in the editor.
They do not change what you see on screen, but they control
how text looks when printed or exported.

**Character formatting (toggle on and off):**
- **Ctrl + B** — bold (shows ← marker)
- **Ctrl + U** — underline (shows ▄ marker)
- **Ctrl + G** — elongated / double-width (shows E marker)
- **Ctrl + [** — superscript (shows ↑ marker)
- **Ctrl + ]** — subscript (shows ↓ marker)

**Paragraph formatting (placed at the start of a line):**
- **Ctrl + E** — center the line (shows ↔ marker)
- **Ctrl + R** — flush right / block right (shows →→ marker)

**Special inserts:**
- **Ctrl + M** — paragraph mark (auto-indent without a hard return)
- **Alt + M** — mail merge field (type a field number 1-15 after the @ marker)
- **Alt + F** — form printing blank (prompts for input at print time)

---

## Document Structure

These markers control page layout and multi-file printing.

- **Ctrl + Shift + H** — insert a header line (prints at the top of every page)
- **Ctrl + Shift + F** — insert a footer line (prints at the bottom of every page)
- **Ctrl + Shift + S** — insert a section heading (auto-numbered, levels 1-9)
- **Ctrl + Shift + E** — insert a page break (forces a new page)
- **Ctrl + Shift + C** — chain print file (links another file for sequential printing)

---

## Tab Stops

The tab indicator row shows downward arrows at each active tab
stop position.

- **Tab** — jump the cursor to the next tab stop
- **Ctrl + T** — toggle a tab stop at the current column
- **Ctrl + Shift + T** — clear all custom tab stops (resets to default every 5 columns)

---

## Case Toggling

- **Caps Lock** — toggle between Uppercase and Lowercase mode
- **Shift + F3** — toggle the case of the character at the cursor
- **Insert** — toggle between Insert and Type-over mode

---

## Global Format

Press **G** from the Main Menu to open the Global Format screen.
This controls the overall layout of your printed document.

Press the highlighted letter to edit a parameter. Type a new value
and press **Enter** to confirm. Press **Escape** to cancel an edit.
Press **Tab** to reset everything to factory defaults.

**Margins:**
- **T** Top Margin (default 12 half-lines = 1 inch)
- **B** Bottom Margin (default 12)
- **L** Left Margin (default 10 character spaces)
- **R** Right Margin (default 70)

**Spacing:**
- **S** Line Spacing (2 = single, 4 = double, 6 = triple)
- **D** Paragraph Spacing (default 2 half-lines)

**Multi-Column Layout:**
- **M** 2nd Left Margin (for a right-hand column)
- **N** 2nd Right Margin

**Typography:**
- **G** Type Font (1=pica, 2=condensed, 3=proportional, 6=elite)
- **I** Paragraph Indentation (0 = block style, default 5)
- **J** Justification (0 = ragged right, 1 = justified)

**Pagination:**
- **Q** Page Number Start (default 1)
- **Y** Page Length (default 132 half-lines for 8.5 x 11 paper)
- **W** Page Wait (0 = off, 1 = pause between pages)

---

## Printing and Exporting

Press **P** from the Main Menu or **Ctrl + P** in the editor.

- **A** ANSI Preview — view your formatted document in the terminal
- **M** Export to Markdown — save as a .md file
- **P** Export to PostScript — save as a .ps file
- **R** or **Escape** — return to the previous menu

The ANSI preview shows pages with your margins, spacing, and
formatting applied. Use Page Up and Page Down to navigate pages.

---

## Proofreader

Press **V** from the Main Menu to check your spelling.

**Proofreader Menu:**
- **H** Highlight Errors — scan the document and highlight misspelled words
- **P** Print Errors — show a list of all misspelled words
- **C** Correct Errors — stop at each error with options to fix it
- **S** Dictionary Search — look up words by typing the first few letters
- **L** Load Personal Dictionary — load your custom word list
- **W** Write Personal Dictionary — save words you have accepted

**During Correct Errors mode, at each misspelled word you can:**
- Type a correction and confirm
- Search the dictionary for suggestions
- Keep the current spelling (accept it for this session)

The proofreader uses a standard English dictionary. You can add
words to a personal dictionary so they are not flagged again.

---

## Mail Merge

Press **M** from the Main Menu to work with databases and
form letters.

**Mail Merge Menu:**
- **C** Create File — start a new database
- **E** Edit File — browse and modify records
- **B** Build Subset — filter records by field range
- **A** Append File — merge another database with the same schema
- **P** Print File — run mail merge with your document
- **L** Load File — load a database from disk
- **S** Save File — save the database to disk
- **F** Format Record — edit field names and lengths
- **R** Return — go back to the Main Menu

**How mail merge works:**
1. Create a database with field names (like Name, City, State).
2. Enter records (one per person, company, etc.).
3. In your document, insert merge fields with **Alt + M** and a
   field number (1-15).
4. Print with **P** from the Mail Merge menu. It prints one copy
   of your document for each record, with data filled in.

**Database limits:**
- Maximum 255 records per file
- Maximum 15 fields per record
- Maximum 20 characters per field value
- Maximum 12 characters per field name

**Editing records:**
- **Page Up / P** — previous record
- **Page Down / N** — next record
- **E** — edit all fields of the current record
- **Up/Down** — select a field, then **Enter** to edit it
- **Ctrl + D** — delete the current record

---

## File Browsing

Press **1** from the Main Menu to browse files in the current
folder, or **2** to browse another drive.

- **Up / Down** — navigate the file list
- **Home / End** — jump to first or last entry
- **Page Up / Page Down** — jump ahead or back
- **Enter** — open the selected file or enter a directory
- **Backspace** — go up to the parent directory
- **D** — delete the selected file
- **F** — create a new folder
- **R** — return to the Main Menu

---

## Style Switcher

Press **X** from the Main Menu to change the color theme.

- **Up / Down** — browse available themes
- **Enter** — apply the selected theme and save it
- **Escape** — cancel and revert to the previous theme

The theme changes are previewed live as you browse. Your choice
persists across sessions.

---

## Keyboard Quick Reference

**Navigation:**
Arrows, Ctrl+Arrows, Home, End, Ctrl+Home, Ctrl+End, PgUp, PgDn

**Selection:**
Shift + any navigation key

**Editing:**
Backspace, Delete, Shift+Del, Ctrl+Shift+Del, Ctrl+Z

**Clipboard:**
Ctrl+X (cut), Ctrl+C (copy), Ctrl+V (paste)

**Search:**
Ctrl+F (find), F3 (next), Alt+H (set replace), Alt+N (replace next),
Alt+R (replace all)

**Formatting:**
Ctrl+B (bold), Ctrl+U (underline), Ctrl+G (elongated),
Ctrl+[ (super), Ctrl+] (sub), Ctrl+E (center), Ctrl+R (right)

**Structure:**
Ctrl+Shift+H (header), Ctrl+Shift+F (footer), Ctrl+Shift+S (section),
Ctrl+Shift+E (page break), Ctrl+Shift+C (chain file)

**Tabs:**
Tab (jump), Ctrl+T (set/clear), Ctrl+Shift+T (clear all)

**Other:**
Insert (mode toggle), Shift+F3 (case toggle), Ctrl+P (print),
F1 (help), Escape (menu), Alt+W (word count), Alt+A (alphabetize)

---

## Safari DOS File Manager

Safari DOS is a full file manager. Open it with **O** from the
Safari Writer Main Menu, or run **safari-dos** from the command line.

**Main Menu:**
- **F** File List — browse the current folder
- **D** Devices — select a different drive or volume
- **G** Garbage — browse and recover deleted files
- **H** Help — show help screen
- **Y** Style Switcher — change the color theme
- **Q** Quit

---

## Safari DOS File Browser

The file browser is where you manage files and folders.

**Navigation:**
- **Up / Down** — move through the file list
- **Home / End** — jump to first or last item
- **Page Up / Page Down** — jump several items
- **Backspace** — go to the parent directory
- **H** — jump to your home directory

**Selecting files:**
- **Space** — toggle selection on the current file
- **A** — select all visible items

**File operations:**
- **C** — copy selected files to another folder
- **M** — move selected files to another folder
- **R** — rename the selected file
- **U** — duplicate the selected file
- **N** — create a new folder
- **X** — move selected files to Garbage (recoverable)
- **I** — show file information (size, date, permissions)
- **P** — toggle read-only protection on a file

**View options:**
- **.** — show or hide hidden files (dot-files)
- **/** — filter files by name
- **S** — cycle sort order (name, date, size, type)
- **F** — open favorites list

---

## Safari DOS Devices

Press **D** from the Safari DOS Main Menu to see available drives
and volumes.

- **Up / Down** — select a drive
- **Enter** — open the drive in the file browser
- **Escape** — go back

---

## Safari DOS Garbage

Press **G** from the Safari DOS Main Menu to see deleted files.

- **Up / Down** — browse deleted files
- **Enter** — restore the selected file to its original location
- **Delete** — permanently remove the file (no recovery)
- **Escape** — go back

Deleted files stay in Garbage until you permanently remove them
or restore them. This gives you a safety net.

---

## Safari DOS Favorites

Favorites let you bookmark frequently-used folders.

- **Up / Down** — select a favorite
- **Enter** — open it in the file browser
- **F** — toggle the current folder as a favorite (add or remove)
- **Escape** — go back

---

## Safari Fed Mastodon Client

Safari Fed is a calm, keyboard-driven Mastodon client. It treats the
fediverse like a retro message system — more Pine or BBS reader than
an infinite-scroll social app.

Run **safari-fed** from the command line to start it. If no Mastodon
credentials are configured it opens in demo mode with a seeded local
packet so you can explore the interface.

---

## Safari Fed Folders

Posts are organised into folders like a mail program. Use **Tab** and
**Shift+Tab** to cycle through them.

- **Home** — your main timeline
- **Mentions** — posts that mention you
- **Bookmarks** — posts you have bookmarked
- **Drafts** — locally saved compose drafts
- **Sent** — posts you have sent this session
- **Deferred** — posts pushed aside for later

---

## Safari Fed Navigation

- **J / Down** — next post
- **K / Up** — previous post
- **PageDown / PageUp** — skip 5 posts
- **Enter** — open the reader view for the selected post
- **T** — open the thread tree view
- **H** — jump to Home folder
- **N** — jump to Mentions folder
- **Esc / Q** — return to the index or quit

---

## Safari Fed Post Actions

- **C** — compose a new post
- **R** — reply to the selected post
- **B** — boost the selected post
- **F** — favourite the selected post
- **M** — toggle bookmark on the selected post
- **X** — toggle the post between read and unread
- **D** — defer the post to the Deferred folder
- **U** — sync from Mastodon (requires credentials)
- **W** — export the selected post or thread to Safari Writer

---

## Safari Fed Compose

Press **C** to start a new post or **R** to reply. A mini compose
editor opens inside Safari Fed.

- **Ctrl+X** — send the post
- **Ctrl+S** — save as a local draft
- **Esc** — cancel without saving

When launched from inside the full Safari Writer app, **C** and **R**
open the full Safari Writer editor instead of the mini shell.

---

## Safari Fed Multiple Accounts

You can configure more than one Mastodon identity. Each account keeps
its own folder state and compose buffer.

- **A** — cycle through configured accounts
- **1 through 9** — select an account by number

To set up accounts, copy **.env.example** to **.env** and fill in
your credentials using the MASTODON_ID_ pattern.

---

## Safari Fed Writer Handoff

Press **W** on any post or thread to export it as plain text and open
it in Safari Writer. This is useful for quoting posts, building
reading notes, or drafting a blog post from a saved thread.

In thread view the full thread tree is exported, not just the
selected post.

---

## Safari Fed Help

Press **F1** or **?** inside Safari Fed to see the full key-command
reference screen.

---

## Safari Chat Help Assistant

Safari Chat is an ELIZA-inspired help assistant. It answers your
questions using this help document. It is not an AI or LLM. It
is a pattern-matching chatbot with keyword-based retrieval.

Run **safari-chat safari_help.md** from the command line to start
it with this help file loaded.

---

## Using Safari Chat

Type your question at the USER prompt and press **Enter**.
The bot will search the help document for a relevant answer.

If it finds something, it will show you the relevant information.
If it does not, it will ask you to rephrase or tell it more.

The bot is designed to be patient and apologetic. If the app is
frustrating, it will acknowledge that. It is on your side.

---

## Safari Chat Commands

**Keyboard shortcuts:**
- **Ctrl + T** — show parsed topics from the help document
- **Ctrl + S** — show safety notice and crisis resources
- **Ctrl + H** — show help screen
- **Ctrl + Q** — quit
- **Page Up / Page Down** — scroll the conversation
- **Escape** — quit

**Slash commands (type these at the prompt):**
- **/topics** — list all topics from the help document
- **/memory** — show the conversation tree
- **/safety** — show safety notice
- **/options** — show and toggle settings
- **/clear** — clear the conversation and reset
- **/help** — show help
- **/quit** — exit

---

## Safari Chat Distress Meter

The top bar shows a distress meter. It reflects how the
conversation is going.

- **LOW** — everything is normal
- **GUARDED** — some frustration detected
- **ELEVATED** — significant frustration or confusion
- **HIGH** — strong distress signals
- **CRITICAL** — crisis language detected

As distress rises, the bot becomes more direct and less playful.
It prioritizes clear next steps and reassurance.

---

## Safari Chat Safety

Safari Chat is not a therapist, counselor, or crisis professional.
It will never pretend to be one.

If you express thoughts of self-harm or suicide, the bot will:
1. Acknowledge what you are going through.
2. Tell you clearly that it is not a professional.
3. Encourage you to contact real help immediately.

**Crisis resources:**
- **911** — emergency services (US)
- **988** — Suicide and Crisis Lifeline (call or text, US)
- **741741** — Crisis Text Line (text HOME)
- Go to your nearest emergency room
- Reach out to a trusted friend or family member

If you are in crisis, please do not rely on this program.
Contact a real person who can help you.

---

## Command Line Usage

You can also use Safari Writer from the command line without
the full interface.

**Export commands:**
- safari-writer export markdown INPUT -o OUTPUT
- safari-writer export postscript INPUT -o OUTPUT
- safari-writer export ansi INPUT

**Spelling commands:**
- safari-writer proof check INPUT
- safari-writer proof list INPUT
- safari-writer proof suggest WORD

**Format commands:**
- safari-writer format encode INPUT -o OUTPUT
- safari-writer format decode INPUT -o OUTPUT
- safari-writer format strip INPUT -o OUTPUT

**Mail merge commands:**
- safari-writer mail-merge inspect DATABASE
- safari-writer mail-merge subset DATABASE --field N --low A --high E
- safari-writer mail-merge append BASE OTHER -o OUTPUT
- safari-writer mail-merge validate DATABASE

**Safari Fed commands:**
- safari-fed
- safari-fed --folder Home|Mentions|Bookmarks|Drafts|Sent|Deferred
- safari-fed --account NAME

---

## File Types

Safari Writer works with these file types:

- **.sfw** — Safari Writer formatted document (includes formatting codes)
- **.txt** — plain text (no formatting)
- **.md** — Markdown files

Safari Writer can also open source code files with syntax
highlighting: .py, .js, .rs, .go, .java, .c, .cpp, .h, .sql
and others. These are read-only for reference.

---

## Tips and Troubleshooting

**The cursor is not where I expect it.**
Check if you are in Insert or Type-over mode. The status bar
shows which mode is active. Press Insert to toggle.

**My formatting markers look strange.**
That is normal. Formatting shows as visible markers in the
editor (like ← for bold). They will render correctly when
you print or export.

**The proofreader flags words I know are correct.**
Add them to your personal dictionary. Press **W** in the
Proofreader to save your accepted words.

**I accidentally deleted a file.**
Check Safari DOS Garbage. Press **G** from the Safari DOS menu.
Your file may still be there and recoverable.

**I cannot find my file.**
Use Safari DOS (press **O** from the Main Menu) to browse
your folders. Press **/** to filter by name.

**The app crashed or froze.**
Try restarting. If the problem persists, check whether your
document file is very large or contains unusual characters.

**I want to change the colors.**
Press **X** from the Main Menu (or **Y** in Safari DOS) to
open the Style Switcher. Browse themes with arrow keys and
press Enter to apply.

**How do I print my document?**
Press **P** from the Main Menu. Choose ANSI preview to see it
on screen, or Markdown/PostScript to export to a file.

**How do I undo?**
Press **Ctrl + Z** to undo the last action in the editor.

---

## About Safari Writer

Safari Writer is a word processor, built with Python and the 
Textual framework.

It includes four applications:
- **Safari Writer** — the word processor
- **Safari DOS** — the file manager
- **Safari Chat** — the help assistant
- **Safari Fed** — the Mastodon client

All three share the same retro text-mode aesthetic and can be
run independently or together.

Safari Chat is powered by ELIZA-style pattern matching and
keyword retrieval. It is not an artificial intelligence. It
searches this document for answers and responds conversationally.

If you are frustrated, that is understandable. These old-style
interfaces take some getting used to. But once you learn the
keyboard shortcuts, they can be very fast and satisfying to use.

Take it one step at a time. You will get there.
