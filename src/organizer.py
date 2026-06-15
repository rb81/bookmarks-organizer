"""LLM-powered bookmark categorization using OpenAI's library."""

from __future__ import annotations

import json
import time
from pathlib import Path
from openai import OpenAI, APIError, APIConnectionError, RateLimitError, APITimeoutError
from .models import Bookmark, Folder
from .progress import save_progress

MAX_RETRIES = 3
RETRY_DELAYS = [5, 15, 30]  # seconds between retries


SYSTEM_PROMPT = """You are a bookmark organizer. You categorize bookmarks into logical folders.

Rules:
- Assign each bookmark to exactly one category.
- STRONGLY PREFER existing categories. Only create a new category if a bookmark truly does not fit any existing one.
- Use short, broad category names (e.g., "Development", "News", "Finance", "Design"). Prefer general categories over highly specific ones.
- Merge similar topics into one category (e.g., "AI", "Machine Learning", and "Data Science" should all go under one category like "AI & Data Science").
- You MUST NOT exceed the maximum number of categories. If you're at the limit, force-fit bookmarks into the closest existing category.
- Return valid JSON only."""


def organize_bookmarks(
    bookmarks: list[Bookmark],
    client: OpenAI,
    model: str,
    max_categories: int = 20,
    batch_size: int = 10,
    existing_categories: list[str] | None = None,
    progress_path: Path | None = None,
    start_index: int = 0,
    resumed_categories: dict[str, list[Bookmark]] | None = None,
) -> dict[str, list[Bookmark]]:
    """
    Categorize bookmarks using an LLM.
    
    Args:
        bookmarks: Full list of bookmarks to organize.
        client: OpenAI client instance.
        model: Model name to use.
        max_categories: Maximum number of categories to create.
        batch_size: Number of bookmarks per LLM call.
        existing_categories: Category names to reuse (from existing folders).
        progress_path: Path to save progress file (enables stop/resume).
        start_index: Index to start from (for resuming).
        resumed_categories: Previously categorized bookmarks (for resuming).
    
    Returns a dict mapping category name -> list of bookmarks.
    """
    if existing_categories is None:
        existing_categories = []

    categories: dict[str, list[Bookmark]] = resumed_categories or {}

    # Process in batches
    for i in range(start_index, len(bookmarks), batch_size):
        batch = bookmarks[i : i + batch_size]
        current_cats = list(set(existing_categories + list(categories.keys())))

        batch_result = _categorize_batch(batch, client, model, max_categories, current_cats)

        for category, indices in batch_result.items():
            # Fuzzy match to existing categories (case-insensitive)
            matched_cat = _find_matching_category(category, categories)
            if matched_cat not in categories:
                categories[matched_cat] = []
            for idx in indices:
                if 0 <= idx < len(batch):
                    categories[matched_cat].append(batch[idx])

        done = min(i + batch_size, len(bookmarks))
        print(f"  Processed {done}/{len(bookmarks)} bookmarks...")

        # Save progress after each batch
        if progress_path:
            remaining = list(range(done, len(bookmarks)))
            save_progress(progress_path, categories, remaining, len(bookmarks))

    return categories


def _find_matching_category(name: str, categories: dict[str, list[Bookmark]]) -> str:
    """Find an existing category that matches (case-insensitive). Returns original name if no match."""
    name_lower = name.lower().strip()
    for existing in categories:
        if existing.lower().strip() == name_lower:
            return existing
    return name


def _categorize_batch(
    batch: list[Bookmark],
    client: OpenAI,
    model: str,
    max_categories: int,
    existing_categories: list[str],
) -> dict[str, list[int]]:
    """Categorize a single batch of bookmarks. Returns category -> list of indices."""
    
    bookmark_list = "\n".join(
        f"{i}. {b.title} — {b.url}" for i, b in enumerate(batch)
    )

    existing_cats_str = ", ".join(existing_categories) if existing_categories else "None yet"

    user_prompt = f"""Categorize these bookmarks into folders.

Existing categories — YOU MUST REUSE THESE whenever possible: {existing_cats_str}
Maximum total categories allowed: {max_categories}
Current category count: {len(existing_categories)}

IMPORTANT: Do NOT create a new category if an existing one is even remotely relevant. Only create a new category as a last resort when nothing fits. Prefer broader groupings.

Bookmarks:
{bookmark_list}

Respond with JSON in this exact format:
{{
  "Category Name": [0, 2, 5],
  "Another Category": [1, 3, 4]
}}

Where the numbers are the bookmark indices from the list above. Every bookmark must be assigned to exactly one category. Use existing category names exactly as written (case-sensitive)."""

    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            try:
                result = json.loads(content)
                # Validate structure
                validated = {}
                for key, value in result.items():
                    if isinstance(value, list) and all(isinstance(v, int) for v in value):
                        validated[key] = value
                return validated
            except (json.JSONDecodeError, AttributeError):
                # Fallback: put all in Uncategorized
                return {"Uncategorized": list(range(len(batch)))}

        except RateLimitError as e:
            delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
            print(f"  Rate limited. Retrying in {delay}s... (attempt {attempt + 1}/{MAX_RETRIES})")
            time.sleep(delay)
        except APITimeoutError as e:
            delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
            print(f"  Request timed out. Retrying in {delay}s... (attempt {attempt + 1}/{MAX_RETRIES})")
            time.sleep(delay)
        except APIConnectionError as e:
            delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
            print(f"  Connection error: {e}. Retrying in {delay}s... (attempt {attempt + 1}/{MAX_RETRIES})")
            time.sleep(delay)
        except APIError as e:
            if e.status_code and e.status_code >= 500:
                delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
                print(f"  Server error ({e.status_code}). Retrying in {delay}s... (attempt {attempt + 1}/{MAX_RETRIES})")
                time.sleep(delay)
            else:
                # Client error (4xx) — don't retry
                print(f"  API error: {e}")
                return {"Uncategorized": list(range(len(batch)))}

    # Exhausted retries
    print(f"  Failed after {MAX_RETRIES} attempts. Marking batch as Uncategorized.")
    return {"Uncategorized": list(range(len(batch)))}


def build_organized_tree(
    categories: dict[str, list[Bookmark]],
    protected_folders: list[Folder] | None = None,
) -> Folder:
    """Build a Folder tree from categorized bookmarks and protected folders."""
    root = Folder(title="Bookmarks")

    # Add protected folders first
    if protected_folders:
        for folder in protected_folders:
            root.children.append(folder)

    # Add categorized folders
    for category_name, bookmarks in sorted(categories.items()):
        folder = Folder(title=category_name)
        folder.children = bookmarks
        root.children.append(folder)

    return root
