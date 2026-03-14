Below is a **compact but complete specification** for a **Markdown-based slide format for human-written presentations**. It assumes a Markdown renderer already exists and this spec defines **additional semantics and directives** for slide layout and presentation behavior.

The design goal is:

- Easy for humans to write
- Mostly valid Markdown
- Compatible with common conventions (Reveal.js, Pandoc, Marp style ideas)
- Works well in Git repositories
- Minimal special syntax

This spec will be referred to as **SlideMD**.

______________________________________________________________________

# SlideMD Specification

*A Markdown Extension for Human-Written Slide Shows*

Version: 0.1

______________________________________________________________________

# 1. Design Goals

SlideMD aims to:

1. Allow slide decks to be written entirely in Markdown.

1. Preserve readability in raw text.

1. Require minimal syntax beyond standard Markdown.

1. Follow familiar conventions used in tools like:

   - Reveal.js
   - Pandoc
   - Marp

1. Support speaker notes, layouts, fragments, and metadata.

______________________________________________________________________

# 2. File Structure

A SlideMD presentation is a **single Markdown document**.

Slides are separated using:

```
---
```

Example:

```
# Title Slide
Welcome to the talk

---

# Agenda

- Intro
- Problem
- Solution
- Q&A
```

______________________________________________________________________

# 3. Slide Types

### Horizontal Slide

```
---
```

Creates the next slide.

### Vertical Slide (Optional)

Borrowing from Reveal.js convention:

```
----
```

Creates a **vertical slide stack**.

Example:

```
# Topic

---

## Detail A

----

## Detail B
```

Result:

```
Topic
  ↓
Detail A
  ↓
Detail B
```

______________________________________________________________________

# 4. Presentation Metadata

Document metadata appears at the top of the file as YAML.

Example:

```
---
title: Building Safari Writer
author: Matthew Martin
date: 2026
theme: safari-dark
aspect: 16:9
---

# Intro
```

Common fields:

| Field | Meaning |
| -------- | ------------------ |
| title | Presentation title |
| author | Presenter name |
| date | Date |
| theme | Visual theme |
| aspect | 16:9 or 4:3 |
| footer | Footer text |
| paginate | Show slide numbers |

______________________________________________________________________

# 5. Slide Metadata

Slides may include metadata blocks.

Example:

```
---
layout: title
background: safari.jpg
class: center
---

# Safari Writer
### Retro Word Processing
```

Supported attributes:

| Attribute | Meaning |
| ---------- | ---------------- |
| layout | Slide layout |
| background | Image background |
| class | CSS classes |
| transition | Slide transition |
| notes | Speaker notes |

______________________________________________________________________

# 6. Speaker Notes

Speaker notes appear after the slide using:

```
Note:
```

Example:

```
# Problem

People still write slides in PowerPoint.

Note:

Explain the pain of PowerPoint here.
```

Alternative supported syntax:

```
::: notes
Speaker text
:::
```

Notes are **not visible to the audience**.

______________________________________________________________________

# 7. Fragments (Step-by-Step Reveals)

Items can appear incrementally.

Fragment marker:

```
<!-- fragment -->
```

Example:

```
# Why Markdown?

- Simple
- Version controlled <!-- fragment -->
- Works everywhere <!-- fragment -->
- Plain text <!-- fragment -->
```

Alternative shorthand:

```
+ First
+ Second
+ Third
```

Where `+` indicates fragment reveal.

______________________________________________________________________

# 8. Layout Blocks

Slides may use layout directives.

Syntax:

```
::: layout columns
```

Example:

```
::: columns

::: column
### Pros

- Fast
- Simple
:::

::: column
### Cons

- Limited styling
:::

:::
```

______________________________________________________________________

# 9. Image Slides

Images may fill slides.

Example:

```
![](diagram.png)
```

Optional directives:

```
![](diagram.png){fullscreen}
```

or

```
![](diagram.png){width=80%}
```

______________________________________________________________________

# 10. Code Blocks

Standard Markdown code blocks are supported.

Example:

````
```python
print("Hello world")
````

```

Optional highlight:

```

```python {highlight=2}
def main():
    print("Hello")
```

```

---

# 11. Centering

Common pattern:

```

::: center

# Big Idea

:::

```

Equivalent shorthand:

```

# Big Idea {.center}

```

---

# 12. Title Slide Layout

Recommended pattern:

```

______________________________________________________________________

## layout: title

# Presentation Title

### Subtitle

Matthew Martin
2026

```

---

# 13. Two-Column Layout

```

::: columns

::: column

# Left

- Item
- Item
  :::

::: column

# Right

![image](pic.png)

:::

:::

```

---

# 14. Quotes

Use Markdown blockquotes.

```

> The best slide is the one you delete.

```

Optional attribution:

```

> Simplicity is the ultimate sophistication.
>
> — Leonardo da Vinci

```

---

# 15. Callout Blocks

Supported extensions:

```

::: warning
Don't put too much text on slides.
:::

```

Types:

```

::: info
::: tip
::: warning
::: danger

```

---

# 16. Footer Controls

Footer text may be defined globally or per slide.

Example:

```

______________________________________________________________________

## footer: Safari Writer Project

# Slide

```

Override per slide:

```

______________________________________________________________________

## footer: Confidential

```

---

# 17. Timing (Optional)

Slides may specify auto-advance.

```

______________________________________________________________________

## autoplay: 10

```

Meaning: advance after **10 seconds**.

---

# 18. Presenter Commands

Inline presenter directives:

```

<!-- pause -->

```

Pauses until presenter advances.

```

<!-- demo -->

```

Marks demo sections.

---

# 19. Export Targets

SlideMD is intended to render to:

- HTML slides
- PDF slides
- PowerPoint (.pptx)
- Speaker notes view
- Static website

---

# 20. Example Slide Deck

```

______________________________________________________________________

## title: Safari Writer author: Matthew Martin theme: retro aspect: 4:3

# Safari Writer

Retro Word Processing

______________________________________________________________________

# Why Markdown?

- Simple
- Git friendly <!-- fragment -->
- Easy to write <!-- fragment -->

Note:

Mention how documentation teams already use Markdown.

______________________________________________________________________

::: columns

::: column

### Good

- Plain text
- Diff friendly
  :::

::: column

### Bad

- Not WYSIWYG
  :::

:::

______________________________________________________________________

# Thank You

Questions?

```

---

# 21. Compatibility

SlideMD intentionally mirrors patterns found in:

- Pandoc slides
- Marp
- Reveal.js Markdown
- Obsidian slides
- GitHub Markdown extensions

This ensures **familiar syntax for most users**.

---

# 22. Non-Goals

SlideMD does **not attempt to replicate PowerPoint features like**:

- complex animations
- slide master editing
- drag-and-drop layout design
- embedded charts

The focus is **text-first presentations**.
```
