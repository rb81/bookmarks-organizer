import os
import json
import yaml
import logging
import sys
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

def load_config() -> Dict[str, Any]:
    """Load the config.yaml file from the same directory as the script."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join('config.yaml')
    try:
        with open(config_path, 'r') as config_file:
            return yaml.safe_load(config_file)
    except FileNotFoundError:
        logger.error(f"config.yaml not found in the correct directory: {script_dir}")
        return None
    except yaml.YAMLError as e:
        logger.error(f"Error parsing config.yaml: {e}", exc_info=True)
        return None

def load_bookmarks(file_path: str) -> Dict[str, Any]:
    """Load the bookmarks from the specified JSON file."""
    try:
        with open(file_path, 'r') as f:
            bookmarks = json.load(f)
        logger.info(f"Successfully loaded bookmarks from {file_path}")
        return bookmarks
    except FileNotFoundError:
        logger.error(f"Bookmark file not found: {file_path}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing bookmark file: {e}", exc_info=True)
        return {}

def save_bookmarks(bookmarks: Dict[str, Any], file_path: str) -> None:
    """Save the bookmarks to the specified JSON file."""
    try:
        with open(file_path, 'w') as f:
            json.dump(bookmarks, f, indent=2, ensure_ascii=False)
        logger.info(f"Bookmarks saved to {file_path}")
    except IOError as e:
        logger.error(f"Error saving bookmarks: {e}", exc_info=True)

def is_protected_folder(folder: str, protected_folders: List[str]) -> bool:
    """Check if a folder is protected or is a subfolder of a protected folder."""
    return any(folder.startswith(protected) for protected in protected_folders)

def flatten_bookmarks(bookmarks: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Flatten the bookmark structure, preserving all metadata."""
    flat_bookmarks = []
    for folder, content in bookmarks.items():
        for bookmark in content['bookmarks']:
            # Create a copy of the bookmark to preserve all metadata
            flat_bookmark = bookmark.copy()
            # Ensure 'title' and 'url' are always present
            if 'title' not in flat_bookmark:
                flat_bookmark['title'] = ''
            if 'url' not in flat_bookmark:
                flat_bookmark['url'] = ''
            flat_bookmarks.append(flat_bookmark)
    logger.debug(f"Flattened {len(flat_bookmarks)} bookmarks")
    return flat_bookmarks

def reorganize_all_bookmarks(bookmarks: Dict[str, Any], protected_folders: List[str]) -> Dict[str, Any]:
    """Reorganize all bookmarks, keeping protected folders intact."""
    reorganized = {}
    uncategorized = []

    for folder, content in bookmarks.items():
        if is_protected_folder(folder, protected_folders):
            reorganized[folder] = content
            logger.debug(f"Kept protected folder intact: {folder}")
        else:
            uncategorized.extend(flatten_bookmarks({folder: content}))

    reorganized['Uncategorized'] = {
        'parent': None,
        'bookmarks': uncategorized
    }

    logger.info(f"Reorganized all bookmarks. Protected folders: {len(reorganized) - 1}, Uncategorized: {len(uncategorized)}")
    return reorganized

def reorganize_uncategorized(bookmarks: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure the Uncategorized folder is flat and preserves all metadata."""
    if 'Uncategorized' not in bookmarks:
        logger.info("No Uncategorized folder found. Skipping reorganization.")
        return bookmarks

    flat_uncategorized = flatten_bookmarks({'Uncategorized': bookmarks['Uncategorized']})
    bookmarks['Uncategorized'] = {
        'parent': None,
        'bookmarks': flat_uncategorized
    }

    logger.info(f"Reorganized Uncategorized folder. Total bookmarks: {len(flat_uncategorized)}")
    return bookmarks

def save_categories(bookmarks: Dict[str, Any], protected_folders: List[str], output_path: str) -> None:
    """Save non-protected, non-Uncategorized category names to categories.json."""
    categories = [
        folder for folder in bookmarks.keys()
        if folder not in protected_folders and folder != "Uncategorized"
    ]
    try:
        with open(output_path, 'w') as f:
            json.dump(categories, f, indent=2)
        logger.info(f"Categories saved to {output_path}. Total categories: {len(categories)}")
    except IOError as e:
        logger.error(f"Error saving categories: {e}", exc_info=True)

def main(reorganize_all: bool):
    logger.info("Starting bookmark reorganization process")
    config = load_config()
    if config is None:
        logger.error("Failed to load config. Exiting.")
        sys.exit(1)

    protected_folders = config.get('Protected Folders', [])
    logger.info(f"Protected folders: {protected_folders}")

    input_file = os.path.join('data', 'updated_bookmarks.json')
    output_file = os.path.join('data', 'reorganized_bookmarks.json')
    categories_file = os.path.join('data', 'categories.json')

    bookmarks = load_bookmarks(input_file)
    if not bookmarks:
        logger.error("Failed to load bookmarks. Exiting.")
        sys.exit(1)

    if reorganize_all:
        logger.info("Reorganizing all bookmarks")
        reorganized_bookmarks = reorganize_all_bookmarks(bookmarks, protected_folders)
    else:
        logger.info("Reorganizing only uncategorized bookmarks")
        reorganized_bookmarks = reorganize_uncategorized(bookmarks)

    save_bookmarks(reorganized_bookmarks, output_file)
    save_categories(reorganized_bookmarks, protected_folders, categories_file)

    logger.info("Bookmark reorganization completed successfully.")

if __name__ == "__main__":
    reorganize_all = len(sys.argv) > 1 and sys.argv[1] == "all"
    main(reorganize_all)