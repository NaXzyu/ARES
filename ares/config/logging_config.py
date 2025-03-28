"""Logging configuration for Ares Engine."""

import os
import sys
import logging
import logging.handlers
from pathlib import Path

from .base_config import BaseConfig
from ares.utils.paths import Paths

class LoggingConfig(BaseConfig):
    """Configuration class for managing logging settings."""
    
    def __init__(self):
        """Initialize the logging configuration."""
        super().__init__("logging")
        self.logger = None
        self.initialized = False
        
    def initialize(self, logs_dir=None, log_filename="engine.log"):
        """Initialize the logging system with the configured settings.
        
        Args:
            logs_dir (Path, optional): Directory to store log files. If None, use default.
            log_filename (str, optional): Name of log file. Defaults to "engine.log".
            
        Returns:
            bool: True if initialization succeeded
        """
        if self.initialized:
            return True
            
        # Load configuration if not already loaded
        if not self.loaded:
            self.load()
        
        # Ensure logs directory exists
        if logs_dir is None:
            # Use appropriate logs directory based on whether we're in a frozen app
            logs_dir = Paths.get_logs_dir(for_app=Paths.IS_FROZEN)
        else:
            logs_dir = Path(logs_dir)
            
        os.makedirs(logs_dir, exist_ok=True)
        
        # Get log level from configuration
        log_level_str = self.get("log_level", "INFO").upper()
        log_level = getattr(logging, log_level_str, logging.INFO)
        
        # Get rotation settings
        max_bytes = self.get_int("max_bytes", 1024 * 1024)  # 1 MB default
        backup_count = self.get_int("backup_count", 5)  # Keep 5 backups by default
        
        # Configure the root logger
        logger = logging.getLogger()
        logger.setLevel(log_level)
        
        # Clear any existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Set up file handler with rotation
        log_file = logs_dir / log_filename
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count
        )
        
        # Get formatter settings
        date_format = self.get("date_format", "%Y-%m-%d %H:%M:%S")
        log_format = self.get(
            "log_format", 
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        
        formatter = logging.Formatter(log_format, datefmt=date_format)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Add console handler if enabled
        if self.get_bool("console_output", True):
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        # Store the logger for later access
        self.logger = logger
        self.initialized = True
        
        # Log initialization message with appropriate path info
        project_root = Paths.PROJECT_ROOT
        logger.info(f"Logging initialized. Log file: {log_file}")
        logger.info(f"Project root: {project_root}")
        logger.info(f"Running in {'frozen' if Paths.IS_FROZEN else 'development'} mode")
        
        return True
        
    def get_logger(self):
        """Get the configured logger instance.
        
        Returns:
            logging.Logger: Configured logger or None if not initialized
        """
        return self.logger
