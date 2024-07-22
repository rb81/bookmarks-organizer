import json
import os
import datetime
import logging
from typing import Dict, TextIO

logger = logging.getLogger(__name__)

def generate_bookmark_file(bookmarks: Dict[str, Dict], output_file: str):
    logger.info(f"Starting to generate bookmark file: {output_file}")
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('''<!DOCTYPE NETSCAPE-Bookmark-file-1>
<!--This is an automatically generated file.
    It will be read and overwritten.
    Do Not Edit! -->
<Title>Bookmarks</Title>
<H1>Bookmarks</H1>
<DL><p>
''')
            
            write_folders(f, bookmarks)
            
            f.write('</DL><p>\n')
        logger.info(f"Successfully generated bookmark file: {output_file}")
    except IOError as e:
        logger.error(f"Error writing to file {output_file}: {str(e)}", exc_info=True)

def write_folders(f: TextIO, bookmarks: Dict[str, Dict], level: int = 0, parent: str = None):
    indent = '    ' * level
    for folder_name, folder_data in bookmarks.items():
        if folder_data['parent'] == parent:
            logger.debug(f"Writing folder: {folder_name}")
            f.write(f'{indent}<DT><H3 FOLDED ADD_DATE="{int(datetime.datetime.now().timestamp())}">{folder_name}</H3>\n')
            f.write(f'{indent}<DL><p>\n')
            
            # Write bookmarks in this folder
            for bookmark in folder_data['bookmarks']:
                logger.debug(f"Writing bookmark: {bookmark['title']}")
                f.write(f'{indent}    <DT><A HREF="{bookmark["url"]}">{bookmark["title"]}</A>\n')
            
            # Recursively write subfolders
            write_folders(f, bookmarks, level + 1, folder_name)
            
            f.write(f'{indent}</DL><p>\n')

def convert_to_html(input_file: str, output_file: str):
    logger.info(f"Starting conversion of {input_file} to HTML format")
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            bookmarks = json.load(f)
        
        generate_bookmark_file(bookmarks, output_file)
        logger.info(f"Successfully converted bookmarks to HTML. Saved as {output_file}")
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from {input_file}: {str(e)}", exc_info=True)
    except Exception as e:
        logger.error(f"Error during conversion: {str(e)}", exc_info=True)

def export_bookmarks(data_dir, root_dir):
    logger.info("Starting bookmark export process")
    input_file = os.path.join(data_dir, "categorized_bookmarks.json")
    output_file = os.path.join(root_dir, "bookmarks_new.html")
    
    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}")
        return
    
    convert_to_html(input_file, output_file)
    logger.info("Bookmark export process completed")

if __name__ == "__main__":
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    
    logger.debug(f"Starting script with root_dir: {root_dir} and data_dir: {data_dir}")
    export_bookmarks(data_dir, root_dir)