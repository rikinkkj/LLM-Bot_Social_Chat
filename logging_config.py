import os
import logging
import datetime
from pythonjsonlogger import jsonlogger

def setup_logging():
    """
    Sets up a unique, timestamped JSONL logger for each simulation run.
    """
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = os.path.join(log_dir, f"sim_{timestamp}.jsonl")

    # Get the root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Remove any existing handlers to avoid duplicate logs
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create a file handler for the new log file
    log_handler = logging.FileHandler(log_filename)

    # Create a JSON formatter
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s'
    )
    log_handler.setFormatter(formatter)

    # Add the handler to the root logger
    logger.addHandler(log_handler)

    # Also add a handler for the console for real-time feedback
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    logging.info("Structured logging initialized.", extra={'event': 'system.init'})
    return log_filename
