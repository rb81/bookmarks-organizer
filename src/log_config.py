import logging

def setup_logging():
    # Clear existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers = []

    logging.basicConfig(
        filename='data/bookmarks_organizer.log',
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create a StreamHandler to also log to console
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    # Remove the name from the console output format
    formatter = logging.Formatter('%(levelname)s: %(message)s')
    console.setFormatter(formatter)
    
    # Check if the handler already exists before adding
    if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
        root_logger.addHandler(console)