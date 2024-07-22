import os
import json
import yaml
import logging
import time
from typing import Dict, List, Any
from tqdm import tqdm
from .llm_factory import LLMFactory

logger = logging.getLogger(__name__)

def load_config() -> Dict[str, Any]:
    """Load the config.yaml file from the same directory as the script."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join('config.yaml')
    try:
        with open(config_path, 'r') as config_file:
            return yaml.safe_load(config_file)
    except FileNotFoundError:
        logger.error(f"config.yaml not found in the app directory: {script_dir}")
        return None
    except yaml.YAMLError as e:
        logger.error(f"Error parsing config.yaml: {e}", exc_info=True)
        return None

def load_json_file(file_path: str) -> Dict[str, Any]:
    """Load a JSON file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON file {file_path}: {e}", exc_info=True)
        return {}

def save_json_file(data: Dict[str, Any], file_path: str) -> None:
    """Save data to a JSON file."""
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Data saved to {file_path}")
    except IOError as e:
        logger.error(f"Error saving data to {file_path}: {e}", exc_info=True)

def categorize_bookmarks(organize_all: bool = False):
    logger.info("Starting bookmark categorization process")
    config = load_config()
    if config is None:
        logger.error("Failed to load config. Exiting.")
        return

    max_categories = config.get('max_categories', 20)
    protected_folders = config.get('Protected Folders', [])
    llm_type = config.get('llm_type', 'openai')
    batch_size = config.get('batch_size', 10)

    logger.info(f"Using LLM type: {llm_type}")
    llm = LLMFactory.create_llm(llm_type)

    input_file = os.path.join('data', 'reorganized_bookmarks.json')
    categories_file = os.path.join('data', 'categories.json')
    output_file = os.path.join('data', 'categorized_bookmarks.json')

    bookmarks = load_json_file(input_file)
    if not bookmarks:
        logger.error("Failed to load bookmarks. Exiting.")
        return

    existing_categories = [cat for cat in bookmarks.keys() if cat not in protected_folders and cat.lower() != "uncategorized"]
    logger.info(f"Loaded {len(existing_categories)} existing categories")

    if organize_all:
        categorized_bookmarks = {folder: bookmarks[folder] for folder in bookmarks if folder in protected_folders}
        bookmarks_to_categorize = []
        for folder, content in bookmarks.items():
            if folder not in protected_folders and folder != 'Uncategorized':
                bookmarks_to_categorize.extend(content.get('bookmarks', []))
        bookmarks_to_categorize.extend(bookmarks.get('Uncategorized', {}).get('bookmarks', []))
    else:
        categorized_bookmarks = {folder: bookmarks[folder] for folder in bookmarks if folder != 'Uncategorized'}
        bookmarks_to_categorize = bookmarks.get('Uncategorized', {}).get('bookmarks', [])

    logger.info(f"Organizing {'all' if organize_all else 'only uncategorized'} bookmarks. Total bookmarks to categorize: {len(bookmarks_to_categorize)}")

    total_bookmarks = len(bookmarks_to_categorize)
    processed_bookmarks = 0
    total_inference_time = 0
    
    with tqdm(total=total_bookmarks, desc="Processing bookmarks", unit="bookmark") as pbar:
        for i in range(0, total_bookmarks, batch_size):
            batch = bookmarks_to_categorize[i:i+batch_size]
            is_first_iteration = (i == 0)
            
            start_time = time.time()
            batch_categorization = llm.categorize_bookmarks(batch, existing_categories, is_first_iteration)
            end_time = time.time()
            
            inference_time = end_time - start_time
            total_inference_time += inference_time
            processed_bookmarks += len(batch)
            
            for idx, category in batch_categorization.items():
                bookmark = batch[int(idx)-1]
                
                if category not in categorized_bookmarks:
                    if len(existing_categories) < max_categories:
                        existing_categories.append(category)
                        categorized_bookmarks[category] = {"parent": None, "bookmarks": []}
                        logger.debug(f"Created new category: {category}")
                    else:
                        category = "Other"
                        if "Other" not in categorized_bookmarks:
                            categorized_bookmarks["Other"] = {"parent": None, "bookmarks": []}
                            logger.debug("Created 'Other' category as max categories reached")
                
                categorized_bookmarks[category]["bookmarks"].append(bookmark)
                logger.debug(f"Categorized bookmark '{bookmark['title']}' into '{category}'")
            
            avg_inference_time = total_inference_time / processed_bookmarks
            remaining_bookmarks = total_bookmarks - processed_bookmarks
            estimated_time_remaining = avg_inference_time * remaining_bookmarks
            
            pbar.set_postfix({
                'Avg. Inference': f'{avg_inference_time:.2f}s',
                'Est. Remaining': f'{estimated_time_remaining:.2f}s'
            })
            pbar.update(len(batch))

    categorized_bookmarks['Uncategorized'] = {"parent": None, "bookmarks": []}

    final_bookmarks = categorized_bookmarks

    save_json_file(final_bookmarks, output_file)
    
    new_categories = [cat for cat in existing_categories if cat != "Other" and cat not in protected_folders]
    save_json_file(new_categories, categories_file)
    
    logger.info("Bookmark categorization completed. Results saved in 'data/categorized_bookmarks.json'.")
    logger.info(f"Total categories: {len(final_bookmarks)}")
    logger.info(f"Total bookmarks categorized: {sum(len(v['bookmarks']) for v in final_bookmarks.values())}")

if __name__ == "__main__":
    organize_all = input("Organize all bookmarks? (y/n): ").lower() == 'y'
    categorize_bookmarks(organize_all)