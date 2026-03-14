Below is the **addendum specification** describing how a **reference implementation of SlideMD** could be built. This focuses on **architecture, parsing, rendering, and export pipelines**, while remaining implementation-agnostic enough that different languages could implement it.

______________________________________________________________________

# SlideMD Reference Implementation Addendum

*Architecture and Rendering Specification*

Version: 0.1

______________________________________________________________________

# 1. Overview

A SlideMD renderer converts a Markdown document with SlideMD extensions into a **presentation model**, which can then be rendered to multiple output formats.

Pipeline:

```
SlideMD Markdown
        │
        ▼
Markdown Parser
        │
        ▼
SlideMD AST Transformer
        │
        ▼
Presentation Model
        │
 ┌──────┼─────────┬────────┐
 ▼      ▼         ▼        ▼
HTML    PDF      PPTX    TUI
Renderer Renderer Renderer Renderer
```

The reference implementation consists of **five major subsystems**.

1. Markdown parsing
1. Slide segmentation
1. Directive processing
1. Presentation model creation
1. Output renderers

______________________________________________________________________

# 2. Parsing Strategy

The system **does not implement Markdown itself**.

Instead it uses an existing Markdown parser.

Recommended options:

| Language | Library |
| -------- | ---------------- |
| Python | `markdown-it-py` |
| Python | `mistune` |
| Python | `markdown` |

Preferred:

```
markdown-it-py
```

Reasons:

- extensible token system
- plugins
- CommonMark compliance

______________________________________________________________________

# 3. Slide Segmentation

SlideMD adds logic for splitting Markdown into slides.

Primary separators:

```
---
```

Secondary vertical separators:

```
----
```

Algorithm:

```
read entire markdown file
split into sections on --- lines
within sections split on ----
construct slide hierarchy
```

Example input:

```
Slide A

---

Slide B

----

Slide C
```

Model:

```
Horizontal Slide A
Horizontal Slide B
   Vertical Slide C
```

______________________________________________________________________

# 4. AST Processing

After Markdown parsing, the renderer walks the **Markdown AST tokens** and identifies SlideMD constructs.

These include:

| Construct | Detection |
| ---------------- | ----------------------- |
| Fragments | HTML comment marker |
| Columns | container directive |
| Speaker notes | note blocks |
| Metadata | YAML frontmatter |
| Slide attributes | YAML between separators |

Each construct is converted into structured nodes.

Example internal node:

```
Slide
 ├── metadata
 ├── blocks
 │    ├── heading
 │    ├── list
 │    └── image
 └── notes
```

______________________________________________________________________

# 5. Presentation Model

The core data model is a **presentation object**.

Example structure:

```
Presentation
 ├── metadata
 ├── slides[]
 │     ├── id
 │     ├── metadata
 │     ├── blocks
 │     ├── notes
 │     └── fragments
 └── theme
```

Recommended Python model (conceptual):

```
Presentation
Slide
Block
Fragment
Notes
Layout
Theme
```

Slides should contain **only semantic content**, not rendering details.

______________________________________________________________________

# 6. Block Types

Blocks correspond to Markdown structures.

Common block types:

| Block | Source |
| --------- | ---------------- |
| Heading | `#` syntax |
| Paragraph | plain text |
| List | `-` or `*` |
| Code | fenced blocks |
| Image | `![]()` |
| Quote | `>` |
| Table | Markdown table |
| Columns | layout container |
| Callout | `::: warning` |

Block representation example:

```
Block(
  type="heading",
  level=1,
  text="Intro"
)
```

______________________________________________________________________

# 7. Fragment Handling

Fragments allow incremental reveals.

Example input:

```
- One
- Two <!-- fragment -->
- Three <!-- fragment -->
```

Algorithm:

```
detect fragment marker
assign fragment order
```

Internal representation:

```
Fragment(
  order=1,
  block=list_item
)
```

Renderers decide how to display fragments.

______________________________________________________________________

# 8. Notes Handling

Notes are stored separately from visible slide content.

Example:

```
Note:

Explain this diagram.
```

Model:

```
Slide.notes = [
    "Explain this diagram."
]
```

Notes are rendered only in:

- presenter view
- speaker exports
- printed notes

______________________________________________________________________

# 9. Layout System

Layouts affect slide rendering.

Example metadata:

```
layout: title
```

Layout engine:

```
if layout == title:
    render_title_layout()
elif layout == columns:
    render_columns_layout()
```

Layout types:

| Layout | Purpose |
| ------- | ---------------- |
| title | title slide |
| default | normal slide |
| columns | two columns |
| image | full background |
| center | centered content |

______________________________________________________________________

# 10. Theme System

Themes define:

- fonts
- colors
- spacing
- transitions

Themes are stored as:

```
theme/
   safari/
      theme.css
      layout.html
      fragments.js
```

Renderer loads theme assets when generating output.

______________________________________________________________________

# 11. HTML Rendering

The primary output target is HTML.

Typical structure:

```
presentation.html
theme.css
presentation.js
```

Example HTML:

```
<section class="slide">
  <h1>Intro</h1>
  <ul>
    <li>Item</li>
  </ul>
</section>
```

Slides are navigated using:

- keyboard
- click
- touch

Optional frameworks:

- Reveal.js
- bespoke.js
- custom JS engine

______________________________________________________________________

# 12. PDF Export

PDF export may occur through two methods.

### Method 1

HTML → Print → PDF

Advantages:

- simplest
- preserves layout

### Method 2

Direct renderer

Possible using:

```
WeasyPrint
```

Pipeline:

```
HTML
 ↓
CSS print layout
 ↓
PDF
```

______________________________________________________________________

# 13. PowerPoint Export

PowerPoint export is useful for interoperability.

Python library:

```
python-pptx
```

Mapping rules:

| Markdown | PPTX |
| --------- | ----------------- |
| Heading | Title |
| Paragraph | Text box |
| List | Bullet list |
| Image | Picture |
| Code | Monospace textbox |

Example slide creation:

```
ppt.slides.add_slide(layout)
```

Fragments become **separate animation steps**.

______________________________________________________________________

# 14. Terminal (TUI) Renderer

A TUI renderer allows slide presentation in terminals.

Libraries:

```
textual
rich
blessed
```

Rendering strategy:

```
clear screen
render slide
wait for keypress
```

Controls:

| Key | Action |
| ----- | ------------- |
| Right | next slide |
| Left | previous |
| Space | next fragment |
| N | show notes |

______________________________________________________________________

# 15. Image Handling

Images may be:

```
local
remote
embedded
```

Renderer behavior:

```
resolve path
copy asset
optimize image
```

For HTML export:

```
images/
   diagram.png
```

______________________________________________________________________

# 16. Code Highlighting

Recommended highlighters:

```
Pygments
Shiki
Highlight.js
```

Renderer converts code blocks to:

```
<pre><code class="language-python">
```

______________________________________________________________________

# 17. Incremental Compilation

For authoring convenience, renderer should support:

```
watch mode
```

Example:

```
slidemd watch talk.md
```

Behavior:

```
file changes
→ rebuild
→ refresh browser
```

______________________________________________________________________

# 18. CLI Interface

Reference CLI commands.

```
slidemd build talk.md
```

Outputs:

```
build/
   presentation.html
```

______________________________________________________________________

```
slidemd serve talk.md
```

Starts local preview server.

______________________________________________________________________

```
slidemd export talk.md --pdf
```

Exports PDF.

______________________________________________________________________

```
slidemd export talk.md --pptx
```

Exports PowerPoint.

______________________________________________________________________

# 19. Plugin System

The renderer should support plugins.

Example:

```
slidemd-mermaid
slidemd-math
slidemd-chart
```

Plugin API:

```
register_block()
register_directive()
register_renderer()
```

______________________________________________________________________

# 20. Performance Considerations

Typical slide decks are small (\<1MB).

However:

- image compression
- caching parsed AST
- incremental builds

should be implemented.

______________________________________________________________________

# 21. Error Handling

Errors should include line numbers.

Example:

```
Error: Unknown directive

file: talk.md
line: 134
directive: ::: grid
```

______________________________________________________________________

# 22. Testing Strategy

Recommended test layers:

1. Parser tests
1. AST tests
1. Renderer tests
1. Snapshot tests

Example snapshot test:

```
input.md → output.html
```

Compare to expected result.

______________________________________________________________________

# 23. Reference Implementation (Python)

Suggested stack:

```
markdown-it-py
pydantic
jinja2
python-pptx
rich/textual
watchdog
```

Architecture:

```
slidemd/
  parser/
  model/
  directives/
  renderer/
  themes/
  cli/
```

______________________________________________________________________

# 24. Minimal Prototype Pipeline

Simplified algorithm:

```
read markdown
extract YAML metadata
split slides
parse markdown
build slide model
render HTML template
```
