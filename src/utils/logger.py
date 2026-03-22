"""Logging factory for the financial analysis platform."""

import logging
import sys
from typing import Optional


def setup_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Set up a named logger with a StreamHandler at DEBUG level.

    Args:
        name: Logger name (typically __name__)
        level: Optional logging level override (defaults to DEBUG)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    effective_level = (level.upper() if level else "DEBUG")
    logger.setLevel(effective_level)

    if not logger.handlers:
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(effective_level)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
