Here is the product specification for Safari Writer's Proofreader (spelling verification) module, translating the legacy functionality into a streamlined UI feature set.

---

## 16. Proofreader Module Overview

The Proofreader is an integrated spelling verification system accessed via the "Verify Spelling" option on the Main Menu. It cross-references the active document against a built-in master dictionary of over 36,000 words, as well as any user-defined custom dictionaries.

* **UI Paradigm**: The Proofreader maintains the distraction-free, terminal-style interface. When active, it displays the text almost exactly as it appears in the editor, scrolling the text upward as it checks each word.


* 
**Visual Flagging**: Correctly spelled words are displayed in standard text rendering. Unrecognized words are highlighted using inverse video to immediately draw the user's attention.



## 17. Proofing Modes

Users can interact with the Proofreader in three distinct modes depending on their workflow needs:

* **Highlight Errors**: A read-only scanning mode. The system scrolls through the document and highlights all unrecognized words in inverse video without stopping to prompt for corrections.


* **Print Errors**: A batch-processing mode. The system scans the document and displays a compiled list of all unrecognized words on-screen.


* **Correct Errors**: An interactive, step-by-step correction mode. The system halts scrolling at the first identified error and opens a "Correction Menu" in the top message window.



## 18. Interactive Correction Menu (UI)

When using the "Correct Errors" mode, the UI halts at a flagged word and presents three choices in the header:

* **Correct Word**: The user selects this to type a replacement. The UI prompts the user to enter the corrected word. After typing the correction and pressing `Enter`, the system asks "Are you sure? Y/N" as a final failsafe before replacing the text.


* 
**Search Dictionary**: If the user is unsure of a spelling, they can search the database directly from the correction prompt. The user types at least the first two letters of the word. The UI then displays a list of matching words from the dictionary at the top of the screen (up to 18 words at a time). The user can page through results until they find the correct spelling.


* 
**Keep This Spelling**: The user selects this (by simply pressing `Enter`) to bypass the highlighted word. The system immediately "memorizes" this spelling for the duration of the session, ensuring it won't be flagged again in the current document.



## 19. Standalone Dictionary Search

Users can access the dictionary database independently without initiating a full document proofing session.

* 
**Lookup UI**: The user is prompted to enter at least the first two letters of a word. The system returns a full-screen list of matching words (up to 126 words per screen page). The user can continue to page through the alphabetical list or cancel to start a new search.



## 20. Personal Dictionaries

To accommodate specialized vocabulary, proper nouns, or industry jargon, Safari Writer supports custom Personal Dictionaries.

* 
**Filing Learned Words**: At the end of an interactive "Correct Errors" session, the user can save all the words the system "memorized" (via the "Keep This Spelling" command) into a dedicated Personal Dictionary file.


* 
**Manual Dictionary Creation**: Users can proactively build custom dictionaries using the standard text editor. By typing a list of words (separated by spaces or carriage returns) and saving the file, they create a custom dictionary.


* 
**Loading Dictionaries**: Before proofing, users can load one or multiple Personal Dictionary files into active memory. The Proofreader will then cross-reference the document against both the master dictionary and the loaded custom dictionaries.



---

Would you like me to draft the final section of the specification covering the Mail Merge (database and form letter) module next?