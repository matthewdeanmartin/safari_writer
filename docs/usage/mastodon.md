# Posting to Mastodon

Safari Writer integrates with **Safari Fed**, the built-in Mastodon client, so you
can write a post in the editor and send it without leaving the app.

## Prerequisites

You must have an active Safari Fed session before posting. Open Safari Fed from
the Main Menu first and sign in to your Mastodon account.

## Posting the current document

1. Write your post in the editor as a normal document.
2. Press **Ctrl+P** (or **P** from the Main Menu) to open the Print / Export menu.
3. Press **T** — "Post to Mastodon (Toot)".
4. A full-screen **Toot Preview** opens showing:
   - The account you are posting as.
   - The document title (if the file has been saved).
   - A character count against the 500-character limit. The count turns **red** if
     you exceed the limit.
   - A spell-check report in the lower pane.
5. Press **Enter** or **O** to send the toot, or **Esc** / **Q** to cancel.

> **Tip:** Keep your post under 500 characters. The preview shows
> `chars/500 OVER n` in red when you are over the limit.

## Composing a reply from Safari Fed

Inside Safari Fed you can compose new posts and replies directly in the Safari
Writer editor:

1. Open Safari Fed from the Main Menu (**Safari Fed** option).
2. Navigate to a post you want to reply to and press the reply key.
3. Safari Writer opens the editor pre-filled with a quote of the post and
   `@author` on the last line.
4. Type your reply.
5. Press **Ctrl+P** to send, or **Esc** to go back to Safari Fed without posting.

## Spell-check on toots

The Toot Preview screen runs the built-in proofreader automatically. Misspelled
words are listed in the lower pane. Install **pyenchant** for full dictionary
support (`uv add pyenchant`). Without it the check is skipped and a notice is
shown.

## Character limit notes

Mastodon's standard limit is 500 characters. Counting is done on the raw text of
the buffer — control characters and formatting markers are not counted, but URLs
are counted at their full length (no shortening).
