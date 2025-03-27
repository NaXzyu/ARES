"""Central logging facility for Ares Engine with unified interface."""

import functools
import inspect
import logging
import logging.config
import sys
from pathlib import Path
from typing import Any, Callable, Dict, Optional, TypeVar, Union

# Type variable for decorator return types
T = TypeVar("T")

# Default log format
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_DATE_FORMAT = "%Y.%m.%d:%H:%M:%S"

class Log:
    """Unified logging with context tracking and level management"""
    
    # Class variables
    _instance = None
    _level = logging.INFO
    _file_handlers: Dict[str, logging.FileHandler] = {}
    _default_log_dir = None
    
    # Logging levels for easier access
    CRITICAL = logging.CRITICAL
    ERROR = logging.ERROR
    WARNING = logging.WARNING
    INFO = logging.INFO
    DEBUG = logging.DEBUG
    NOTSET = logging.NOTSET
    
    @staticmethod
    def _get_name() -> str:
        """Identifies calling context for log attribution"""
        frame = inspect.stack()[2]
        module = inspect.getmodule(frame[0])
        module_name = module.__name__ if module else "ares"
        class_name = frame[3]
        return f"{module_name}.{class_name}"
    
    @staticmethod
    def _setup() -> None:
        """Initializes basic logging configuration"""
        logging.basicConfig(
            level=Log._level,
            format=DEFAULT_LOG_FORMAT,
            datefmt=DEFAULT_DATE_FORMAT,
            handlers=[logging.StreamHandler(sys.stdout)]
        )
        Log._instance = logging.getLogger("ares")
        Log._instance.setLevel(Log._level)
    
    @staticmethod
    def get() -> logging.Logger:
        """Get or create the singleton logger instance."""
        if Log._instance is None:
            Log._setup()
        return Log._instance
    
    @staticmethod
    def get_handler() -> logging.StreamHandler:
        """Get a stdout stream handler for logging configuration."""
        return logging.StreamHandler(sys.stdout)
    
    @staticmethod
    def set_default_log_dir(log_dir: Union[str, Path]) -> None:
        """Set the default directory for log files."""
        if isinstance(log_dir, str):
            log_dir = Path(log_dir)
        
        log_dir.mkdir(exist_ok=True, parents=True)
        Log._default_log_dir = log_dir
    
    @staticmethod
    def add_file_handler(logger_name: str = "ares", 
                         filename: Optional[str] = None,
                         log_dir: Optional[Union[str, Path]] = None) -> logging.FileHandler:
        """Add a file handler to the specified logger."""
        # Use default log directory if none specified
        if log_dir is None:
            if Log._default_log_dir is None:
                # Default to project_root/logs
                project_root = Path(__file__).resolve().parents[2]
                log_dir = project_root / "logs"
            else:
                log_dir = Log._default_log_dir
        
        # Create log directory if it doesn't exist
        if isinstance(log_dir, str):
            log_dir = Path(log_dir)
        log_dir.mkdir(exist_ok=True, parents=True)
        
        # Set default filename if not provided
        if filename is None:
            filename = f"{logger_name}.log"
            
        # Create full path
        log_path = log_dir / filename
        
        # Check if handler already exists for this path
        handler_key = f"{logger_name}:{str(log_path)}"
        if handler_key in Log._file_handlers:
            return Log._file_handlers[handler_key]
        
        # Create and configure file handler
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(logging.Formatter(DEFAULT_LOG_FORMAT))
        file_handler.setLevel(Log._level)
        
        # Add handler to the specified logger
        logger = logging.getLogger(logger_name)
        logger.addHandler(file_handler)
        
        # Store handler for future reference
        Log._file_handlers[handler_key] = file_handler
        
        return file_handler
    
    @staticmethod
    def get_logger(name: str, with_file: bool = False, 
                  filename: Optional[str] = None,
                  log_dir: Optional[Union[str, Path]] = None) -> logging.Logger:
        """Get a named logger with optional file handler."""
        logger = logging.getLogger(name)
        logger.setLevel(Log._level)
        
        if with_file:
            if not filename:
                filename = f"{name}.log"
            Log.add_file_handler(name, filename, log_dir)
            
        return logger
    
    @staticmethod
    def set_level(level: int) -> None:
        """Set the global logging level for all loggers."""
        Log._level = level
        if Log._instance:
            Log._instance.setLevel(Log._level)
            logging.getLogger("ares").setLevel(Log._level)
            
        # Update file handler levels
        for handler in Log._file_handlers.values():
            handler.setLevel(level)
    
    @staticmethod
    def level(level: int) -> Callable[[Callable[..., T]], Callable[..., T]]:
        """Decorator to temporarily change log level during method execution."""
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @functools.wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> T:
                prev_level = Log._level
                Log.set_level(level)
                try:
                    return func(*args, kwargs)
                finally:
                    Log.set_level(prev_level)
            return wrapper
        return decorator
    
    # Simplified logging methods
    @staticmethod
    def debug(message: str) -> None:
        """Log a debug level message with calling context."""
        logger = Log.get()
        logger.name = Log._get_name()
        logger.debug(message)
    
    @staticmethod
    def info(message: str) -> None:
        """Log an info level message with calling context."""
        logger = Log.get()
        logger.name = Log._get_name()
        logger.info(message)
    
    @staticmethod
    def warn(message: str) -> None:
        """Log a warning level message with calling context."""
        logger = Log.get()
        logger.name = Log._get_name()
        logger.warning(message)
    
    @staticmethod
    def error(message: str, exc_info: Optional[bool] = None) -> None:
        """Log an error level message with call context and optional trace."""
        logger = Log.get()
        logger.name = Log._get_name()
        logger.error(message, exc_info=exc_info)

# For simpler importing, create log functions at module level
debug = Log.debug
info = Log.info
warn = Log.warn
error = Log.error
set_level = Log.set_level
get_logger = Log.get_logger
add_file_handler = Log.add_file_handler
set_default_log_dir = Log.set_default_log_dir
