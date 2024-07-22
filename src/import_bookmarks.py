import json
import os
import re
import logging
from typing import Dict

logger = logging.getLogger(__name__)

def parse_bookmarks(file_content: str) -> Dict[str, Dict]:
    lines = file_content.split('\n')
    bookmarks = {}
    current_folder = None
    folder_stack = []

    logger.info("Starting to parse bookmarks")
    for line in lines:
        line = line.strip()
        if line.startswith('<DT><H3'):
            folder_name = parse_folder_name(line)
            parent = folder_stack[-1] if folder_stack else None
            bookmarks[folder_name] = {
                "parent": parent,
                "bookmarks": []
            }
            folder_stack.append(folder_name)
            current_folder = folder_name
            logger.debug(f"Parsed folder: {folder_name}")
        elif line.startswith('<DT><A'):
            if current_folder:
                bookmark = parse_bookmark(line)
                bookmarks[current_folder]["bookmarks"].append(bookmark)
                logger.debug(f"Parsed bookmark: {bookmark['title']} in folder {current_folder}")
        elif line == '</DL><p>' and folder_stack:
            folder_stack.pop()
            current_folder = folder_stack[-1] if folder_stack else None

    logger.info(f"Finished parsing bookmarks. Total folders: {len(bookmarks)}")
    return bookmarks

def parse_folder_name(line: str) -> str:
    match = re.search(r'<H3[^>]*>(.*?)</H3>', line)
    return match.group(1) if match else "Unnamed Folder"

def parse_bookmark(line: str) -> Dict[str, str]:
    url_match = re.search(r'HREF="(.*?)"', line)
    title_match = re.search(r'>(.*?)</A>', line)
    return {
        "title": title_match.group(1) if title_match else "Untitled",
        "url": url_match.group(1) if url_match else ""
    }

def convert_to_json(input_file: str, output_file: str):
    logger.info(f"Starting conversion of {input_file} to JSON format")
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        bookmarks = parse_bookmarks(content)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(bookmarks, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Successfully converted bookmarks to JSON. Saved as {output_file}")
    except Exception as e:
        logger.error(f"Error during conversion: {str(e)}", exc_info=True)

def import_bookmarks(root_dir, data_dir):
    logger.info("Starting bookmark import process")
    input_file = os.path.join(root_dir, "bookmarks.html")
    output_file = os.path.join(data_dir, "bookmarks.json")
    
    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}")
        return
    
    convert_to_json(input_file, output_file)
    logger.info("Bookmark import process completed")

if __name__ == "__main__":
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(root_dir, 'data')
    
    logger.debug(f"Starting script with root_dir: {root_dir} and data_dir: {data_dir}")
    import_bookmarks(root_dir, data_dir)