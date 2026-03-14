# Learnings 02: Terminal Shortcut and Footer Layout Traps

This note is for future clankers working on the Textual editor screen.

## 1. Do not depend on Alt+function keys

On Windows Terminal, Git Bash, and similar terminals, Alt+function keys are not dependable editor shortcuts.

- `Alt+F3` may not arrive as `alt+f3`
- some terminals translate it into higher function keys such as `f15`
- some terminals swallow the combination entirely

Because of that, Safari Writer should not advertise Alt+function keys as primary commands. Use plain Alt+letter shortcuts when possible. For replace-next, `Alt+N` is the reliable choice.

## 2. Ctrl+H is effectively Backspace in many terminals

`Ctrl+H` is a long-standing terminal alias for Backspace. In practice that means:

- pressing `Ctrl+H` may arrive as `backspace`
- using `Ctrl+H` for a command conflicts with text entry and prompt editing
- prompt handlers must treat only `backspace` as deletion, not `ctrl+h`

So Safari Writer uses `Alt+H` for the replace prompt, and prompt editing only watches for `backspace`.

## 3. Keep the editor footer bars in an explicit container

The editor needs three bottom rows to remain visible:

1. message / prompt row
1. status row
1. help row

If these are yielded as separate bottom-docked widgets, Textual docking order is easy to get wrong and bars can appear hidden or covered. The stable approach is:

- keep the tab marker row at the top
- wrap the bottom bars in a single `Container`
- dock that container to the bottom
- give the container a fixed height and vertical layout

That pattern prevents prompts like `Find:` from disappearing behind other footer UI.

## 4. Practical rule

When adding new editor shortcuts on Windows terminals:

- prefer `Alt+<letter>` over `Alt+<function key>`
- assume `Ctrl+H` is not safely distinct from Backspace
- if a footer line must always stay visible, put it inside the shared footer container rather than adding another independently docked bottom widget
