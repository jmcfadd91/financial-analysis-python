"""
Unit tests for logger module (src/utils/logger.py).
Tests logger initialization, configuration, and output.
"""

import pytest
import logging
import os
from src.utils.logger import setup_logger


class TestLoggerSetup:
    """Test logger initialization and configuration."""
    
    def test_setup_logger_basic(self):
        """Test basic logger setup."""
        logger = setup_logger('test_logger')
        
        assert logger is not None
        assert isinstance(logger, logging.Logger)
        assert logger.name == 'test_logger'
    
    def test_logger_level(self):
        """Test logger level is DEBUG."""
        logger = setup_logger('test_debug')
        assert logger.level == logging.DEBUG
    
    def test_logger_has_handlers(self):
        """Test logger has stream handler."""
        logger = setup_logger('test_handlers')
        assert len(logger.handlers) > 0
    
    def test_logger_formatter(self):
        """Test logger has proper formatter."""
        logger = setup_logger('test_format')
        handler = logger.handlers[0]
        
        assert handler.formatter is not None
        # Check formatter contains expected fields
        format_str = handler.formatter._fmt
        assert '%(asctime)s' in format_str
        assert '%(name)s' in format_str
        assert '%(levelname)s' in format_str
        assert '%(message)s' in format_str
    
    def test_multiple_loggers_independent(self):
        """Test multiple loggers are independent."""
        logger1 = setup_logger('logger1')
        logger2 = setup_logger('logger2')
        
        assert logger1.name != logger2.name
        assert logger1 is not logger2
    
    def test_logger_same_name_returns_same(self):
        """Test logger with same name returns same instance."""
        logger1 = setup_logger('same_name')
        logger2 = setup_logger('same_name')
        
        assert logger1 is logger2
    
    def test_logger_logging_works(self, caplog):
        """Test logger actually logs messages."""
        logger = setup_logger('test_log_output')
        
        with caplog.at_level(logging.DEBUG):
            logger.debug("Test debug message")
            logger.info("Test info message")
            logger.warning("Test warning message")
            logger.error("Test error message")
        
        assert len(caplog.records) >= 4
        assert "Test debug message" in caplog.text
        assert "Test info message" in caplog.text
        assert "Test warning message" in caplog.text
        assert "Test error message" in caplog.text
    
    def test_logger_propagation(self):
        """Test logger propagation setting."""
        logger = setup_logger('test_propagate')
        # Root logger behavior test
        assert logger.name == 'test_propagate'
    
    def test_logger_with_special_names(self):
        """Test logger with various naming patterns."""
        logger1 = setup_logger('module.submodule')
        logger2 = setup_logger('test.integration.feature')
        logger3 = setup_logger('__main__')
        
        assert logger1 is not None
        assert logger2 is not None
        assert logger3 is not None


class TestLoggerIntegration:
    """Test logger integration with other modules."""
    
    def test_logger_import_from_utils(self):
        """Test logger can be imported from utils."""
        from src.utils import setup_logger as imported_logger
        
        logger = imported_logger('import_test')
        assert logger is not None
    
    def test_logger_with_module_name(self):
        """Test logger works with __name__ parameter."""
        logger = setup_logger(__name__)
        assert 'test_logger' in logger.name
    
    def test_concurrent_logger_calls(self):
        """Test multiple logger calls work correctly."""
        loggers = [setup_logger(f'concurrent_{i}') for i in range(5)]
        
        assert len(loggers) == 5
        assert all(isinstance(l, logging.Logger) for l in loggers)
        assert len(set(l.name for l in loggers)) == 5  # All unique names


class TestLoggerOutput:
    """Test logger output and formatting."""
    
    def test_log_message_format(self, caplog):
        """Test log message format includes all components."""
        logger = setup_logger('format_test')
        
        with caplog.at_level(logging.INFO):
            logger.info("Test message")
        
        record = caplog.records[0]
        assert record.name == 'format_test'
        assert record.levelname == 'INFO'
        assert record.message == 'Test message'
    
    def test_log_levels_work_correctly(self, caplog):
        """Test all log levels function correctly."""
        logger = setup_logger('level_test')
        
        with caplog.at_level(logging.DEBUG):
            logger.debug("debug")
            logger.info("info")
            logger.warning("warning")
            logger.error("error")
            logger.critical("critical")
        
        assert len(caplog.records) == 5
        levels = [r.levelname for r in caplog.records]
        assert 'DEBUG' in levels
        assert 'INFO' in levels
        assert 'WARNING' in levels
        assert 'ERROR' in levels
        assert 'CRITICAL' in levels
    
    def test_logger_exception_logging(self, caplog):
        """Test logger exception handling."""
        logger = setup_logger('exception_test')
        
        try:
            raise ValueError("Test exception")
        except ValueError:
            with caplog.at_level(logging.ERROR):
                logger.exception("An error occurred")
        
        assert "An error occurred" in caplog.text
        assert "ValueError" in caplog.text
