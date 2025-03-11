# src/anki_creator/logging.py
import logging
import sys
from pathlib import Path


def setup_logging(log_file: Path | None = None, debug: bool = False) -> logging.Logger:
    """Configure logging for the application.

    Args:
        log_file: Optional path to log file
        debug: Whether to enable debug logging
    """
    logger = logging.getLogger("anki_creator")
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    # Create formatters
    detailed_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    simple_formatter = logging.Formatter("%(levelname)s: %(message)s")

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(simple_formatter)
    console_handler.setLevel(logging.DEBUG if debug else logging.INFO)
    logger.addHandler(console_handler)

    # File handler (if log_file specified)
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(detailed_formatter)
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)

    return logger
