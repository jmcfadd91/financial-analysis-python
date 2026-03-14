"""
Production-grade logging configuration for financial analysis platform.
Provides consistent logging across all modules with file and console output.
"""

import logging
import sys
from typing import Optional


def configure_logging(level: str = "INFO") -> None:
    """
    Configure root logger with dual handlers (console + file).
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Example:
        >>> configure_logging("DEBUG")
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level.upper())
    
    # Prevent duplicate handlers
    if root_logger.handlers:
        return
    
    # Format: timestamp - name - level - message
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console handler (INFO and above)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (ERROR and above)
    file_handler = logging.FileHandler("financial_analysis.log")
    file_handler.setLevel(logging.ERROR)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Get a configured logger for a specific module.
    
    Args:
        name: Logger name (typically __name__)
        level: Optional logging level override
    
    Returns:
        Configured logger instance
    
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Module initialized")
    """
    logger = logging.getLogger(name)
    
    if level:
        logger.setLevel(level.upper())
    
    return logger


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
