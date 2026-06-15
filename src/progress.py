"""Progress persistence for stop/resume capability."""

from __future__ import annotations

import json
from pathlib import Path
from .models import Bookmark

PROGRESS_FILE = "progress.json"


def get_progress_path(output_path: str) -> Path:
    """Get the progress file path based on the output file."""
    return Path(output_path).parent / PROGRESS_FILE


def save_progress(
    progress_path: Path,
    categories: dict[str, list[Bookmark]],
    remaining_indices: list[int],
    total_count: int,
):
    """Save current progress to disk."""
    data = {
        "total_count": total_count,
        "remaining_indices": remaining_indices,
        "categories": {
            cat: [{"title": b.title, "url": b.url, "add_date": b.add_date,
                   "last_visit": b.last_visit, "last_modified": b.last_modified}
                  for b in bookmarks]
            for cat, bookmarks in categories.items()
        },
    }
    progress_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_progress(progress_path: Path) -> dict | None:
    """Load progress from disk. Returns None if no progress file exists."""
    if not progress_path.exists():
        return None
    try:
        data = json.loads(progress_path.read_text(encoding="utf-8"))
        # Reconstruct Bookmark objects
        categories = {}
        for cat, bookmark_dicts in data.get("categories", {}).items():
            categories[cat] = [
                Bookmark(
                    title=b["title"],
                    url=b["url"],
                    add_date=b.get("add_date", ""),
                    last_visit=b.get("last_visit", ""),
                    last_modified=b.get("last_modified", ""),
                )
                for b in bookmark_dicts
            ]
        return {
            "total_count": data["total_count"],
            "remaining_indices": data["remaining_indices"],
            "categories": categories,
        }
    except (json.JSONDecodeError, KeyError):
        return None


def clear_progress(progress_path: Path):
    """Remove progress file after successful completion."""
    if progress_path.exists():
        progress_path.unlink()
