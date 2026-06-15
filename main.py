#!/usr/bin/env python3
"""Bookmarks Organizer - Organize browser bookmarks using AI."""

import argparse
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv
from openai import OpenAI
import os

from src.parser import parse_bookmarks, extract_all_bookmarks, extract_uncategorized_bookmarks
from src.organizer import organize_bookmarks, build_organized_tree
from src.writer import write_bookmarks
from src.progress import get_progress_path, load_progress, clear_progress


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Organize browser bookmarks into categories using AI.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python main.py bookmarks.html
  python main.py bookmarks.html -o organized.html
  python main.py bookmarks.html --uncategorized-only
  python main.py bookmarks.html --model gpt-4o --base-url https://openrouter.ai/api/v1
""",
    )
    parser.add_argument("input", help="Path to bookmarks HTML file (Netscape format)")
    parser.add_argument("-o", "--output", default="bookmarks_organized.html", help="Output file path (default: bookmarks_organized.html)")
    parser.add_argument("--uncategorized-only", action="store_true", help="Only sort bookmarks in the 'Uncategorized' folder")
    parser.add_argument("--model", default=None, help="Model to use (overrides .env and config)")
    parser.add_argument("--base-url", default=None, help="API base URL (overrides .env)")
    parser.add_argument("--api-key", default=None, help="API key (overrides .env)")
    parser.add_argument("--max-categories", type=int, default=None, help="Max categories to create")
    parser.add_argument("--batch-size", type=int, default=None, help="Bookmarks per LLM batch")
    parser.add_argument("--no-resume", action="store_true", help="Ignore saved progress and start fresh")

    args = parser.parse_args()

    # Load config
    config = {}
    config_path = Path(__file__).parent / "config.yaml"
    if config_path.exists():
        with open(config_path) as f:
            config = yaml.safe_load(f) or {}

    # Resolve settings (CLI > env > config > defaults)
    api_key = args.api_key or os.getenv("API_KEY") or os.getenv("OPENAI_API_KEY")
    base_url = args.base_url or os.getenv("BASE_URL", "https://api.openai.com/v1")
    model = args.model or os.getenv("MODEL", config.get("model", "gpt-4o-mini"))
    max_categories = args.max_categories or config.get("max_categories", 20)
    batch_size = args.batch_size or config.get("batch_size", 10)
    protected_folders = config.get("protected_folders", [])

    if not api_key:
        print("Error: No API key provided.")
        print("Set API_KEY in .env, pass --api-key, or set OPENAI_API_KEY environment variable.")
        sys.exit(1)

    # Read input file
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: File not found: {input_path}")
        sys.exit(1)

    print(f"Reading bookmarks from: {input_path}")
    html_content = input_path.read_text(encoding="utf-8")

    # Parse bookmarks
    root = parse_bookmarks(html_content)

    # Extract bookmarks based on mode
    if args.uncategorized_only:
        print("Mode: Organizing uncategorized bookmarks only")
        bookmarks, kept_folders = extract_uncategorized_bookmarks(root, protected_folders)
        existing_categories = [f.title for f in kept_folders]
    else:
        print("Mode: Organizing all bookmarks")
        bookmarks, kept_folders = extract_all_bookmarks(root, protected_folders)
        existing_categories = []

    if not bookmarks:
        print("No bookmarks to organize.")
        sys.exit(0)

    print(f"Found {len(bookmarks)} bookmarks to organize")
    print(f"Protected folders: {[f.title for f in kept_folders]}")
    print(f"Using model: {model}")
    print(f"API base: {base_url}")
    print()

    # Check for saved progress
    progress_path = get_progress_path(args.output)
    start_index = 0
    resumed_categories = None

    if not args.no_resume:
        progress = load_progress(progress_path)
        if progress and progress["total_count"] == len(bookmarks):
            already_done = len(bookmarks) - len(progress["remaining_indices"])
            print(f"Found saved progress: {already_done}/{len(bookmarks)} bookmarks already categorized.")
            print("Resuming... (use --no-resume to start fresh)\n")
            start_index = already_done
            resumed_categories = progress["categories"]
        elif progress:
            print("Found saved progress but bookmark count changed. Starting fresh.\n")
            clear_progress(progress_path)
    else:
        clear_progress(progress_path)

    # Initialize OpenAI client
    client = OpenAI(api_key=api_key, base_url=base_url)

    # Organize bookmarks (with graceful interrupt handling)
    print("Categorizing bookmarks...")
    try:
        categories = organize_bookmarks(
            bookmarks=bookmarks,
            client=client,
            model=model,
            max_categories=max_categories,
            batch_size=batch_size,
            existing_categories=existing_categories,
            progress_path=progress_path,
            start_index=start_index,
            resumed_categories=resumed_categories,
        )
    except KeyboardInterrupt:
        print("\n\nInterrupted! Progress has been saved.")
        print("Run the same command again to resume, or use --no-resume to start over.")
        sys.exit(130)

    print(f"\nCreated {len(categories)} categories:")
    for cat, bms in sorted(categories.items()):
        print(f"  {cat}: {len(bms)} bookmarks")

    # Build output tree
    organized = build_organized_tree(categories, kept_folders)

    # Write output
    output_html = write_bookmarks(organized)
    output_path = Path(args.output)
    output_path.write_text(output_html, encoding="utf-8")

    # Clean up progress file on success
    clear_progress(progress_path)

    print(f"\nOrganized bookmarks written to: {output_path}")


if __name__ == "__main__":
    main()
