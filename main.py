
import os
import sys
import logging
from src import import_bookmarks, validate_bookmarks, export_bookmarks, reorganize_bookmarks
from src.categorize_bookmarks import categorize_bookmarks
from src.log_config import setup_logging
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
import signal

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT_DIR, 'data')
console = Console()

def get_user_choice(prompt, options):
    choices = [f"[cyan]{i}[/cyan]. {option}" for i, option in enumerate(options, 1)]
    panel = Panel("\n".join(choices), title=prompt, expand=False)
    console.print(panel)
    return Prompt.ask("Enter your choice", choices=[str(i) for i in range(1, len(options) + 1)])

def signal_handler(sig, frame):
    console.print("\n[yellow]Interrupt received. Exiting gracefully...[/yellow]")
    sys.exit(0)

def main():
    signal.signal(signal.SIGINT, signal_handler)
    setup_logging()
    logger = logging.getLogger(__name__)

    console.print("[bold green]Welcome to Bookmarks Organizer[/bold green]")

    # Determine scope
    scope_options = ["Sort all bookmarks", "Sort uncategorized bookmarks only"]
    scope = int(get_user_choice("Choose sorting scope:", scope_options))
    reorganize_all = (scope == 1)

    # Ensure data directory exists
    os.makedirs(DATA_DIR, exist_ok=True)
    logger.info(f"Ensured data directory exists: {DATA_DIR}")

    try:
        # Import bookmarks
        console.print("[green]Importing bookmarks...[/green]")
        import_bookmarks(ROOT_DIR, DATA_DIR)

        # Validate bookmarks
        console.print("[yellow]Validating bookmarks and retrieving metadata...[/yellow]")
        validate_bookmarks(DATA_DIR, retrieve_metadata=True, process_all=reorganize_all)

        # Reorganize bookmarks
        console.print("[blue]Reorganizing bookmarks...[/blue]")
        reorganize_bookmarks(reorganize_all)

        # Categorize bookmarks
        console.print("[magenta]Categorizing bookmarks...[/magenta]")
        categorize_bookmarks(reorganize_all)

        # Export bookmarks
        console.print("[cyan]Exporting bookmarks...[/cyan]")
        export_bookmarks(DATA_DIR, ROOT_DIR)

    except Exception as e:
        console.print(f"[bold red]An error occurred: {str(e)}[/bold red]")
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        sys.exit(1)

    console.print("[bold green]Bookmark processing completed.[/bold green]")

if __name__ == "__main__":
    main()