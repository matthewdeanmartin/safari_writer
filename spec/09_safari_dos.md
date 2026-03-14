# Safari DOS Product Specification

## 1. Purpose

Safari DOS is a file management environment designed to pair with an AtariWriter-style word processor while running on modern desktop operating systems. It should feel like Atari DOS in tone, flow, and user expectations, while behaving like a safe, cross-platform Python desktop application for people doing real work on Windows, macOS, and Linux.

Safari DOS is not a nostalgia skin pasted onto a modern file picker. It is a structured file operations console with Atari-era interaction patterns, reduced complexity, strong defaults, and visible system state. Its mission is to make common file management tasks understandable, dependable, and low-risk for users who are primarily working with documents.

The product must preserve the spirit of Atari DOS:

- menu-driven operation
- lettered actions
- plain-language prompts
- visible current target/location
- strong sense of device, file, and operation
- lightweight help at every step
- reversible, safety-first behavior

The product must not preserve the limitations of Atari DOS where those limitations are harmful on modern systems.

## 2. Product Goals

Safari DOS must:

- provide a complete file management shell for document-centric desktop use
- support modern folders, filenames, volumes, removable media, and user directories
- keep users oriented at all times with explicit source, destination, and action context
- make risky actions safe by routing deletions to garbage/trash instead of permanently deleting
- work without shelling out to operating system commands for core features
- rely primarily on Python standard library and Python-native cross-platform libraries where needed
- integrate naturally with an AtariWriter-style editor
- make bulk operations understandable rather than magical
- make every action inspectable before commitment when that action changes user data

## 3. Non-Goals

Safari DOS is not:

- a command-line shell replacement
- a developer power tool optimized for scripting
- a disk utility for partitioning, formatting drives, or low-level repair
- a synchronization client
- a backup system
- a permanent-delete interface
- an implementation of historical Atari filesystem formats
- a file manager that depends on invoking external shell commands

## 4. Design Principles

### 4.1 Atari DOS Vibes, Modern Reality

The system must look and behave like an Atari DOS descendant. The user should feel that they are selecting operations from a trusted machine utility, not wandering through a modern visual desktop.

The interaction model should emphasize:

- one main menu
- clear lettered selections
- operation-specific subflows
- compact textual layouts
- stable screen regions for status, prompts, results, and help hints
- keyboard-first interaction
- minimal decoration

### 4.2 Safety Over Speed

Destructive behavior is forbidden. Any operation that would normally delete user content must instead move it to the platform trash/garbage mechanism or to Safari DOS garbage management.

The system should prefer:

- confirmation for state-changing actions
- preview before bulk actions
- explicit target naming
- undo where feasible
- safe failure over partial silent success

### 4.3 Consistency Over Cleverness

Every operation should follow a familiar structure:

1. show the operation name
1. ask for source scope
1. ask for destination or parameter changes
1. show a summary
1. require explicit execution
1. report outcome in plain language

### 4.4 Useful for Writers

The primary user is someone managing manuscripts, notes, drafts, exports, templates, and project folders. The system should prioritize document workflows over generic system administration.

## 5. Supported Platforms

Safari DOS must support:

- Windows
- macOS
- Linux

Cross-platform behavior should be as consistent as possible, while respecting each platform’s filesystem conventions, trash behavior, path formats, and user document locations.

## 6. Core User Model

Safari DOS presents the filesystem in Atari-like terms, adapted for modern systems.

### 6.1 Devices

A device is any mounted, browsable storage root that a user can access through Safari DOS. Examples include:

- system drive or primary volume
- external drive
- removable USB storage
- mounted network location if exposed through the local filesystem
- user home area shortcuts such as Documents

The UI may present devices as numbered or lettered targets for fast selection, but the user must also see the friendly modern name of each location.

### 6.2 Working Location

Safari DOS always has a current working location. This is the folder whose contents are currently being listed, filtered, acted on, or handed off to the word processor.

### 6.3 File Set

A file set is the current selection scope for an operation. It may consist of:

- one file
- all visible files in the current folder
- all matching files by pattern or filter
- one folder
- multiple selected entries

### 6.4 Garbage

Garbage is the safe holding area for deleted items. Safari DOS treats deletion as relocation to garbage, never permanent removal.

## 7. UI and Interaction Specification

## 7.1 Overall Presentation

The interface must evoke Atari DOS:

- fixed-layout screen regions
- high-contrast text presentation
- blocky, simple framing
- monospaced or Atari-inspired bitmap-friendly typography if practical
- no ornamental chrome
- no floating modern panels unless absolutely required by accessibility or platform rules

The interface should include these persistent regions:

- title/status line
- current device and path line
- main body for directory or operation content
- prompt line
- help hint or message line

### 7.1.1 Tone of Language

System language should be short, direct, and operational.
Examples of preferred tone:

- Select Function
- Source Location?
- Destination Folder?
- Move file to Garbage?
- Copy complete
- 3 files moved to Garbage
- Name already exists
- Operation cancelled

Avoid modern marketing language, conversational fluff, or visually noisy labels.

## 7.2 Input Model

Safari DOS must be keyboard-first.

Required input patterns:

- single-letter menu selection
- arrow navigation in lists
- Return/Enter to accept
- Escape to back out or return to menu
- dedicated help key binding
- type-to-jump in file lists
- optional hotkeys for frequent actions

Mouse support is allowed, but keyboard operation must be complete and first-class.

## 7.3 Menu Structure

The product should use a main menu modeled on Atari DOS-style operation selection, but updated for modern needs.

Suggested main menu categories:

- File List
- Open in Writer
- Copy
- Move
- Rename
- New Folder
- Duplicate
- Send to Garbage
- Restore from Garbage
- Protect
- Unprotect
- Search
- Sort / Filter
- Make Alias / Shortcut
- Show Info
- Refresh
- Favorites
- Devices
- Help
- Quit

The specific lettering may vary, but the scheme must remain stable and memorable.

## 7.4 File Listing Screen

The file listing screen is the heart of Safari DOS.

It must display:

- entry name
- entry type
- size for files
- modified date/time
- protected/locked status if present
- optional indicator for hidden items when showing hidden entries
- optional indicator for alias/shortcut/symlink-like entries

It should support multiple views while preserving Atari-style simplicity:

- compact list view as default
- optional detailed list view

No icon-heavy grid view. The product identity is textual, list-based, and operational.

## 7.5 Prompting Model

Every operation must have an explicit prompt sequence. Prompts should always reflect the current operation and current defaults.

Example structure:

- Source?
- Destination?
- Name?
- Apply to all matching files (Y/N)?
- Proceed (Y/N)?

Defaults may be shown, but must never conceal the effect of the action.

## 7.6 Help Model

Help must be available everywhere.

Help should be:

- context-sensitive
- concise first, with optional expansion
- written in operational language
- specific to the current prompt or menu item

Help content should explain:

- what the operation does
- what input is expected
- what happens next
- any safety behavior
- any limitations

## 8. Filesystem Scope and Capabilities

Safari DOS should support all normal user-facing filesystem tasks that are practical through Python-native mechanisms and appropriate for a document-centric file manager.

### 8.1 Browsing and Navigation

Required capabilities:

- list current folder contents
- enter folder
- go up one level
- jump to home
- jump to documents folder
- jump to desktop folder where available
- jump to recent working locations
- switch devices/volumes
- return to previous location
- refresh listing
- show hidden files optionally

### 8.2 File Operations

Required capabilities:

- copy files
- move files
- duplicate files in place or to chosen destination
- rename files
- rename folders
- create new folder
- open file in AtariWriter clone when applicable
- reveal file details
- move file to garbage
- move folder to garbage
- restore from garbage

### 8.3 Folder Operations

Required capabilities:

- create folder
- rename folder
- copy folder recursively
- move folder recursively
- duplicate folder
- send folder to garbage
- inspect folder contents summary

Any folder-affecting operation must clearly indicate whether child contents are included.

### 8.4 Bulk Operations

Required capabilities:

- act on multiple selected files
- act on all visible entries
- act on pattern matches
- act on filtered results
- preview bulk targets before commit
- skip, replace, or rename-on-conflict behavior when appropriate

Bulk actions must not be silent.

### 8.5 Search and Filtering

Required capabilities:

- search by name
- search within current folder
- search recursively from current folder
- filter current listing by name pattern
- filter by file type or extension
- sort by name, date, size, type
- toggle ascending/descending

Full text content search is optional unless it can be implemented without shelling out and without undermining product simplicity.

### 8.6 Metadata and Info

Required capabilities:

- show file size
- show modified time
- show created time where available
- show type/extension
- show full path
- show permissions/locked state in user-friendly form
- show item count for folders
- show total selected size

### 8.7 Protection / Locking

Safari DOS should expose a writer-friendly form of protection analogous to Atari DOS protect/unprotect.

This feature must allow users to:

- mark a file as protected/read-only where the platform supports it
- remove protected/read-only state where the platform supports it
- see protected status in listings

The language should use Protect and Unprotect, with a help description that explains the modern equivalent.

### 8.8 Favorites and Working Sets

Required capabilities:

- save favorite locations
- return quickly to favorite project folders
- pin recent project folders
- optionally remember last writer project locations

## 9. Garbage and Safety Specification

## 9.1 Deletion Policy

Safari DOS must never offer permanent delete in normal UI.

Any delete-like action must instead:

- move selected item or items to the operating system trash where possible, or
- move them into Safari DOS garbage using a reversible mechanism if platform trash integration is not available for a case

The interface should use the phrase Send to Garbage or Move to Garbage, not Delete.

## 9.2 Restore Policy

Users must be able to:

- browse Safari DOS garbage-managed items when applicable
- restore items to original location where feasible
- restore to alternate location if original location is unavailable or blocked

## 9.3 Safety Confirmations

Confirmation is required for:

- moving items to garbage
- moving files or folders across devices/volumes
- bulk rename
- recursive copy/move of folders
- replace-on-conflict
- restoring items when name collisions exist

## 9.4 Conflict Handling

When a destination already contains an item with the same name, Safari DOS must not guess silently.

Allowed conflict responses:

- skip
- rename copied/moved item
- replace, only with explicit confirmation
- apply chosen rule to remaining conflicts

## 9.5 Interrupted Operations

If a copy or move is interrupted, Safari DOS must report clearly:

- what completed
- what failed
- what remains uncertain
- what the user can safely do next

## 10. Integration with AtariWriter Clone

Safari DOS is intended to pair tightly with an AtariWriter-like application.

Required integration behaviors:

- open selected document in writer
- save from writer back into user-chosen Safari DOS location
- support Save As through Safari DOS location selection
- return from writer to Safari DOS at same project location when practical
- expose recent documents and recent project folders shared with the writer
- present writer-friendly file filters by default for common document types

Optional but desirable behaviors:

- create new document from Safari DOS
- duplicate a document as new draft
- create dated backup copy before opening
- show template folders as favorites

## 11. Filename and Path Behavior

Safari DOS must support modern filenames, Unicode, and long paths as allowed by platform and Python support.

The interface should simplify presentation without limiting capability.

Required behaviors:

- display full modern filenames
- truncate visually only when needed, never in underlying operation logic
- preserve case as stored by the platform
- allow spaces and modern punctuation as supported
- clearly distinguish file extension when relevant
- display full path on demand

The product may optionally support pattern matching inspired by historical wildcard behavior, but it must work predictably for modern filenames.

## 12. Device and Location Model

Safari DOS should adapt Atari drive thinking into a modern location model.

### 12.1 Device Screen

A Devices view should show accessible roots and important locations, such as:

- primary system volume
- removable volumes
- home folder
- documents
- downloads
- desktop where meaningful
- configured favorites

### 12.2 Naming

Each device/location should show:

- short selector token
- friendly name
- mount or path summary
- status if unavailable or removable

### 12.3 Removable Media

Safari DOS should support removable storage as regular browseable devices. It may support safe refresh and state updates when media appears or disappears.

It must not attempt low-level drive formatting or shell-based media operations.

## 13. Operation Specifications

## 13.1 File List

Purpose: show contents of the current location and enable fast selection.

Must support:

- scrolling
- selection movement
- multi-select mode
- sort and filter
- open folder
- open file in writer or associated internal handler
- show info
- jump to first matching typed name

## 13.2 Copy

Purpose: create a second copy of selected files or folders.

Must support:

- single or multiple source entries
- destination selection
- recursive copy for folders
- conflict handling
- progress display
- completion summary

## 13.3 Move

Purpose: relocate files or folders.

Must support:

- same-device and cross-device moves
- explicit destination choice
- folder recursion awareness
- conflict handling
- progress and result summary

## 13.4 Rename

Purpose: change item names safely.

Must support:

- single-item rename
- batch rename for selected items
- pattern-based rename only if understandable and previewable
- collision prevention
- preview before applying batch changes

## 13.5 Duplicate

Purpose: make a nearby copy optimized for draft-based writing workflows.

Must support:

- duplicate in same folder
- duplicate to selected folder
- automatic safe name generation when desired
- preservation of file type/extension

## 13.6 New Folder

Purpose: create project folders and organizational containers.

Must support:

- folder creation in current location
- validation of name
- immediate visibility in listing
- optional jump into newly created folder

## 13.7 Send to Garbage

Purpose: safely remove visible clutter without permanent destruction.

Must support:

- file and folder targets
- multi-select
- confirmation summary
- clear success/failure report
- restore availability where feasible

## 13.8 Restore from Garbage

Purpose: recover mistakenly discarded items.

Must support:

- browsing recoverable items
- restore to original location
- alternate restore location
- collision handling

## 13.9 Protect / Unprotect

Purpose: guard important drafts or reference files from accidental editing.

Must support:

- file-level protection toggle
- folder behavior only if clearly defined and platform-appropriate
- visible status indicator
- help text describing actual modern effect

## 13.10 Search

Purpose: locate files quickly in project folders.

Must support:

- name search
- current folder or recursive scope
- display matching results in list form
- transition from results into file operations without losing orientation

## 13.11 Show Info

Purpose: make state visible.

Must support:

- one-item detail view
- selected-items summary view
- folder summary view

## 14. Status, Progress, and Messaging

Safari DOS must always tell the user what it is doing.

### 14.1 Status Messages

Required message categories:

- ready state
- current operation state
- prompt request
- success confirmation
- warning
- recoverable error
- cancelled action

### 14.2 Progress Displays

Longer operations such as recursive copy or bulk move should show:

- operation name
- current item
- items completed / total
- bytes completed where practical
- skip/failure counts where relevant

### 14.3 End Reports

State-changing operations should end with a plain-language summary such as:

- 12 files copied
- 1 file skipped; name conflict
- 3 items moved to Garbage
- 2 folders restored

## 15. Error Handling Requirements

Errors must be understandable to non-technical users.

The system should prefer messages such as:

- File not found
- Destination unavailable
- Name already exists
- You do not have permission to change this item
- Item is protected
- Cannot restore to original location
- Device removed during operation

Avoid raw tracebacks or platform jargon in user-facing UI.

Where useful, errors should include a next step.

## 16. Accessibility and Usability

Safari DOS must remain faithful to Atari-era style without becoming inaccessible.

Requirements:

- fully keyboard operable
- readable high-contrast mode
- scalable text or zoom support
- visible focus state
- no information conveyed by color alone
- screen-reader-friendly control labeling if a GUI toolkit is used

The retro style is a presentation choice, not a reason to deny accessibility.

## 17. Cross-Platform Behavioral Requirements

Safari DOS must abstract platform differences so users experience one coherent product.

Required consistency areas:

- browsing files and folders
- copy/move/rename behavior
- trash/garbage semantics
- path handling in UI
- file info presentation
- recent locations and favorites

Where platforms differ materially, the help text should explain the difference plainly.

## 18. Python-First Technical Boundary

This product must only include user-visible features that can be supported through Python-native mechanisms and libraries appropriate to the target platforms.

Feature boundary rules:

- core functionality must not depend on shelling out to OS commands
- any feature that requires shelling out is out of scope
- third-party Python libraries are acceptable when they improve safe cross-platform behavior
- platform integration libraries are acceptable for locating user folders, handling trash/garbage, or managing compatibility gaps

This boundary is a product constraint, not just an implementation preference.

## 19. Data Integrity Requirements

Safari DOS must prioritize preserving user work.

Requirements:

- do not modify file contents during copy, move, duplicate, rename, or garbage operations
- preserve timestamps and metadata where practical and appropriate
- avoid partial hidden transformations
- verify target existence and accessibility before beginning large operations when possible
- fail safely and visibly

## 20. Preferences and Customization

Customization should be limited and disciplined.

Allowed customization areas:

- color theme variants within retro aesthetic
- default sort order
- whether hidden files are shown
- whether file extensions are emphasized
- favorite locations
- confirmation strictness for advanced users, without ever enabling permanent delete

Do not let customization dilute the Atari DOS identity.

## 21. Suggested Information Architecture

### Main Menu

- Directory / File List
- Writer
- Copy
- Move
- Rename
- Duplicate
- New Folder
- Garbage
- Protect
- Search
- Sort / Filter
- Devices
- Favorites
- Info
- Help
- Quit

### Subscreens

- Directory Listing
- Operation Prompt Screen
- Conflict Resolution Screen
- Progress Screen
- Info Screen
- Devices Screen
- Favorites Screen
- Garbage Screen
- Help Screen

## 22. Example Usage Patterns

### 22.1 Writer Project Setup

User starts Safari DOS, selects Documents, enters a manuscript folder, creates a new folder for Drafts, opens a template in the writer, and saves a new draft there.

### 22.2 Safe Cleanup

User filters for backup files older than a chosen point, reviews the list, selects several, and sends them to Garbage. Nothing is permanently deleted.

### 22.3 Draft Duplication

User selects CHAPTER03, duplicates it in place, gets CHAPTER03 COPY or similarly safe naming, renames it to CHAPTER03-REVISION, then opens it in writer.

### 22.4 External Transfer

User plugs in removable storage, switches devices, copies a folder of documents to that device, and receives a summary report with any skipped conflicts.

### 22.5 Recovery

User accidentally sends a notes folder to Garbage, opens Garbage, restores it, and Safari DOS returns it to its original project folder or asks for an alternate location if needed.

## 23. Out-of-Scope Features

The following are explicitly out of scope:

- permanent delete UI
- low-level disk formatting
- partition management
- shell-command wrappers
- shell-dependent archive tools
- file permission editors beyond simple protect/unprotect semantics
- background daemon behavior
- cloud sync-specific management features unless exposed as ordinary local files
- terminal emulation

## 24. Acceptance Criteria

Safari DOS is successful when:

- a user can manage modern writing-project files entirely within Safari DOS and the paired writer
- the interface feels recognizably inspired by Atari DOS
- the product never requires shelling out for core file operations
- deletion is always safe and reversible by routing to garbage/trash
- common tasks on Windows, macOS, and Linux behave consistently enough to be learned once
- every state-changing operation is explicit, understandable, and recoverable where reasonable

## 25. Final Product Statement

Safari DOS should feel like the file manager that Atari DOS would have become if it had grown up around modern document workflows, cross-platform Python tooling, and an uncompromising belief that users should never lose work because a utility got clever.
