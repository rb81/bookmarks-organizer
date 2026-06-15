"""Tests for the organizer module."""

import json
import pytest
from unittest.mock import MagicMock, patch
from src.organizer import (
    organize_bookmarks,
    build_organized_tree,
    _find_matching_category,
    _categorize_batch,
)
from src.models import Bookmark, Folder


class TestFindMatchingCategory:
    def test_exact_match(self):
        categories = {"Development": [], "News": []}
        assert _find_matching_category("Development", categories) == "Development"

    def test_case_insensitive_match(self):
        categories = {"Development": [], "News": []}
        assert _find_matching_category("development", categories) == "Development"
        assert _find_matching_category("DEVELOPMENT", categories) == "Development"

    def test_no_match_returns_original(self):
        categories = {"Development": [], "News": []}
        assert _find_matching_category("Finance", categories) == "Finance"

    def test_whitespace_handling(self):
        categories = {"Development": []}
        assert _find_matching_category(" Development ", categories) == "Development"


class TestBuildOrganizedTree:
    def test_build_with_categories(self):
        bookmarks = [Bookmark(title="GH", url="https://github.com")]
        categories = {"Development": bookmarks}
        root = build_organized_tree(categories)
        assert root.title == "Bookmarks"
        assert len(root.children) == 1
        assert root.children[0].title == "Development"
        assert root.children[0].children == bookmarks

    def test_build_with_protected_folders(self):
        protected = [Folder(title="Favorites", children=[
            Bookmark(title="Fav", url="https://fav.com")
        ])]
        categories = {"Development": [Bookmark(title="GH", url="https://github.com")]}
        root = build_organized_tree(categories, protected_folders=protected)
        # Protected folders come first
        assert root.children[0].title == "Favorites"
        assert root.children[1].title == "Development"

    def test_build_empty(self):
        root = build_organized_tree({})
        assert root.title == "Bookmarks"
        assert len(root.children) == 0

    def test_categories_sorted_alphabetically(self):
        categories = {
            "Zebra": [Bookmark(title="Z", url="https://z.com")],
            "Alpha": [Bookmark(title="A", url="https://a.com")],
        }
        root = build_organized_tree(categories)
        assert root.children[0].title == "Alpha"
        assert root.children[1].title == "Zebra"


class TestCategorizeBatch:
    def test_successful_categorization(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "Development": [0, 1],
            "News": [2],
        })
        mock_client.chat.completions.create.return_value = mock_response

        batch = [
            Bookmark(title="GitHub", url="https://github.com"),
            Bookmark(title="GitLab", url="https://gitlab.com"),
            Bookmark(title="HN", url="https://news.ycombinator.com"),
        ]

        result = _categorize_batch(batch, mock_client, "gpt-4o-mini", 20, [])
        assert result == {"Development": [0, 1], "News": [2]}

    def test_invalid_json_returns_uncategorized(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "not json at all"
        mock_client.chat.completions.create.return_value = mock_response

        batch = [Bookmark(title="Test", url="https://test.com")]
        result = _categorize_batch(batch, mock_client, "gpt-4o-mini", 20, [])
        assert result == {"Uncategorized": [0]}

    def test_invalid_structure_filtered(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "Good": [0],
            "Bad": "not a list",
            "AlsoBad": [0, "string"],
        })
        mock_client.chat.completions.create.return_value = mock_response

        batch = [Bookmark(title="Test", url="https://test.com")]
        result = _categorize_batch(batch, mock_client, "gpt-4o-mini", 20, [])
        assert "Good" in result
        assert "Bad" not in result
        assert "AlsoBad" not in result
