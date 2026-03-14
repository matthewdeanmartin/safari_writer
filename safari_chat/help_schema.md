# Safari Chat Help Schema

This document defines the schema and best practices for creating help files compatible with the Safari Chat ELIZA/RAG engine.

## Document Structure

Safari Chat help files are written in Markdown and use a specific structure to enable topic retrieval and conversation branching.

### Topic Chunks
The document is split into **Topic Chunks** using a horizontal rule (`---`) on its own line. Each chunk represents a discrete unit of information that the bot can retrieve.

```markdown
# Topic Heading
Information about the topic.
---
# Next Topic
Information about the next topic.
```

### Headings
Each chunk should have a primary heading (H1 to H6). The first heading in a chunk is used as the **Topic Title** and is a valid target for branching.

### Keywords
The engine automatically extracts keywords from:
1.  Headings.
2.  **Bold** or *italicized* text.
3.  Sub-headings within the chunk.

Keywords are used to match user queries to the most relevant chunk.

## Conversation Trees (Branching)

Branches allow the bot to guide the user through a conversation by offering related topics.

### Defining Branches
Branches are defined using Markdown list items containing a link to another heading within the document.

**Syntax:**
`- [User-Visible Label](#Heading-Target)`

**Example:**
```markdown
## Main Menu
The Main Menu is the central hub of Safari Writer.
- [How do I save?](#Saving Files)
- [How do I print?](#Printing)
```

### How Branches Work
1.  **Bot Suggestion:** When a chunk with branches is retrieved, the bot appends "Would you like to know more about:" followed by the labels.
2.  **User Selection:** if the user types the exact label (case-insensitive), the bot immediately retrieves the target section.

## Instructions for Clankers (LLMs)

When generating help documentation for Safari Chat, follow these rules:

1.  **Surgical Chunks:** Keep each topic focused. If a section is too long, split it into multiple chunks using `---`.
2.  **Explicit Branching:** Every major topic should have at least 2-3 branches to related topics or common follow-up questions.
3.  **Keyword Density:** Use **bolding** for important terms to ensure the keyword extractor picks them up.
4.  **Natural Labels:** Branch labels should look like things a human would actually type (e.g., "Tell me about saving" rather than "GO_SAVE_SECTION").
5.  **Target Integrity:** Ensure every `(#Target)` matches an actual heading in the document.

## Schema Demonstration

A well-structured chunk looks like this:

```markdown
## Formatting Text
You can **bold**, **underline**, and **italicize** text in the editor.
- [What are the shortcuts?](#Keyboard Shortcuts)
- [How do I remove formatting?](#Clearing Styles)
---
```
