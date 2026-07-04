"""
Structured logging configuration.

Sets up dual-output logging:
    1. File handler  → logs/trading_bot.log  (detailed, with timestamps)
    2. Console handler → stdout              (concise, for user feedback)

Usage:
    from bot.logging_config import setup_logging
    logger = setup_logging(log_dir, log_level)
    logger.info("Order placed successfully", extra={...})
"""

import logging
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Custom Formatter for log files (includes all context)
# ---------------------------------------------------------------------------
FILE_LOG_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s"
)

# Console gets a cleaner format — no noise for the end user
CONSOLE_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(message)s"

LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_FILENAME = "trading_bot.log"


def setup_logging(log_dir: Path, log_level: str = "INFO") -> logging.Logger:
    """Configure and return the application-wide logger.

    Creates the log directory if it doesn't exist. Attaches a rotating-safe
    file handler and a console handler with appropriate formatters.

    Args:
        log_dir:   Directory where log files will be written.
        log_level: Minimum severity to capture (DEBUG, INFO, WARNING, ERROR).

    Returns:
        Configured root logger for the 'trading_bot' namespace.
    """
    # Ensure log directory exists
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / LOG_FILENAME

    # Create namespaced logger (avoids polluting the root logger)
    logger = logging.getLogger("trading_bot")
    logger.setLevel(getattr(logging, log_level, logging.INFO))

    # Prevent duplicate handlers on repeated calls
    if logger.handlers:
        return logger

    # --- File Handler (detailed) ---
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)  # Capture everything to file
    file_handler.setFormatter(
        logging.Formatter(FILE_LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    )

    # --- Console Handler (concise) ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level, logging.INFO))
    console_handler.setFormatter(
        logging.Formatter(CONSOLE_LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    )

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.debug("Logging initialized — file: %s | level: %s", log_file, log_level)

    return logger
