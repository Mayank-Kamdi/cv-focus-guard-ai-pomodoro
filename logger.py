"""
Logging Module for Focus Guard

Provides centralized logging functionality with both file and console output.
"""

import logging
import logging.handlers
from config import LOG_FILE, LOG_LEVEL, LOG_FORMAT, LOG_DATE_FORMAT


def setup_logger(name: str) -> logging.Logger:
    """
    Setup and configure logger for the application.

    Args:
        name (str): Name of the logger (typically __name__)

    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL))

    # Formatter
    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    # File handler - writes to log file
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            LOG_FILE,
            maxBytes=5 * 1024 * 1024,  # 5 MB
            backupCount=5,
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not setup file logging: {e}")

    # Console handler - writes to console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


# Create module-level logger
logger = setup_logger(__name__)
