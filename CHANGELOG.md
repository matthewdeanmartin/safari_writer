# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Improvements to web version and sample app

## [0.1.5] - 2026-03-14

### Fixed
- Packaging now requires `Pillow>=12.0.0` on Python 3.14+ and drops the unused `term-image` dependency that capped Pillow below 11

## [0.1.4] - 2026-03-14

### Added
- Image viewer
- Better support for Markdown
- Slide viewer with PDF support
- Improved OPML support
- Assembly script runner
- Reader improvements with better navigation

### Changed
- Better menu organization
- More CLI functionality
- Splash screen improvements
- Better internationalization support
- Improved shortcut audit and help

### Fixed
- Editor scrolling
- Markdown support in various contexts
- Post to Mastodon functionality

## [0.1.3] - 2026-03-11

### Added
- XBase clone language parser for BASIC support
- Improved BASIC REPL
- Print to Git Push for publishing a blog (e.g. Pelican)
- Most of Safari Base (xbase clone) implemented, integrations pending
- Internationalization support
- File type awareness for syntax coloring
- Edit time macros bundled with app

### Changed
- Better markdown support
- Branch support in chat

### Fixed
- Post to Mastodon
- Editor scrolling in reader view
- Fallback handling for missing or unsupported file types

## [0.1.2] - 2026-03-10

### Added
- Internationalization framework
- More consistent F1 styling
- Documentation improvements
- Print to Git functionality for Pelican blog
- XBase clone language parser
- Reader for long documents
- Reader improvements

## [0.1.1] - 2026-03-08

### Added
- Safari Fed Mastodon client
- File type awareness to distinguish between .swf files with formatting codes and plain text, with syntax coloring for .en and .py files
- Safari DOS two-pane Atari-style file browser with a left command menu and right file listing
- Safari DOS file-management actions menu without irrelevant disk-formatting commands
- Safari Chat Eliza-like help system with emotional support and RAG, no LLMs
- Safari Base extreme beta implementation
- Improved documentation

## [0.1.0] - 2026-03-08

### Added
- Application created

[Unreleased]: https://github.com/matthewdeanmartin/safari_writer/compare/v0.1.5...HEAD
[0.1.5]: https://github.com/matthewdeanmartin/safari_writer/compare/v0.1.4...v0.1.5
[0.1.4]: https://github.com/matthewdeanmartin/safari_writer/compare/v0.1.3...v0.1.4
[0.1.3]: https://github.com/matthewdeanmartin/safari_writer/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/matthewdeanmartin/safari_writer/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/matthewdeanmartin/safari_writer/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/matthewdeanmartin/safari_writer/compare/v0.1.0...v0.1.0
