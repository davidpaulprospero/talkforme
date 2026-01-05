"""Logging setup for Talk For Me."""

import logging
import sys
from typing import Optional


def setup_logger(
    level: str = "INFO",
    name: str = "talk_for_me",
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Set up and configure logger.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        name: Logger name
        format_string: Custom format string (optional)

    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Remove existing handlers to avoid duplicates
    logger.handlers = []

    # Create console handler (use stderr to avoid mixing with stdout JSON)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Create formatter
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    formatter = logging.Formatter(format_string)
    console_handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(console_handler)

    return logger
