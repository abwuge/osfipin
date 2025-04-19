#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
import codecs
from datetime import datetime
from logging.handlers import RotatingFileHandler


class EncodedRotatingFileHandler(RotatingFileHandler):
    """
    Extended version of RotatingFileHandler that supports encoding
    """

    def __init__(
        self, filename, mode="a", maxBytes=0, backupCount=0, encoding="utf-8", delay=0
    ):
        super().__init__(filename, mode, maxBytes, backupCount, encoding, delay)

    def _open(self):
        """
        Open the current base file with specific encoding
        """
        return codecs.open(self.baseFilename, self.mode, self.encoding)


class Logger:
    """
    Logger class for managing application logging with multi-level support
    """

    # Log levels mapping
    LEVELS = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }

    def __init__(
        self,
        name="osfipin",
        log_dir="logs",
        console_level="info",
        file_level="debug",
        max_size=1024 * 1024 * 5,
        backup_count=3,
    ):
        """
        Initialize logger with specified configuration

        Args:
            name: Logger name
            log_dir: Directory to store log files
            console_level: Minimum level for console output
            file_level: Minimum level for file output
            max_size: Maximum size of log file before rotation (default: 5MB)
            backup_count: Number of backup files to keep
        """
        self.name = name
        self.log_dir = log_dir
        self.console_level = self.LEVELS.get(console_level.lower(), logging.INFO)
        self.file_level = self.LEVELS.get(file_level.lower(), logging.DEBUG)
        self.max_size = max_size
        self.backup_count = backup_count
        self.lang = None

        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(min(self.console_level, self.file_level))

        # Create logs directory if it doesn't exist
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # Create log file with date in name
        date_str = datetime.now().strftime("%Y%m%d")
        log_file = os.path.join(log_dir, f"{name}_{date_str}.log")

        # Set up formatters
        console_formatter = logging.Formatter("%(levelname)s: %(message)s")
        file_formatter = logging.Formatter("%(asctime)s [%(levelname)s]: %(message)s")

        # Set up console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.console_level)
        console_handler.setFormatter(console_formatter)

        # Set up file handler with rotation and UTF-8 encoding
        file_handler = EncodedRotatingFileHandler(
            log_file,
            maxBytes=self.max_size,
            backupCount=self.backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(self.file_level)
        file_handler.setFormatter(file_formatter)

        # Clear any existing handlers
        self.logger.handlers = []

        # Add handlers to logger
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

    def set_language_instance(self, lang):
        """
        Set language instance for localized logging

        Args:
            lang: Language instance with get method
        """
        self.lang = lang

    def _format_message(self, message, *args):
        """
        Format message with args and translate if language instance is available

        Args:
            message: Message string or language key
            *args: Format arguments

        Returns:
            Formatted and translated message
        """
        if self.lang and isinstance(message, str) and not message.startswith("__"):
            try:
                return self.lang.get(message, *args)
            except Exception:
                # If translation fails, use original message with formatting
                if args:
                    return message.format(*args)
                return message
        else:
            # Use direct formatting if no language instance or message starts with "__"
            if message.startswith("__"):
                message = message[2:]
            if args:
                return message.format(*args)
            return message

    def debug(self, message, *args):
        """Log debug message"""
        self.logger.debug(self._format_message(message, *args))

    def info(self, message, *args):
        """Log info message"""
        self.logger.info(self._format_message(message, *args))

    def warning(self, message, *args):
        """Log warning message"""
        self.logger.warning(self._format_message(message, *args))

    def error(self, message, *args):
        """Log error message"""
        self.logger.error(self._format_message(message, *args))

    def critical(self, message, *args):
        """Log critical message"""
        self.logger.critical(self._format_message(message, *args))


# Global logger instance
_logger = None


def initialize_logger(
    name="osfipin",
    log_dir="logs",
    console_level="info",
    file_level="debug",
    max_size=1024 * 1024 * 5,
    backup_count=3,
):
    """
    Initialize global logger instance

    Args:
        name: Logger name
        log_dir: Directory to store log files
        console_level: Minimum level for console output
        file_level: Minimum level for file output
        max_size: Maximum size of log file before rotation
        backup_count: Number of backup files to keep

    Returns:
        Logger instance
    """
    global _logger
    _logger = Logger(name, log_dir, console_level, file_level, max_size, backup_count)
    return _logger


def get_logger():
    """
    Get global logger instance

    Returns:
        Logger instance (creates one with default settings if none exists)
    """
    global _logger
    if _logger is None:
        _logger = initialize_logger()
    return _logger
