"""
Logging Configuration Module

This module provides centralized logging configuration for the SpineModeling application.
It sets up console and file handlers with appropriate formatting and log levels.

Usage:
    from spine_modeling.utils.logging_config import setup_logging

    # At application startup
    setup_logging(level='INFO')  # or 'DEBUG' for development

    # Then use logging throughout the application
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Application started")
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional
import sys

# Default log format
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEBUG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"

# Log file settings
DEFAULT_LOG_DIR = Path.home() / ".spinemodeling" / "logs"
DEFAULT_LOG_FILE = "spinemodeling.log"
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5


def setup_logging(
    level: str = "INFO",
    log_to_file: bool = True,
    log_to_console: bool = True,
    log_dir: Optional[Path] = None,
    log_file: str = DEFAULT_LOG_FILE,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Configure logging for the SpineModeling application.

    Args:
        level: Log level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        log_to_file: Enable file logging with rotation
        log_to_console: Enable console logging
        log_dir: Directory for log files (default: ~/.spinemodeling/logs)
        log_file: Log file name (default: spinemodeling.log)
        format_string: Custom log format string

    Returns:
        Root logger instance

    Example:
        >>> setup_logging(level='DEBUG', log_to_file=True)
        >>> logger = logging.getLogger('spine_modeling.imaging')
        >>> logger.debug("Loading DICOM file...")
    """
    # Determine log level
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Choose format based on level
    if format_string is None:
        format_string = DEBUG_FORMAT if numeric_level == logging.DEBUG else DEFAULT_FORMAT

    # Create formatter
    formatter = logging.Formatter(format_string)

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Add console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # Add file handler with rotation
    if log_to_file:
        log_directory = log_dir or DEFAULT_LOG_DIR
        log_directory.mkdir(parents=True, exist_ok=True)
        log_path = log_directory / log_file

        file_handler = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=MAX_LOG_SIZE,
            backupCount=BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Configure specific module log levels
    _configure_module_levels()

    root_logger.info(f"Logging configured: level={level}, file={log_to_file}, console={log_to_console}")
    return root_logger


def _configure_module_levels() -> None:
    """
    Configure log levels for specific modules.

    Some modules may need different log levels than the root.
    """
    # Reduce noise from external libraries
    logging.getLogger('PIL').setLevel(logging.WARNING)
    logging.getLogger('matplotlib').setLevel(logging.WARNING)
    logging.getLogger('vtk').setLevel(logging.WARNING)

    # SpineModeling module levels (can be customized)
    # logging.getLogger('spine_modeling.visualization').setLevel(logging.DEBUG)
    # logging.getLogger('spine_modeling.algorithms').setLevel(logging.DEBUG)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the given name.

    Convenience function that ensures proper naming convention.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing image...")
    """
    return logging.getLogger(name)


def set_log_level(level: str, module: Optional[str] = None) -> None:
    """
    Change log level at runtime.

    Args:
        level: New log level
        module: Specific module name, or None for root logger

    Example:
        >>> set_log_level('DEBUG')  # Set root to DEBUG
        >>> set_log_level('WARNING', 'spine_modeling.imaging')  # Quiet imaging module
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    if module:
        logging.getLogger(module).setLevel(numeric_level)
    else:
        logging.getLogger().setLevel(numeric_level)
        for handler in logging.getLogger().handlers:
            handler.setLevel(numeric_level)


class LogContext:
    """
    Context manager for temporarily changing log level.

    Example:
        >>> with LogContext('DEBUG'):
        ...     # Verbose logging in this block
        ...     process_complex_operation()
        >>> # Log level restored after block
    """

    def __init__(self, level: str, module: Optional[str] = None):
        self.level = level
        self.module = module
        self.previous_level = None

    def __enter__(self):
        logger = logging.getLogger(self.module) if self.module else logging.getLogger()
        self.previous_level = logger.level
        set_log_level(self.level, self.module)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.previous_level is not None:
            logger = logging.getLogger(self.module) if self.module else logging.getLogger()
            logger.setLevel(self.previous_level)
        return False


# Convenience function for quick debug sessions
def enable_debug_logging() -> None:
    """Enable DEBUG level logging to console only."""
    setup_logging(level='DEBUG', log_to_file=False, log_to_console=True)


def disable_logging() -> None:
    """Disable all logging (useful for tests)."""
    logging.getLogger().handlers.clear()
    logging.getLogger().addHandler(logging.NullHandler())
