"""Logging configuration for Ares Engine."""

import sys
import logging
import logging.config
from pathlib import Path

from ares.utils.log import Log
from ares.utils.paths import USER_LOGS_DIR, IS_FROZEN, PROJECT_ROOT
from .base_config import BaseConfig

# Get log directories
INI_DIR = PROJECT_ROOT / "ares" / "ini" if not IS_FROZEN else Path(sys._MEIPASS) / "ares" / "ini"
LOGGING_INI = INI_DIR / "logging.ini"

class LoggingConfig(BaseConfig):
    """Wrapper for logging configuration settings."""
    
    # Class variables
    _logging_initialized = False
    _subprocess_log_handler = None
    
    def __init__(self):
        super().__init__("logging")
        self._create_default_config()
        
    def _create_default_config(self):
        """Create default logging configuration based on logging.ini."""
        # Basic logger configuration
        self.set("loggers", "keys", "root,ares,build")
        
        # Root logger
        self.set("logger_root", "level", "INFO")
        self.set("logger_root", "handlers", "consoleHandler")
        
        # Ares logger
        self.set("logger_ares", "level", "INFO")
        self.set("logger_ares", "handlers", "consoleHandler,fileHandler")
        self.set("logger_ares", "qualname", "ares")
        self.set("logger_ares", "propagate", "0")
        
        # Build logger
        self.set("logger_build", "level", "DEBUG")
        self.set("logger_build", "handlers", "consoleHandler,buildFileHandler")
        self.set("logger_build", "qualname", "ares.build")
        self.set("logger_build", "propagate", "0")
        
        # Handlers definition
        self.set("handlers", "keys", "consoleHandler,fileHandler,buildFileHandler")
        
        # Formatters definition
        self.set("formatters", "keys", "simpleFormatter,detailedFormatter,consoleFormatter")
    
    def get_root_logger_level(self):
        """Get the root logger's level."""
        return self.get("logger_root", "level", "INFO")
    
    def get_ares_logger_level(self):
        """Get the ares logger's level."""
        return self.get("logger_ares", "level", "INFO")
    
    def get_build_logger_level(self):
        """Get the build logger's level."""
        return self.get("logger_build", "level", "DEBUG")
    
    def get_console_formatter(self):
        """Get the console formatter format string."""
        return self.get("formatter_consoleFormatter", "format", "%(message)s")
    
    def get_console_date_format(self):
        """Get the console formatter date format string."""
        return self.get("formatter_consoleFormatter", "datefmt", "%H:%M:%S")
    
    def get_detailed_formatter(self):
        """Get the detailed formatter format string."""
        return self.get("formatter_detailedFormatter", "format", 
                      "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s")
    
    def get_override_dict(self):
        """Get dictionary of important configuration values."""
        return {
            "root_level": self.get_root_logger_level(),
            "ares_level": self.get_ares_logger_level(),
            "build_level": self.get_build_logger_level()
        }
    
    def initialize(self, log_dir=None, log_filename=None):
        """Sets up logging system from config or defaults"""
        # Skip if already initialized
        if self.__class__._logging_initialized:
            return True

        # Set up log directory
        if log_dir is None:
            log_dir = USER_LOGS_DIR
        
        if isinstance(log_dir, str):
            log_dir = Path(log_dir)
            
        # Create logs directory if it doesn't exist
        log_dir.mkdir(exist_ok=True, parents=True)
        
        # Set default log directory for Log utility
        Log.set_default_log_dir(log_dir)
        
        # Use app-specific filename or default
        if not log_filename:
            if IS_FROZEN:
                # In frozen mode, use the executable's name for log file
                log_filename = f"{Path(sys.executable).stem}.log"
                
                # Import here to avoid circular imports
                try:
                    from ares.config.project_config import ProjectConfig
                    project_config = ProjectConfig()
                    product_name = project_config.get_product_name()
                    if product_name:
                        log_filename = f"{product_name}.log"
                except (ImportError, AttributeError):
                    pass
            else:
                # In development mode, use engine.log
                log_filename = "engine.log"
        
        # Full path to the log file
        log_file_path = log_dir / log_filename
        
        # Create a log redirector for capturing child process output
        build_log_path = log_dir / "build.log"
        self.__class__._subprocess_log_handler = logging.FileHandler(build_log_path)
        self.__class__._subprocess_log_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - SUBPROCESS - %(message)s", "%Y.%m.%d:%H:%M:%S")
        self.__class__._subprocess_log_handler.setFormatter(formatter)
        
        # Try to find logging.ini in multiple locations
        logging_ini_paths = [
            # Check for user config directory first if in frozen app
            Path(log_dir.parent) / "Config" / "logging.ini" if IS_FROZEN else None,
            log_dir / "logging.ini",  # Check in log directory
            LOGGING_INI,  # Default location
        ]
        
        logging_ini = None
        for ini_path in logging_ini_paths:
            if ini_path and ini_path.exists():
                logging_ini = ini_path
                break
        
        if not logging_ini:
            raise FileNotFoundError(f"Logging configuration file not found in any standard location")
        
        # Convert Windows paths to posix format to avoid escape character issues
        log_dir_str = str(log_dir).replace('\\', '/')
        log_file_str = str(log_file_path).replace('\\', '/')
        
        # Load config with interpolated log_dir and log_file
        logging.config.fileConfig(
            logging_ini,
            defaults={
                'log_dir': log_dir_str,
                'log_file': log_file_str
            },
            disable_existing_loggers=False
        )
        print(f"Logging configuration loaded from {logging_ini}")
        
        # Mark logging as initialized
        self.__class__._logging_initialized = True
        return True
    
    @classmethod
    def set_level(cls, level):
        """Updates log level for all Ares loggers"""
        Log.set_level(level)
        
        # Also update the configured loggers
        for logger_name in ["", "ares", "ares.build", "ares.project"]:
            logger = logging.getLogger(logger_name)
            logger.setLevel(level)
    
    @classmethod
    def get_subprocess_logger(cls):
        """Returns handler for capturing subprocess output"""
        return cls._subprocess_log_handler
