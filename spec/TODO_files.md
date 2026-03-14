# Spec 10: File Type Awareness — Implementation Progress

## Remaining / Future Work

### Not yet implemented (lower priority items from spec)

- [ ] Theme compatibility: highlight colors that adapt to all Safari Writer themes (currently uses "monokai" Pygments theme)
- [ ] Configurable Pygments theme selection
- [ ] Additional language extensions (e.g., `.rs`, `.go`, `.c`, `.cpp`, `.html`, `.css`, `.sql`)
- [ ] Additional natural-language overlays beyond English (e.g., `.fr`, `.de`, `.es`)
- [ ] Rendering layer composition with full Rich `Text` objects instead of markup strings for SFW mode (currently SFW uses string markup, plain files use `Text` spans)
- [ ] Performance optimization for very large files (current approach re-highlights per-line via Pygments)

### Spec items that depend on other features

- [ ] Full English prose highlighting subsystem (spec says "there will be a whole subsystem for handling that") — current implementation covers function words, punctuation, editorial markers, URLs, emails, numbers as placeholder
- [ ] Proofreader integration with file type awareness
