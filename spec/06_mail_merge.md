Here is the product specification for Safari Writer's Mail Merge (database and form letter) module, translating the legacy database functionality into a clean, modern UI specification.

______________________________________________________________________

## 21. Mail Merge Module Overview

Mail Merge is an integrated, flat-file database program utilized primarily for generating form letters, managing contacts, and compiling lists .

-

**UI Paradigm**: The module operates in its own dedicated workspace, accessed via the Main Menu .

-

**Status Headers**: The Mail Merge menu continuously displays the available memory ("Bytes Free") and the remaining record capacity ("Records Free," up to a maximum of 255 records per file) .

## 22. Database Schema (Record Formatting)

Before entering data, the user establishes a "Record Format" (the database schema) which dictates the structure of every entry in that file.

-

**Default Template**: The system provides a default 15-field address book template (e.g., Last Name, First Name, Company, Address, City, State, Zipcode) .

-

**Custom Formatting**: Users can dynamically edit the template to create custom databases.

-

*Field Operations*: Users can delete unneeded fields, insert new ones, or rename existing fields (up to 12 characters for the field name) .

-

*Character Limits*: Users can manually add or remove character spaces for each field .

-

**Schema Constraints**: A single record format supports a maximum of 15 fields, and each field is strictly capped at a 20-character maximum .

## 23. Data Entry and Record Management (UI)

Once the schema is defined, the UI transitions to a form-fill interface for data entry.

-

**Data Entry**: The user types data into the current field and presses `Enter` to jump to the next field . Empty fields are permitted and will remain blank. Upon completing the final field, the UI prompts a "Definitions Complete Y/N?" confirmation to commit the record to memory .

-

**Updating Records**: Users can trigger an "Update Menu" to browse and manage existing records .

-

*Navigation*: Modern mappings like `Page Up` and `Page Down` cycle through previous and next records (adapting the legacy `[Select]` and `[Option]` mappings) .

-

*Deletion*: The user presses `Ctrl + D` to delete the currently displayed record, protected by a final "Are You Sure? Y/N" failsafe prompt .

-

**Appending Files**: Users can merge an external Mail Merge file from disk into the active file in memory, provided both files share the exact same number of fields and field character lengths .

## 24. Building Subsets (Filtering)

Safari Writer includes a filtering mechanism to isolate specific records for targeted printing (e.g., sending letters only to contacts in a certain state) .

-

**Subset UI**: The "Build Subset" screen displays a list of all active fields alongside "Low Value" and "High Value" input columns .

-

**Filter Logic**: The user defines an alphabetical or numeric range (e.g., entering "A" for Low Value and "E" for High Value) .

-

**Execution**: The user specifies which field number to apply this range to, and the system temporarily filters the active database so that only records matching those criteria are accessible for updating or printing .

## 25. Document Integration (Word Processor Side)

The core value of the Mail Merge module is its integration with the standard text editor .

-

**The Merge Character**: While typing a standard text document (like a form letter), the user inserts a specialized "Database Merge Character" (represented by an inverse `@` symbol) .

-

**Field Targeting**: Immediately following the `@` symbol, the user types the specific field number (1 through 15) they want to inject into that spot (e.g., `@1` for Last Name).

-

**Print-Time Execution**: When the user prints the document, Safari Writer halts and prompts for a "Database Filename". The software then automatically prints a sequential copy of the document for every individual record (or filtered subset) present in that database file, seamlessly injecting the localized data into the `@` placeholders .

______________________________________________________________________

This concludes the feature specifications mapping the classic AtariWriter 80 capabilities to the modern UI-compatible Safari Writer. Let me know if you need to detail any specific edge cases, error handling, or further shortcut mapping!
