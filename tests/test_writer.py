"""Tests for the bookmark writer."""

import pytest
from src.writer import write_bookmarks
from src.models import Bookmark, Folder


class TestWriteBookmarks:
    def test_write_empty_root(self):
        root = Folder(title="Bookmarks")
        html = write_bookmarks(root)
        assert "<!DOCTYPE NETSCAPE-Bookmark-file-1>" in html
        assert "<DL><p>" in html
        assert "</DL><p>" in html

    def test_write_single_bookmark(self):
        root = Folder(title="Bookmarks")
        root.children.append(Bookmark(title="Example", url="https://example.com", add_date="123"))
        html = write_bookmarks(root)
        assert 'HREF="https://example.com"' in html
        assert 'ADD_DATE="123"' in html
        assert ">Example</A>" in html

    def test_write_folder_with_bookmarks(self):
        root = Folder(title="Bookmarks")
        folder = Folder(title="Dev", add_date="456")
        folder.children.append(Bookmark(title="GitHub", url="https://github.com"))
        root.children.append(folder)
        html = write_bookmarks(root)
        assert "<H3 FOLDED" in html
        assert ">Dev</H3>" in html
        assert 'HREF="https://github.com"' in html

    def test_write_escapes_html_in_title(self):
        root = Folder(title="Bookmarks")
        root.children.append(Bookmark(title="<script>alert('xss')</script>", url="https://example.com"))
        html = write_bookmarks(root)
        assert "&lt;script&gt;" in html
        assert "<script>" not in html.split("<DL>")[1]  # Not in bookmark area

    def test_write_escapes_html_in_url(self):
        root = Folder(title="Bookmarks")
        root.children.append(Bookmark(title="Test", url='https://example.com?a=1&b="2"'))
        html = write_bookmarks(root)
        assert "a=1&amp;b=&quot;2&quot;" in html

    def test_write_optional_attributes(self):
        root = Folder(title="Bookmarks")
        root.children.append(Bookmark(
            title="Test",
            url="https://example.com",
            add_date="100",
            last_visit="200",
            last_modified="300",
        ))
        html = write_bookmarks(root)
        assert 'ADD_DATE="100"' in html
        assert 'LAST_VISIT="200"' in html
        assert 'LAST_MODIFIED="300"' in html

    def test_write_omits_empty_attributes(self):
        root = Folder(title="Bookmarks")
        root.children.append(Bookmark(title="Test", url="https://example.com"))
        html = write_bookmarks(root)
        assert "LAST_VISIT" not in html
        assert "LAST_MODIFIED" not in html


class TestRoundTrip:
    """Test that parsing and writing produces consistent output."""

    def test_round_trip_preserves_bookmarks(self):
        from src.parser import parse_bookmarks as parse

        original = Folder(title="Bookmarks")
        folder = Folder(title="Development", add_date="123")
        folder.children = [
            Bookmark(title="GitHub", url="https://github.com", add_date="456"),
            Bookmark(title="GitLab", url="https://gitlab.com", add_date="789"),
        ]
        original.children = [folder]

        html = write_bookmarks(original)
        parsed = parse(html)

        assert len(parsed.children) == 1
        assert isinstance(parsed.children[0], Folder)
        assert parsed.children[0].title == "Development"
        assert len(parsed.children[0].children) == 2
        assert parsed.children[0].children[0].title == "GitHub"
        assert parsed.children[0].children[0].url == "https://github.com"
        assert parsed.children[0].children[1].title == "GitLab"
