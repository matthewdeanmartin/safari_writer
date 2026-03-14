---
title: The Safari Suite
author: GitHub Copilot
theme: classic-blue
aspect: 4:3
footer: Safari Writer Documentation Tour
paginate: true
---

layout: title
footer: Start Here
---

# The Safari Suite

### A keyboard-first tour of the retro writing toolkit

Safari Writer, Safari DOS, Safari Chat, Safari Fed, Safari REPL, Safari Basic, Safari View, and Safari Slides

---

# What is the Safari suite?

Safari Writer is the center of a family of text-mode tools inspired by AtariWriter-era software.

+ Write and format documents in Safari Writer
+ Browse and manage files in Safari DOS
+ Get help from Safari Chat
+ Read and post on Mastodon with Safari Fed
+ Experiment with BASIC in Safari REPL and Safari Basic
+ Preview images with Safari View
+ Present decks with Safari Slides

Note:

This slide is based on the project README and docs index, which describe the suite as a set of keyboard-driven tools with a shared retro aesthetic.

---

# Start with the main launcher

Most people begin in Safari Writer and open the other tools from its menus.

```bash
safari-writer
```

You can also launch companion tools directly:

```bash
safari-dos
safari-chat
safari-fed
safari-repl
safari-view
safari-slides
```

---

# Safari Writer

Safari Writer is the core word processor.

- Modern editing keys with a retro text-mode feel
- Search, replace, word count, and alphabetize
- Safari Writer formatting codes in `.sfw` documents
- Print and export to ANSI preview, Markdown, PostScript, PDF, and slides
- Built-in proofreader and mail merge workflows

Note:

The README and usage docs position Safari Writer as the main shell and the place where the suite's features come together.

---

# Proofreader and mail merge

Press **V** from the main menu for proofreading.

- Highlight misspelled words
- Step through corrections
- Search the dictionary
- Keep approved spellings in your personal dictionary

Press **M** for mail merge.

- Create and format a database
- Enter or edit records
- Insert merge markers with **Alt+M**
- Print one copy of the document per record

---

# Safari DOS

Safari DOS is the suite's file manager.

- Browse folders and devices
- Copy, move, rename, duplicate, and protect files
- Create folders without leaving the suite
- Send deleted files to **Garbage** for recovery
- Keep favorite folders close at hand

Common browser keys:

- **C** copy
- **M** move
- **R** rename
- **U** duplicate
- **X** move to Garbage
- **I** file information

---

# Safari Chat

Safari Chat is the built-in helper.

- Type a question at the `USER` prompt
- Search help topics without leaving the suite
- Use `/topics`, `/memory`, `/clear`, and `/help`
- Watch the distress meter react to your tone

Safari Chat is intentionally simple: it uses the documentation, not a large language model, to answer questions.

---

# Safari Fed

Safari Fed is a calm, keyboard-driven Mastodon client.

- Read Home, Mentions, Bookmarks, Drafts, Sent, and Deferred folders
- Compose, reply, boost, favourite, bookmark, and sync
- Open threads in a dedicated reader view
- Hand posts back to Safari Writer for editing or quoting

Helpful keys:

- **C** compose
- **R** reply
- **T** thread view
- **W** export the selected post or thread to Safari Writer

---

# Safari REPL and Safari Basic

Safari REPL is the quick Atari BASIC workspace.

- Run immediate commands
- Load `.BAS` files
- Use **F9** to open loaded BASIC source in Safari Writer

Safari Basic is the interpreter and macro engine.

- Use line-numbered BASIC
- Write macros that `PRINT` text into Safari Writer
- Run editor macros with **Ctrl+Backslash**
- Run fediverse macros in Safari Fed with **~**

---

# Safari View and Safari Slides

Safari View handles retro image viewing and rendering.

- Open images in terminal or Tk modes
- Render with retro display styles and options

Safari Slides handles presentation decks.

- Open SlideMD decks written in Markdown
- Preview decks from Safari Writer
- Export writer content to `.slides.md`
- Use it as a lightweight terminal projector for docs, talks, and demos

---

# The suite works best as a chain

Here are common handoff patterns:

+ Write a draft in Safari Writer, then export to Markdown or PDF
+ Open Safari DOS to load, save, rename, or recover files
+ Move from Safari Fed into Safari Writer when a post becomes a longer draft
+ Launch Safari REPL when you want to test or edit a BASIC macro
+ Preview a presentation in Safari Slides before sharing it

Note:

The suite is strongest when treated like a collection of linked rooms rather than isolated apps.

---

# Handy command-line entry points

Use the CLI when you want direct access without menu navigation.

```bash
safari-writer export markdown INPUT -o OUTPUT
safari-writer export postscript INPUT -o OUTPUT
safari-writer export ansi INPUT
safari-writer proof check INPUT
safari-writer mail-merge inspect DATABASE
safari-writer tui safari-repl --file demo.bas
```

You can also launch the companion tools directly:

```bash
safari-fed --folder Home
safari-dos browse C:\work --show-hidden --sort date --descending
```

---

# Which tool should I use?

Use **Safari Writer** when you are writing, revising, proofreading, formatting, or exporting text.

Use **Safari DOS** when the task is really about files and folders.

Use **Safari Chat** when you need help navigating the docs.

Use **Safari Fed** when the text belongs on Mastodon.

Use **Safari REPL** or **Safari Basic** when the task becomes programmable.

Use **Safari View** for images and **Safari Slides** for decks.

---

layout: center
footer: Explore the menus
---

# Follow the menus

Start in `safari-writer`, explore one tool at a time, and let the suite hand work from one room to the next.

Questions? Open Safari Chat.
