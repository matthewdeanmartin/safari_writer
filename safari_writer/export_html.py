"""Export document buffer to HTML format."""

from __future__ import annotations

import html
import re
from typing import TYPE_CHECKING

from safari_writer.state import GlobalFormat

if TYPE_CHECKING:
    from safari_writer.mail_merge_db import MailMergeDB

__all__ = ["export_html"]


def export_html(
    buffer: list[str],
    fmt: GlobalFormat,
    db: MailMergeDB | None = None,
    is_markdown: bool = False,
) -> str:
    """Convert a document buffer to HTML.

    If is_markdown is True, treats buffer as raw Markdown.
    Otherwise, converts Safari Writer formatting to HTML.
    """
    if is_markdown:
        md_text = "\n".join(buffer)
    else:
        from safari_writer.export_md import export_markdown

        md_text = export_markdown(buffer, fmt, db)

    # Simple Markdown to HTML converter
    html_content = _md_to_html(md_text)

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Safari Writer Export</title>
    <style>
        body {{
            font-family: sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 2em auto;
            padding: 0 1em;
            color: #333;
        }}
        pre {{
            background: #f4f4f4;
            padding: 1em;
            overflow-x: auto;
        }}
        blockquote {{
            border-left: 5px solid #ccc;
            margin: 1.5em 10px;
            padding: 0.5em 10px;
            color: #666;
        }}
        code {{
            background: #f4f4f4;
            padding: 0.2em 0.4em;
        }}
    </style>
</head>
<body>
{html_content}
</body>
</html>
"""


def _md_to_html(md: str) -> str:
    """Very basic Markdown to HTML conversion using regex."""
    # This is not a full-featured parser, but covers basics for Safari Writer needs.

    lines = md.splitlines()
    html_lines = []
    in_list = False

    for line in lines:
        # Headings
        if line.startswith("#"):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            level = 0
            for char in line:
                if char == "#":
                    level += 1
                else:
                    break
            content = line[level:].strip()
            html_lines.append(f"<h{level}>{html.escape(content)}</h{level}>")
            continue

        # Horizontal rule
        if line.strip() == "---":
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append("<hr>")
            continue

        # Lists (very basic)
        if line.strip().startswith("- ") or line.strip().startswith("* "):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            content = line.strip()[2:]
            html_lines.append(f"  <li>{_render_inline_html(content)}</li>")
            continue
        elif in_list and line.strip():
            # Continuation of list?
            html_lines.append(f"  {_render_inline_html(line.strip())}")
            continue
        elif in_list:
            html_lines.append("</ul>")
            in_list = False

        # Paragraphs
        if line.strip():
            html_lines.append(f"<p>{_render_inline_html(line)}</p>")
        else:
            html_lines.append("")

    if in_list:
        html_lines.append("</ul>")

    return "\n".join(html_lines)


def _render_inline_html(text: str) -> str:
    """Render inline markdown (bold, italic, links, etc) to HTML."""
    t = html.escape(text)

    # Bold: **text**
    t = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", t)
    # Italic: *text* (be careful with bold)
    t = re.sub(r"\*(.*?)\*", r"<em>\1</em>", t)
    # Underline (if present in MD via <u>)
    # Links: [text](url)
    t = re.sub(r"\[(.*?)\]\((.*?)\)", r'<a href="\2">\1</a>', t)

    # Safari Writer specific tags if they survived export_md
    t = t.replace("&lt;center&gt;", '<div style="text-align: center;">').replace(
        "&lt;/center&gt;", "</div>"
    )
    t = t.replace("&lt;u&gt;", "<u>").replace("&lt;/u&gt;", "</u>")
    t = t.replace("&lt;sup&gt;", "<sup>").replace("&lt;/sup&gt;", "</sup>")
    t = t.replace("&lt;sub&gt;", "<sub>").replace("&lt;/sub&gt;", "</sub>")

    return t
