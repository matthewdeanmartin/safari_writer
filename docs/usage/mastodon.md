# Posting to Mastodon

Safari Writer integrates with **Safari Fed**, the built-in Mastodon client, so you
can write a post in the editor and send it without leaving the app.

## Prerequisites

You can open Safari Fed from the Main Menu or by running `safari-fed`.

If Mastodon credentials are configured, Safari Fed can sync and send live posts.
If no credentials are configured, Safari Fed still opens in demo mode so you can
explore the interface safely.

## Posting the current document

1. Write your post in the editor as a normal document.
1. Press **Ctrl+P** (or **P** from the Main Menu) to open the Print / Export menu.
1. Press **T** — "Post to Mastodon (Toot)".
1. A full-screen **Toot Preview** opens showing:
   - The account you are posting as.
   - The document title (if the file has been saved).
   - A character count against the 500-character limit. The count turns **red** if
     you exceed the limit.
   - A spell-check report in the lower pane.
1. Press **Enter** or **O** to send the toot, or **Esc** / **Q** to cancel.

> **Tip:** Keep your post under 500 characters. The preview shows
> `chars/500 OVER n` in red when you are over the limit.

## Composing a post or reply from Safari Fed

Safari Fed behaves a little differently depending on where it was launched:

1. In standalone Safari Fed, press **C** to compose or **R** to reply.
1. The built-in compose shell opens.
1. Press **Ctrl+X** to send, **Ctrl+S** to save a draft, or **Esc** to cancel.

When Safari Fed is launched from inside the full Safari Writer app, **C** and
**R** hand the draft to the full Safari Writer editor instead of the mini
compose shell.

1. Open Safari Fed from the Main Menu.
1. Press **C** to compose a new post or **R** to reply to the selected post.
1. Safari Writer opens the editor, with replies pre-filled with an `@author`
   line.
1. Draft and revise as normal, then return to the publish flow from Writer.

## Spell-check on toots

The Toot Preview screen runs the built-in proofreader automatically. Misspelled
words are listed in the lower pane. Install **pyenchant** for full dictionary
support (`uv add pyenchant`). Without it the check is skipped and a notice is
shown.

## Character limit notes

Mastodon's standard limit is 500 characters. Counting is done on the raw text of
the buffer — control characters and formatting markers are not counted, but URLs
are counted at their full length (no shortening).
