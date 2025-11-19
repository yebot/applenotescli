"""Converters between Markdown and Apple Notes HTML format."""

import markdown
from bs4 import BeautifulSoup


def markdown_to_html(md_content: str) -> str:
    """Convert Markdown to Apple Notes compatible HTML.

    Apple Notes uses a restricted HTML subset:
    - div for paragraphs
    - br for line breaks
    - Inline styles only (no classes)
    - Limited elements: b, i, u, strike, a, ul, ol, li
    """
    # Convert Markdown to HTML
    html = markdown.markdown(
        md_content,
        extensions=["extra", "nl2br"],
    )

    # Parse and clean for Apple Notes compatibility
    soup = BeautifulSoup(html, "html.parser")

    # Convert <p> tags to <div> (Apple Notes preference)
    for p in soup.find_all("p"):
        p.name = "div"

    # Convert <strong> to <b> and <em> to <i>
    for strong in soup.find_all("strong"):
        strong.name = "b"
    for em in soup.find_all("em"):
        em.name = "i"

    return str(soup)


def html_to_markdown(html_content: str) -> str:
    """Convert Apple Notes HTML to Markdown.

    Basic conversion for common elements.
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # Simple conversion - can be expanded
    result = []

    for element in soup.children:
        if element.name == "div":
            text = _convert_element(element)
            result.append(text)
        elif element.name in ("ul", "ol"):
            result.append(_convert_list(element))
        elif hasattr(element, "get_text"):
            result.append(element.get_text())

    return "\n\n".join(result)


def _convert_element(element) -> str:
    """Convert an HTML element to Markdown text."""
    if element.name is None:
        return str(element)

    text = ""
    for child in element.children:
        if child.name is None:
            text += str(child)
        elif child.name == "b":
            text += f"**{child.get_text()}**"
        elif child.name == "i":
            text += f"*{child.get_text()}*"
        elif child.name == "u":
            text += child.get_text()  # Markdown doesn't have underline
        elif child.name == "strike":
            text += f"~~{child.get_text()}~~"
        elif child.name == "a":
            href = child.get("href", "")
            text += f"[{child.get_text()}]({href})"
        elif child.name == "br":
            text += "\n"
        else:
            text += _convert_element(child)

    return text


def _convert_list(element) -> str:
    """Convert ul/ol to Markdown list."""
    lines = []
    is_ordered = element.name == "ol"

    for i, li in enumerate(element.find_all("li", recursive=False), 1):
        prefix = f"{i}. " if is_ordered else "- "
        lines.append(f"{prefix}{li.get_text().strip()}")

    return "\n".join(lines)
