import json
import html
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import os
import chardet
import yaml
import logging
from typing import Dict, Any
from tqdm import tqdm

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

def check_url(url, timeout=10):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, timeout=timeout, headers=headers, allow_redirects=True)
        if response.status_code == 200:
            logger.debug(f"Successfully accessed URL: {url}")
            return True, response
        else:
            logger.debug(f"Failed to access URL: {url}. Status code: {response.status_code}")
            return False, None
    except requests.RequestException as e:
        logger.debug(f"Error accessing URL: {url}. Error: {str(e)}")
        return False, None

def scrape_metadata(response):
    detected = chardet.detect(response.content)
    encoding = detected['encoding'] if detected['encoding'] else 'utf-8'

    try:
        soup = BeautifulSoup(response.content.decode(encoding), 'html.parser')
    except UnicodeDecodeError:
        logger.debug(f"UnicodeDecodeError with {encoding}. Falling back to UTF-8 with error ignoring.")
        soup = BeautifulSoup(response.content.decode('utf-8', errors='ignore'), 'html.parser')

    title = soup.title.string if soup.title else ''
    description_tag = soup.find('meta', attrs={'name': 'description'})
    description = description_tag.get('content', '') if description_tag else ''
    
    # Convert HTML entities to Unicode characters, handling None values
    title = html.unescape(title) if title else ''
    description = html.unescape(description) if description else ''
    
    # Remove extra whitespace
    title = ' '.join(title.split()).strip()
    description = ' '.join(description.split()).strip()

    # Re-encode special characters as HTML entities
    title = html.escape(title, quote=False)
    description = html.escape(description, quote=False)

    logger.debug(f"Scraped metadata - Title: {title[:30]}..., Description: {description[:30]}...")
    return title, description

def needs_validation(bookmark, days_threshold):
    if 'date-verified' not in bookmark:
        logger.debug(f"Bookmark {bookmark['url']} has never been verified.")
        return True
    last_verified = datetime.fromisoformat(bookmark['date-verified'])
    time_since_verification = datetime.now() - last_verified
    needs_valid = time_since_verification > timedelta(days=days_threshold)
    if needs_valid:
        logger.debug(f"Bookmark {bookmark['url']} needs validation.")
    return needs_valid

def process_bookmarks(data, days_threshold, retrieve_metadata):
    retired_urls = []
    updated_count = 0
    skipped_count = 0
    total_bookmarks = sum(len(content['bookmarks']) for content in data.values() if 'bookmarks' in content)
    logger.info(f"Starting to process {total_bookmarks} bookmarks.")

    with tqdm(total=total_bookmarks, desc="Processing bookmarks", unit="bookmark") as pbar:
        for category, content in data.items():
            if 'bookmarks' in content:
                updated_bookmarks = []
                for bookmark in content['bookmarks']:
                    if needs_validation(bookmark, days_threshold):
                        url = bookmark['url']
                        is_active, response = check_url(url)
                        
                        if is_active:
                            if retrieve_metadata:
                                title, description = scrape_metadata(response)
                                updated_bookmark = {
                                    'title': title or bookmark['title'],
                                    'url': url,
                                    'description': description,
                                    'date-verified': datetime.now().isoformat()
                                }
                            else:
                                updated_bookmark = {
                                    'title': bookmark['title'],
                                    'url': url,
                                    'description': bookmark.get('description', ''),
                                    'date-verified': datetime.now().isoformat()
                                }
                            updated_bookmarks.append(updated_bookmark)
                            logger.debug(f"Updated bookmark: {url}")
                            updated_count += 1
                        else:
                            retired_urls.append(url)
                            logger.debug(f"Retired URL: {url}")
                    else:
                        updated_bookmarks.append(bookmark)
                        skipped_count += 1
                    pbar.update(1)
                
                content['bookmarks'] = updated_bookmarks

    logger.info(f"Processed all bookmarks. Updated: {updated_count}, Skipped: {skipped_count}, Retired: {len(retired_urls)}")
    return data, retired_urls, updated_count > 0 or len(retired_urls) > 0

def validate_bookmarks(data_dir, days_threshold=30, retrieve_metadata=False, process_all=True):
    logger.info(f"Starting bookmark validation process. Threshold set to {days_threshold} days. Retrieve metadata: {retrieve_metadata}")
    
    input_file = os.path.join(data_dir, 'bookmarks.json')
    output_file = os.path.join(data_dir, 'updated_bookmarks.json')
    retired_file = os.path.join(data_dir, 'retired_bookmarks.json')

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"Successfully loaded bookmarks from {input_file}")
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from {input_file}: {str(e)}", exc_info=True)
        return
    except FileNotFoundError:
        logger.error(f"Input file not found: {input_file}")
        return

    if process_all:
        bookmarks_to_process = data
    else:
        bookmarks_to_process = {'Uncategorized': data.get('Uncategorized', {'bookmarks': []})}
    
    if days_threshold > 0 or retrieve_metadata:
        updated_data, retired_urls, changes_made = process_bookmarks(bookmarks_to_process, days_threshold, retrieve_metadata)
    else:
        updated_data, retired_urls, changes_made = bookmarks_to_process, [], True

    if not process_all:
        # Merge the updated Uncategorized bookmarks back into the original data
        data['Uncategorized'] = updated_data['Uncategorized']
        updated_data = data

    if changes_made:
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(updated_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Updated bookmarks saved to {output_file}")
        except IOError as e:
            logger.error(f"Error writing to {output_file}: {str(e)}", exc_info=True)

        if retired_urls:
            try:
                with open(retired_file, 'w', encoding='utf-8') as f:
                    json.dump(retired_urls, f, indent=2, ensure_ascii=False)
                logger.info(f"Retired URLs saved to {retired_file}")
            except IOError as e:
                logger.error(f"Error writing to {retired_file}: {str(e)}", exc_info=True)
    else:
        logger.info("No changes were made. All bookmarks are up to date.")

    logger.info("Bookmark validation process completed.")

if __name__ == "__main__":
    config = load_config()
    if config is None:
        logger.error("Failed to load configuration. Exiting.")
        exit(1)
    
    data_dir = config.get('data_dir', os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data'))
    days_threshold = config.get('days_threshold', 30)
    
    logger.info(f"Starting script with data_dir: {data_dir} and days_threshold: {days_threshold}")
    validate_bookmarks(data_dir, days_threshold)