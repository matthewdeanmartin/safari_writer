# Safari DOS: Preview and Archive Management Specification

## 1. Overview

This document specifies the "Modern Power" extensions for Safari DOS. While Safari DOS maintains an Atari-inspired core, these features provide essential modern utility: the ability to visually inspect file contents without opening them in the writer, and the ability to manage compressed archives (ZIP) for project portability.

## 2. Right-Pane Preview System

The Safari DOS interface shall be enhanced with a persistent or toggleable right-hand preview pane. This pane provides immediate context for the currently highlighted file in the directory list.

### 2.1 UI Layout
- **Split Screen:** The main body area is divided into a Left Pane (Directory Listing) and a Right Pane (Preview).
- **Ratio:** Approximately 50/50 or 60/40 (Left/Right) split, adjustable if the platform allows, but fixed by default to maintain the blocky, structured look.
- **Visual Style:** The preview pane should be framed with the same blocky character-based borders used in the rest of the application.

### 2.2 Content Types
The preview pane dynamically updates as the user navigates the file list:

- **Image Preview:** 
    - Supports common formats: PNG, JPG, BMP, GIF.
    - Renders as a scaled-to-fit version of the image.
    - Uses platform-native primitives or a lightweight image library (e.g., Pillow) to generate a textual or low-resolution visual representation if running in a pure terminal, or a high-fidelity rendering in a GUI-backed environment.
- **Text Preview:**
    - Supports `.txt`, `.sfw` (Safari Writer), `.md`, `.py`, `.json`, `.ini`, `.sfw`.
    - Displays the first 25-50 lines of the file.
    - Monospaced font matching the system theme.
- **Metadata/Info Preview:**
    - For all files (including those without visual previews), shows an expanded info block.
    - Includes: Full Filename, Size (Formatted), Created/Modified dates, Permissions, and File Type description.
- **Folder Preview:**
    - Shows a summary of the folder contents (item count, total size) and a "Peek" at the first few files inside.

### 2.3 Interaction
- **Automatic Update:** Preview updates instantly as the selection moves.
- **Toggle (V):** The user can toggle the preview pane visibility using the `V` key (View Toggle).
- **Fullscreen Preview (Space):** Pressing Spacebar expands the preview to fill the main body area for closer inspection.

## 3. Archive Management (ZIP Support)

Safari DOS adds support for the industry-standard ZIP format using Python's built-in `zipfile` module.

### 3.1 Compression (Z: Zip Archive)
- **Selection:** Operates on the current selection (Single file, Multiple files, or Folder).
- **Workflow:**
    1. User presses `Z`.
    2. Prompt: `Archive Name?` (Defaults to `archive.zip` or `current_folder.zip`).
    3. Operation: Safari DOS creates a compressed ZIP file at the target location.
    4. Progress: Shows a progress bar or "Archiving: [filename]" status.
- **Safety:** If the archive name exists, it prompts for `(O) Overwrite` or `(A) Append`.

### 3.2 Decompression (U: Unzip Archive)
- **Selection:** Only available when a `.zip` file is highlighted.
- **Workflow:**
    1. User presses `U`.
    2. Prompt: `Extract to [current_folder] (Y/N)?` or `Destination Path?`.
    3. Operation: Safari DOS extracts all contents, preserving the internal directory structure.
    4. Progress: Shows "Extracting: [filename]" status.
- **Safety:** Prompts for confirmation if extracting would overwrite existing files.

## 4. Menu Integration

The Main Menu is updated to include these new lettered actions:

- **(V) View Toggle:** Show/Hide Preview Pane.
- **(Z) Zip Archive:** Compress selected items.
- **(U) Unzip Archive:** Extract highlighted ZIP file.

## 5. Technical Requirements

- **Compression:** Must use `zipfile` from the Python Standard Library.
- **Image Rendering:** Should attempt to use `PIL` (Pillow) for scaling. If unavailable, fall back to "Image Metadata only" or a simple "Binary" view.
- **Performance:** Previews must be loaded asynchronously or in a way that does not "stutter" the directory navigation. Large text files should be read partially (first few KB) rather than fully loaded.

## 6. Safety and Error Handling

- **Corrupt Archives:** If a ZIP file is corrupt, Safari DOS must report "Error: Invalid or Corrupt Archive" instead of crashing.
- **Permission Errors:** Clearly report if an archive cannot be created due to write-protection or system permissions.
- **Disk Space:** Check for available space before beginning large compression/decompression operations.
