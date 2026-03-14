Here is the specification for Safari Writer's Global Formatting module, detailing the UI behavior and the specific formatting parameters adapted from the classic system.

______________________________________________________________________

## 9. Global Format Screen (UI)

The Global Format screen acts as the master control center for document layout. It maintains a distraction-free, terminal-style interface consisting of a vertical list of layout parameters.

### User Interaction Model

-

**Navigation & Selection**: Each formatting command is represented by a single alphabetical letter on the left side of the screen. To modify a setting, the user presses the corresponding letter.

-

**Data Entry**: Upon pressing a letter, the cursor instantly jumps to the current numerical value for that command. The user types the new desired value and presses `Enter` (mapping to the classic `[Return]`) to confirm.

-

**Resetting Defaults**: The user can press `Tab` at any time to instantly restore all layout settings to their factory defaults.

-

**Exiting**: Pressing `Esc` accepts the current data and returns the user to the Main Menu.

______________________________________________________________________

## 10. Global Formatting Parameters

The following parameters dictate the overall shape and style of the printed file. Note that Atari standard measurements (such as half-lines) are preserved in Safari Writer to maintain strict UI compatibility.

### Margins & Spacing

-

**T > Top Margin**: Sets the top margin measured from the top edge of the page in half-lines. The default value is 12 (which equals one inch). Setting this to 0 allows for continuous printing without page breaks.

-

**B > Bottom Margin**: Sets the bottom margin measured from the bottom edge of the page in half-lines. The default value is 12.

-

**L > Left Margin**: Measures the left boundary in character spaces from the left edge of the page. The default is 10 , with an allowable range of 1 through 130.

-

**R > Right Margin**: Measures the right boundary in character spaces from the left edge of the page. The default is 70 , with an allowable range of 2 through 132.

-

**S > Line Spacing**: Spacing is calculated in half-lines. The default is 2 (single spacing). The user can enter 4 for double spacing or 6 for triple spacing.

-

**D > Paragraph Spacing**: Determines the amount of blank space (in half-lines) inserted between paragraphs. The default is 2.

### Multi-Column Layouts

These settings manage newspaper-style double-column printing.

-

**M > 2nd Left Margin**: Sets the left boundary for the right-hand column. The default is 8.

-

**N > 2nd Right Margin**: Sets the right boundary for the right-hand column. The default is 70.

### Typography & Styling

-

**G > Type Font**: Selects the character pitch or print style. The default is 1 (Pica, 10 characters per inch). Other standard inputs include 2 for condensed, 3 for proportional, and 6 for elite print.

-

**I > Paragraph Indentation**: Sets the number of character spaces the first line of a paragraph is indented from the left margin. The default is 5. Entering 0 creates block-style paragraphs.

-

**J > Justification**: Functions as a binary switch. The default is 0 for unjustified (ragged right) text. The user enters 1 to enable justified right margins.

### Pagination & Media Control

-

**Q > Page Number**: Defines the starting page number if the user requests numbered pages via inline formatting. The default is 1.

-

**Y > Page Length**: Tells the program where the next printed page should begin. The default is 132, which correlates to standard 8 1/2 by 11-inch paper.

-

**W > Page Wait**: A binary switch for single-sheet feeding (e.g., printing on letterhead). The default is 0 (off). Entering 1 tells the printer to halt at the bottom of each page so the user can load a fresh sheet.

______________________________________________________________________

Would you like me to outline the specification for Safari Writer's inline formatting commands (like headers, footers, and text styles) next?
