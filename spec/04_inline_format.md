Here is the specification for the Inline Formatting features and UI behavior for Safari Writer, focusing on how these elements surface to the user.

______________________________________________________________________

## 11. Inline Formatting UI Model

Safari Writer relies on a "what you see is what you mean" approach rather than strict WYSIWYG. Formatting instructions are embedded directly into the text stream as non-printing control characters.

-

**Visual Representation**: When an inline command is executed, the UI displays a specific symbol or changes the text rendering (e.g., inverse video) to indicate the formatting change. These markers do not appear on the final printed page.

-

**Sequential Logic**: Formatting commands apply to all text following the marker until another marker reverts or changes the setting.

## 12. Global Format Overrides

Users can dynamically alter the master layout settings (defined in the Global Format screen) at any point mid-document.

-

**Insertion UI**: The user presses the designated shortcut for the override (e.g., altering the Left Margin). The UI displays a corresponding control character at the cursor's location.

-

**Value Entry**: The user types the new numerical value immediately after this control character.

-

**Reversion**: To return to the original layout, the user inserts the same command sequence followed by the original value at the end of the affected text.

## 13. Text Styling

Styling commands wrap around text or alter its display state on the screen.

-

**Bold Print**: The user inserts a toggle command at the beginning and end of the target text. The UI places a specific marker (traditionally a Left Arrow) at both boundaries to represent the start and finish of the bold styling.

-

**Elongated (Double-Width) Print**: The user inserts a toggle command at the start and end of the text. The UI displays an "E" symbol at these boundaries.

-

**Underlining**: Activating the underline command toggles the UI into inverse video mode. All subsequently typed characters appear highlighted in inverse video until the command is toggled off.

-

**Subscripts & Superscripts**: The user inserts a directional command before and after the affected characters. The UI displays upward or downward pointing arrows to indicate the shift above or below the baseline.

## 14. Alignment & Tabular Data

-

**Centering Text**: The user places a center command at the absolute beginning of a line. The line must be terminated with a standard carriage return.

-

**Blocking Text Right**: The user places a doubled command at the beginning of a line to flush it against the right margin. This line must also end with a carriage return.

-

**Custom Tabs**: Users can override the default tab stops (which appear every 5 spaces). Press `Ctrl+T` at any column to set or clear a tab stop at that position. Press `Ctrl+Shift+T` to clear all tab stops at once. The UI updates the row of arrows in the top margin header immediately to reflect the current tab placements.

## 15. Document Structure

-

**Headers and Footers**: The user enters a header or footer command followed by the desired text. This must exist on its own dedicated screen line and end with a carriage return.

-

**Auto-Page Numbering**: The user types the `@` symbol within the text of a header or footer. The UI displays the `@` symbol as a dynamic placeholder where the page number will generate during printing. A separate command can be inserted to define a custom starting page number.

-

**Section Headings**: The user inserts a heading command, types a hierarchy level number (1 through 9), and then types the heading text. The UI displays an inverse "H" followed by the level number. During printing, the software automatically numbers and increments these sections (e.g., 1.1, 1.2, 2.0).

-

**Page Eject (Hard Page Break)**: The user inserts the page eject command followed by a carriage return to force the printer to skip to the top of the next page.

-

**Chaining Print Files**: The user places a chaining command at the very end of a document, followed by the filename of another document. This links the files together so they print sequentially as a single continuous document.

______________________________________________________________________

Would you like me to draft the specification for the Proofreader (spelling verification) module and its UI next?
