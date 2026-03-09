"""
Logging configuration for the financial analysis platform.
Provides centralized, production-grade logging setup.
"""

import logging
import sys
from datetime import datetime


def get_logger(name: str, log_level: str = "INFO") -> logging.Logger:
    """
    Get or create a logger with standardized formatting.
    
    Args:
        name (str): Logger name (typically __name__)
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        logging.Logger: Configured logger instance
    
    Example:
        logger = get_logger(__name__)
        logger.info("Application started")
    """
    logger = logging.getLogger(name)
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Set log level
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Create formatter with timestamp
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler (stdout for INFO+, stderr for ERROR+)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Error handler (stderr for errors)
    error_handler = logging.StreamHandler(sys.stderr)
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


def configure_logging(level: str = "INFO") -> None:
    """
    Configure root logger for the entire application.
    
    Args:
        level (str): Root logging level
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
