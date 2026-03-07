# Spec 09: Demo Mode

## 1. Overview

Safari Writer should include a built-in **Demo Mode** that opens a bundled sample document from the Main Menu.

The demo serves two purposes at once:

1. it is a **guided getting-started document** for new users; and
2. it is a **live showcase of editor features**, especially the formatting and structure controls that are normally represented by in-band markers.

This spec defines the user-facing behavior for that demo mode and requires implementation in this phase.

---

## 2. Goals

- Give first-time users a safe, obvious way to explore Safari Writer without preparing their own file first.
- Show the editor in a realistic state with visible control markers already present in the text.
- Demonstrate **all currently supported inline and structural document markers** in one bundled sample.
- Keep the demo content useful as a quick-reference or onboarding document, not just a synthetic test fixture.
- Ship the demo with the installed `safari_writer` package so it is always available offline.

### Non-goals

- No separate tutorial screen or wizard.
- No network-downloaded examples.
- No special editor-only rendering path just for the demo.
- No hidden or partial marker set: the same control characters used by normal documents must be used by the demo document.

---

## 3. Entry Point

## 3.1 Main Menu item

The Main Menu must include a dedicated item for launching Demo Mode.

### Requirements

- The item must appear alongside the other top-level Main Menu actions.
- It must have a unique keyboard accelerator that does not conflict with existing menu bindings.
- Selecting it must immediately load the demo document and open the editor.

### Intent

The feature should feel like a first-class part of the product, not a hidden debug path.

## 3.2 Startup behavior

Choosing Demo Mode must:

1. load the bundled demo document into application state;
2. reset the cursor to the top of the document;
3. clear the modified flag on initial load; and
4. enter the normal editor screen.

The editor experience after load is otherwise the standard editor experience.

---

## 4. Bundled Demo Document

## 4.1 Packaging requirement

The demo document must be stored with the application code as package data so it is available from an installed wheel or editable checkout.

### Requirements

- The file must live under the `safari_writer` package.
- The implementation must load it through package-resource access, not by assuming a repository-relative working directory.
- The bundled file format should be Safari Writer's own document format (`.sfw`) so the source remains readable in the repository while preserving all markers.

## 4.2 Editing model

The bundled demo document is treated as a **loaded copy**, not as a package asset that will be overwritten in place.

### User-visible behavior

- Opening Demo Mode gives the user a normal editable document buffer.
- Initial load must not mark the document as modified.
- If the user changes the demo, those changes are only in memory until the user explicitly saves a copy.

This avoids any implication that the installed demo asset itself is being edited directly.

---

## 5. Demo Content Requirements

## 5.1 Content tone

The demo text should read like a concise **getting started guide** for new users.

It should explain, in plain language:

- how to move around;
- how to type and edit;
- how formatting markers work;
- how to open help;
- how to preview or export;
- how to experiment safely.

The demo should be instructional, readable, and pleasant to skim from top to bottom.

## 5.2 Coverage requirement: all supported markers

The bundled demo document must visibly include examples of every currently supported inline or structural marker represented in the editor:

| Feature | Marker / concept |
|---|---|
| Bold | bold toggle |
| Underline | underline toggle |
| Elongated | elongated toggle |
| Superscript | superscript toggle |
| Subscript | subscript toggle |
| Centering | center-line marker |
| Flush right | right-alignment marker |
| Paragraph indent | paragraph marker |
| Mail merge | merge-field marker |
| Header | header-line marker |
| Footer | footer-line marker |
| Section heading | heading marker with level |
| Page eject | hard page break marker |
| Chain print | chain-file marker |
| Form blank | prompt-at-print marker |

If Safari Writer later gains additional supported markers, the demo document should be updated to include them too.

## 5.3 Document shape

The demo should be organized into short sections such as:

1. welcome / orientation;
2. navigation and editing basics;
3. inline formatting examples;
4. document-structure examples;
5. print / export hints;
6. a safe “try editing here” area.

This structure keeps the file readable while still exercising the feature set.

## 5.4 Realistic examples

Examples should use meaningful prose instead of filler whenever possible.

Preferred examples:

- a bolded phrase used for emphasis;
- an underlined word or title;
- a superscript example like `E=mc²`;
- a subscript example like `H₂O`;
- a centered title;
- a flush-right dateline or signature;
- a merge field in a form letter greeting;
- a form blank in a sample worksheet line;
- a heading example that demonstrates auto-numbering;
- a chain-print line that references another plausible filename.

---

## 6. Interaction Expectations

## 6.1 Editor help alignment

The demo should complement, not replace, the existing help screen.

- The help overlay remains the authoritative key-command reference.
- The demo should mention that `F1` or `?` opens help.
- The demo content may call out a few important shortcuts, but it should not attempt to duplicate the entire help text.

## 6.2 Safe exploration

The demo should encourage experimentation.

Recommended messaging inside the document:

- users can type directly into the demo;
- users can save a copy if they want to keep changes;
- users can reopen Demo Mode at any time to get a fresh bundled version.

---

## 7. Error Handling

If the bundled demo document cannot be loaded, the application must fail visibly rather than silently doing nothing.

### Acceptable behavior

- show a clear message in the application status area when the app can continue; or
- raise an explicit error path during testing/startup logic if the resource is missing.

### Not acceptable

- silently falling back to an empty document;
- routing to the editor with no explanation;
- pretending Demo Mode succeeded when the demo resource was unavailable.

---

## 8. Testing Expectations

The implementation should include automated coverage for:

- the presence of the Main Menu demo action;
- the app routing for the new menu action;
- loading the bundled demo document into a normal document buffer;
- confirmation that the demo resource ships with the package and is readable;
- confirmation that the demo content includes all supported marker types.

Tests should prefer existing non-UI seams where possible.

---

## 9. Documentation Expectations

Because the demo is an onboarding feature, repository docs and code comments should make its purpose clear where directly relevant.

At minimum:

- the new spec file documents the feature;
- the bundled demo content itself reads as user-facing onboarding material.

Separate README changes are optional unless the implementation naturally touches them.
