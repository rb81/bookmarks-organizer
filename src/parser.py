"""Parse Netscape Bookmark File Format into our data model."""

from __future__ import annotations

from html.parser import HTMLParser
from .models import Bookmark, Folder


class NetscapeBookmarkParser(HTMLParser):
    """Parser for Netscape Bookmark File Format HTML."""

    def __init__(self):
        super().__init__()
        self.root = Folder(title="Bookmarks")
        self._stack: list[Folder] = [self.root]
        self._current_tag = ""
        self._current_attrs = {}
        self._in_h3 = False
        self._in_a = False
        self._text = ""

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        attrs_dict = dict(attrs)

        if tag == "dl":
            # A new DL means children follow for the current folder
            pass
        elif tag == "dt":
            pass
        elif tag == "h3":
            self._in_h3 = True
            self._current_attrs = attrs_dict
            self._text = ""
        elif tag == "a":
            self._in_a = True
            self._current_attrs = attrs_dict
            self._text = ""

    def handle_endtag(self, tag):
        tag = tag.lower()

        if tag == "dl":
            # Pop the folder stack (but never pop root)
            if len(self._stack) > 1:
                self._stack.pop()
        elif tag == "h3":
            self._in_h3 = False
            folder = Folder(
                title=self._text.strip(),
                add_date=self._current_attrs.get("add_date", ""),
            )
            self._stack[-1].children.append(folder)
            self._stack.append(folder)
        elif tag == "a":
            self._in_a = False
            bookmark = Bookmark(
                title=self._text.strip(),
                url=self._current_attrs.get("href", ""),
                add_date=self._current_attrs.get("add_date", ""),
                last_visit=self._current_attrs.get("last_visit", ""),
                last_modified=self._current_attrs.get("last_modified", ""),
            )
            self._stack[-1].children.append(bookmark)

    def handle_data(self, data):
        if self._in_h3 or self._in_a:
            self._text += data


def parse_bookmarks(html: str) -> Folder:
    """Parse a Netscape bookmark HTML string into a Folder tree."""
    parser = NetscapeBookmarkParser()
    parser.feed(html)
    return parser.root


def extract_all_bookmarks(folder: Folder, protected_folders: list[str] | None = None) -> tuple[list[Bookmark], list[Folder]]:
    """
    Extract all bookmarks from the tree.
    
    Returns:
        - flat list of bookmarks (from non-protected folders)
        - list of protected folders (kept intact)
    """
    if protected_folders is None:
        protected_folders = []

    bookmarks = []
    protected = []

    for child in folder.children:
        if isinstance(child, Folder):
            if child.title in protected_folders:
                protected.append(child)
            else:
                sub_bookmarks, sub_protected = extract_all_bookmarks(child, protected_folders)
                bookmarks.extend(sub_bookmarks)
                protected.extend(sub_protected)
        elif isinstance(child, Bookmark):
            bookmarks.append(child)

    return bookmarks, protected


def extract_uncategorized_bookmarks(folder: Folder, protected_folders: list[str] | None = None) -> tuple[list[Bookmark], list[Folder]]:
    """
    Extract only bookmarks from an 'Uncategorized' folder.
    
    Returns:
        - flat list of uncategorized bookmarks
        - list of all other folders (kept intact)
    """
    if protected_folders is None:
        protected_folders = []

    uncategorized = []
    kept_folders = []

    for child in folder.children:
        if isinstance(child, Folder):
            if child.title.lower() == "uncategorized":
                # Extract all bookmarks from this folder
                sub_bookmarks, _ = extract_all_bookmarks(child, [])
                uncategorized.extend(sub_bookmarks)
            else:
                kept_folders.append(child)
        elif isinstance(child, Bookmark):
            # Top-level bookmarks are treated as uncategorized
            uncategorized.append(child)

    return uncategorized, kept_folders
