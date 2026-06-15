"""Tests for the progress persistence module."""

import json
import pytest
from pathlib import Path
from src.progress import save_progress, load_progress, clear_progress, get_progress_path
from src.models import Bookmark


@pytest.fixture
def tmp_progress_path(tmp_path):
    return tmp_path / "progress.json"


class TestGetProgressPath:
    def test_returns_progress_json_in_same_dir(self):
        path = get_progress_path("/some/dir/output.html")
        assert path == Path("/some/dir/progress.json")

    def test_relative_path(self):
        path = get_progress_path("output.html")
        assert path.name == "progress.json"


class TestSaveAndLoadProgress:
    def test_save_and_load(self, tmp_progress_path):
        categories = {
            "Development": [
                Bookmark(title="GitHub", url="https://github.com", add_date="123"),
            ],
            "News": [
                Bookmark(title="HN", url="https://news.ycombinator.com"),
            ],
        }
        save_progress(tmp_progress_path, categories, remaining_indices=[5, 6, 7], total_count=10)

        loaded = load_progress(tmp_progress_path)
        assert loaded is not None
        assert loaded["total_count"] == 10
        assert loaded["remaining_indices"] == [5, 6, 7]
        assert "Development" in loaded["categories"]
        assert len(loaded["categories"]["Development"]) == 1
        assert loaded["categories"]["Development"][0].title == "GitHub"
        assert loaded["categories"]["Development"][0].url == "https://github.com"
        assert loaded["categories"]["Development"][0].add_date == "123"

    def test_load_nonexistent(self, tmp_progress_path):
        result = load_progress(tmp_progress_path)
        assert result is None

    def test_load_corrupted_file(self, tmp_progress_path):
        tmp_progress_path.write_text("not valid json {{{")
        result = load_progress(tmp_progress_path)
        assert result is None


class TestClearProgress:
    def test_clear_existing(self, tmp_progress_path):
        tmp_progress_path.write_text("{}")
        clear_progress(tmp_progress_path)
        assert not tmp_progress_path.exists()

    def test_clear_nonexistent(self, tmp_progress_path):
        # Should not raise
        clear_progress(tmp_progress_path)
