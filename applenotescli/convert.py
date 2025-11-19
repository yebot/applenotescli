"""Conversion utilities for Apple Notes content."""

import re


def markdown_to_html(text: str) -> str:
    """Convert Markdown text to HTML suitable for Apple Notes.

    Supports basic Markdown:
    - Headers (# ## ###)
    - Bold (**text**)
    - Italic (*text* or _text_)
    - Links [text](url)
    - Unordered lists (- or *)
    - Ordered lists (1. 2. 3.)
    - Code (`inline`)
    - Paragraphs (blank lines)

    Args:
        text: Markdown formatted text

    Returns:
        HTML string suitable for Apple Notes
    """
    if not text:
        return ""

    lines = text.split("\n")
    html_lines = []
    in_ul = False
    in_ol = False

    for line in lines:
        # Close any open lists if needed
        stripped = line.strip()

        # Check if we're leaving a list
        is_ul_item = stripped.startswith("- ") or stripped.startswith("* ")
        is_ol_item = bool(re.match(r"^\d+\.\s", stripped))

        if in_ul and not is_ul_item:
            html_lines.append("</ul>")
            in_ul = False
        if in_ol and not is_ol_item:
            html_lines.append("</ol>")
            in_ol = False

        # Empty line = paragraph break
        if not stripped:
            html_lines.append("<br>")
            continue

        # Headers
        if stripped.startswith("### "):
            content = _convert_inline(stripped[4:])
            html_lines.append(f"<h3>{content}</h3>")
            continue
        if stripped.startswith("## "):
            content = _convert_inline(stripped[3:])
            html_lines.append(f"<h2>{content}</h2>")
            continue
        if stripped.startswith("# "):
            content = _convert_inline(stripped[2:])
            html_lines.append(f"<h1>{content}</h1>")
            continue

        # Unordered list
        if is_ul_item:
            if not in_ul:
                html_lines.append("<ul>")
                in_ul = True
            content = _convert_inline(stripped[2:])
            html_lines.append(f"<li>{content}</li>")
            continue

        # Ordered list
        if is_ol_item:
            if not in_ol:
                html_lines.append("<ol>")
                in_ol = True
            content = _convert_inline(re.sub(r"^\d+\.\s", "", stripped))
            html_lines.append(f"<li>{content}</li>")
            continue

        # Regular paragraph
        content = _convert_inline(stripped)
        html_lines.append(f"<div>{content}</div>")

    # Close any remaining open lists
    if in_ul:
        html_lines.append("</ul>")
    if in_ol:
        html_lines.append("</ol>")

    return "\n".join(html_lines)


def _convert_inline(text: str) -> str:
    """Convert inline Markdown formatting to HTML.

    Args:
        text: Line of text with potential inline Markdown

    Returns:
        Text with inline elements converted to HTML
    """
    # Code (must be first to avoid conflicts)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)

    # Bold (** or __)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"__([^_]+)__", r"<b>\1</b>", text)

    # Italic (* or _) - must come after bold
    text = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", text)
    text = re.sub(r"_([^_]+)_", r"<i>\1</i>", text)

    # Links
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)

    return text


def html_to_plaintext(html: str) -> str:
    """Convert HTML to plain text.

    Args:
        html: HTML content

    Returns:
        Plain text with formatting stripped
    """
    if not html:
        return ""

    # Remove script and style tags with content
    text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)

    # Convert common elements to text equivalents
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</p>", "\n\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</div>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</li>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<li[^>]*>", "- ", text, flags=re.IGNORECASE)

    # Remove all remaining tags
    text = re.sub(r"<[^>]+>", "", text)

    # Decode common HTML entities
    text = text.replace("&nbsp;", " ")
    text = text.replace("&amp;", "&")
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    text = text.replace("&quot;", '"')
    text = text.replace("&#39;", "'")

    # Clean up whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
