"""Tests for the bookmark parser."""

import pytest
from src.parser import parse_bookmarks, extract_all_bookmarks, extract_uncategorized_bookmarks
from src.models import Bookmark, Folder


SAMPLE_HTML = """<!DOCTYPE NETSCAPE-Bookmark-file-1>
<!--This is an automatically generated file.
It will be read and overwritten.
Do Not Edit! -->
<Title>Bookmarks</Title>
<H1>Bookmarks</H1>
<DL><p>
    <DT><H3 FOLDED ADD_DATE="1234567890">Development</H3>
    <DL><p>
        <DT><A HREF="https://github.com" ADD_DATE="1234567890">GitHub</A>
        <DT><A HREF="https://stackoverflow.com" ADD_DATE="1234567891">Stack Overflow</A>
    </DL><p>
    <DT><H3 FOLDED ADD_DATE="1234567892">News</H3>
    <DL><p>
        <DT><A HREF="https://news.ycombinator.com" ADD_DATE="1234567892">Hacker News</A>
    </DL><p>
    <DT><A HREF="https://example.com" ADD_DATE="1234567893">Example</A>
</DL><p>
"""

UNCATEGORIZED_HTML = """<!DOCTYPE NETSCAPE-Bookmark-file-1>
<Title>Bookmarks</Title>
<H1>Bookmarks</H1>
<DL><p>
    <DT><H3 FOLDED ADD_DATE="1234567890">Development</H3>
    <DL><p>
        <DT><A HREF="https://github.com" ADD_DATE="1234567890">GitHub</A>
    </DL><p>
    <DT><H3 FOLDED ADD_DATE="1234567892">Uncategorized</H3>
    <DL><p>
        <DT><A HREF="https://newsite.com" ADD_DATE="1234567892">New Site</A>
        <DT><A HREF="https://another.com" ADD_DATE="1234567893">Another</A>
    </DL><p>
    <DT><A HREF="https://toplevel.com" ADD_DATE="1234567894">Top Level</A>
</DL><p>
"""


class TestParseBookmarks:
    def test_parse_folders(self):
        root = parse_bookmarks(SAMPLE_HTML)
        assert root.title == "Bookmarks"
        # Should have 2 folders + 1 top-level bookmark
        folders = [c for c in root.children if isinstance(c, Folder)]
        bookmarks = [c for c in root.children if isinstance(c, Bookmark)]
        assert len(folders) == 2
        assert len(bookmarks) == 1
        assert folders[0].title == "Development"
        assert folders[1].title == "News"

    def test_parse_bookmarks_in_folder(self):
        root = parse_bookmarks(SAMPLE_HTML)
        dev_folder = root.children[0]
        assert isinstance(dev_folder, Folder)
        assert len(dev_folder.children) == 2
        assert dev_folder.children[0].title == "GitHub"
        assert dev_folder.children[0].url == "https://github.com"
        assert dev_folder.children[1].title == "Stack Overflow"

    def test_parse_bookmark_attributes(self):
        root = parse_bookmarks(SAMPLE_HTML)
        dev_folder = root.children[0]
        github = dev_folder.children[0]
        assert github.add_date == "1234567890"

    def test_parse_top_level_bookmark(self):
        root = parse_bookmarks(SAMPLE_HTML)
        example = root.children[2]
        assert isinstance(example, Bookmark)
        assert example.title == "Example"
        assert example.url == "https://example.com"

    def test_parse_empty_html(self):
        root = parse_bookmarks("")
        assert root.title == "Bookmarks"
        assert len(root.children) == 0

    def test_parse_folder_add_date(self):
        root = parse_bookmarks(SAMPLE_HTML)
        dev_folder = root.children[0]
        assert dev_folder.add_date == "1234567890"


class TestExtractAllBookmarks:
    def test_extract_all(self):
        root = parse_bookmarks(SAMPLE_HTML)
        bookmarks, protected = extract_all_bookmarks(root)
        assert len(bookmarks) == 4  # 2 in Dev + 1 in News + 1 top-level
        assert len(protected) == 0

    def test_extract_with_protected(self):
        root = parse_bookmarks(SAMPLE_HTML)
        bookmarks, protected = extract_all_bookmarks(root, protected_folders=["News"])
        assert len(bookmarks) == 3  # 2 in Dev + 1 top-level
        assert len(protected) == 1
        assert protected[0].title == "News"

    def test_protected_folder_kept_intact(self):
        root = parse_bookmarks(SAMPLE_HTML)
        _, protected = extract_all_bookmarks(root, protected_folders=["Development"])
        assert len(protected) == 1
        assert len(protected[0].children) == 2  # Still has its bookmarks


class TestExtractUncategorizedBookmarks:
    def test_extract_uncategorized(self):
        root = parse_bookmarks(UNCATEGORIZED_HTML)
        uncategorized, kept = extract_uncategorized_bookmarks(root)
        # 2 from Uncategorized folder + 1 top-level
        assert len(uncategorized) == 3
        # Development folder is kept
        assert len(kept) == 1
        assert kept[0].title == "Development"

    def test_top_level_treated_as_uncategorized(self):
        root = parse_bookmarks(UNCATEGORIZED_HTML)
        uncategorized, _ = extract_uncategorized_bookmarks(root)
        urls = [b.url for b in uncategorized]
        assert "https://toplevel.com" in urls

    def test_uncategorized_case_insensitive(self):
        html = """<!DOCTYPE NETSCAPE-Bookmark-file-1>
<Title>Bookmarks</Title>
<H1>Bookmarks</H1>
<DL><p>
    <DT><H3 FOLDED>UNCATEGORIZED</H3>
    <DL><p>
        <DT><A HREF="https://test.com">Test</A>
    </DL><p>
</DL><p>
"""
        root = parse_bookmarks(html)
        uncategorized, _ = extract_uncategorized_bookmarks(root)
        assert len(uncategorized) == 1
        assert uncategorized[0].url == "https://test.com"
