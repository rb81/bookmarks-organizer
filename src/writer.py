"""Write bookmarks back to Netscape Bookmark File Format."""

from __future__ import annotations

from .models import Bookmark, Folder


HEADER = """<!DOCTYPE NETSCAPE-Bookmark-file-1>
<!--This is an automatically generated file.
It will be read and overwritten.
Do Not Edit! -->
<Title>Bookmarks</Title>
<H1>Bookmarks</H1>
"""


def write_bookmarks(root: Folder) -> str:
    """Write a Folder tree to Netscape bookmark HTML format."""
    lines = [HEADER]
    lines.append("<DL><p>")
    _write_children(root.children, lines, indent=1)
    lines.append("</DL><p>")
    return "\n".join(lines)


def _write_children(children: list, lines: list[str], indent: int):
    prefix = "    " * indent
    for child in children:
        if isinstance(child, Folder):
            attrs = ""
            if child.add_date:
                attrs += f' ADD_DATE="{child.add_date}"'
            lines.append(f"{prefix}<DT><H3 FOLDED{attrs}>{_escape(child.title)}</H3>")
            lines.append(f"{prefix}<DL><p>")
            _write_children(child.children, lines, indent + 1)
            lines.append(f"{prefix}</DL><p>")
        elif isinstance(child, Bookmark):
            attrs = f'HREF="{_escape_attr(child.url)}"'
            if child.add_date:
                attrs += f' ADD_DATE="{child.add_date}"'
            if child.last_visit:
                attrs += f' LAST_VISIT="{child.last_visit}"'
            if child.last_modified:
                attrs += f' LAST_MODIFIED="{child.last_modified}"'
            lines.append(f"{prefix}<DT><A {attrs}>{_escape(child.title)}</A>")


def _escape(text: str) -> str:
    """Escape HTML entities in text content."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _escape_attr(text: str) -> str:
    """Escape HTML entities in attribute values."""
    return (
        text.replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
