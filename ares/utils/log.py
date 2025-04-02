"""Central logging facility for Ares Engine with unified interface."""

import datetime
import inspect
import logging
import logging.config
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, TypeVar, Union

from ares.utils.const import (
    DEFAULT_DATE_FORMAT,
    DEFAULT_LOG_FORMAT,
    FILE_ENCODING,
)

# Type variable for decorator return types
T = TypeVar("T")

class ContextAwareLogger:
    """A logger wrapper that automatically determines the calling module."""
    
    def __init__(self, base_logger: logging.Logger):
        """Initialize with a base logger"""
        self._base_logger = base_logger
        self._level = logging.INFO
        self._file_handlers: Dict[str, logging.FileHandler] = {}
        self._default_log_dir = None
    
    def _get_caller_info(self) -> str:
        """Determine the calling module and function name for context-aware logging."""
        # Get the call stack
        stack = inspect.stack()
        # Skip this function and the logging function that called it
        for frame in stack[2:]:
            module = inspect.getmodule(frame[0])
            if module and module.__name__ != __name__:
                function = frame.function
                return f"{module.__name__}.{function}"
        return "ares.unknown"
    
    def set_default_log_dir(self, log_dir: Union[str, Path]) -> None:
        """Set the default directory for log files."""
        if isinstance(log_dir, str):
            log_dir = Path(log_dir)
        
        log_dir.mkdir(exist_ok=True, parents=True)
        self._default_log_dir = log_dir
    
    def add_file_handler(self, logger_name: str = "ares", 
                         filename: Optional[str] = None,
                         log_dir: Optional[Union[str, Path]] = None) -> logging.FileHandler:
        """Add a file handler to the specified logger."""
        # Use default log directory if none specified
        if log_dir is None:
            if self._default_log_dir is None:
                # Default to project_root/logs
                project_root = Path(__file__).resolve().parents[2]
                log_dir = project_root / "logs"
            else:
                log_dir = self._default_log_dir
        
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
        if handler_key in self._file_handlers:
            return self._file_handlers[handler_key]
        
        # Create and configure file handler
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(logging.Formatter(DEFAULT_LOG_FORMAT))
        
        # Add handler to the specified logger
        logger = logging.getLogger(logger_name)
        logger.addHandler(file_handler)
        
        # Store handler for future reference
        self._file_handlers[handler_key] = file_handler
        
        return file_handler
    
    def get_logger(self, name: str, with_file: bool = False, 
                   filename: Optional[str] = None,
                   log_dir: Optional[Union[str, Path]] = None) -> logging.Logger:
        """Get a named logger with optional file handler."""
        logger = logging.getLogger(name)
        
        if with_file:
            if not filename:
                filename = f"{name}.log"
            self.add_file_handler(name, filename, log_dir)
            
        return logger
    
    def set_level(self, level: int) -> None:
        """Set the global logging level."""
        self._level = level
        logging.getLogger().setLevel(level)
        
    def debug(self, msg: Any, *args, **kwargs) -> None:
        """Log a debug message with auto-detected module context."""
        caller = self._get_caller_info()
        logger = logging.getLogger(caller)
        logger.debug(msg, *args, **kwargs)
    
    def info(self, msg: Any, *args, **kwargs) -> None:
        """Log an info message with auto-detected module context."""
        caller = self._get_caller_info()
        logger = logging.getLogger(caller)
        logger.info(msg, *args, **kwargs)
    
    def warn(self, msg: Any, *args, **kwargs) -> None:
        """Log a warning message with auto-detected module context."""
        caller = self._get_caller_info()
        logger = logging.getLogger(caller)
        logger.warning(msg, *args, **kwargs)
    
    def warning(self, msg: Any, *args, **kwargs) -> None:
        """Alias for warn() - log a warning message with auto-detected module context."""
        self.warn(msg, *args, **kwargs)
    
    def error(self, msg: Any, *args, **kwargs) -> None:
        """Log an error message with auto-detected module context."""
        caller = self._get_caller_info()
        logger = logging.getLogger(caller)
        logger.error(msg, *args, **kwargs)
    
    def critical(self, msg: Any, *args, **kwargs) -> None:
        """Log a critical message with auto-detected module context."""
        caller = self._get_caller_info()
        logger = logging.getLogger(caller)
        logger.critical(msg, *args, **kwargs)
    
    def exception(self, msg: Any, *args, exc_info=True, **kwargs) -> None:
        """Log an exception message with auto-detected module context."""
        caller = self._get_caller_info()
        logger = logging.getLogger(caller)
        logger.exception(msg, exc_info=exc_info, **kwargs)

    def log_to_file(self, file_path, message, add_timestamp=True, add_newlines=True):
        """Write a message directly to a log file with optional timestamp.
        
        Args:
            file_path: Path to log file
            message: Message to write
            add_timestamp: Whether to add timestamp (default: True)
            add_newlines: Whether to add newlines before message (default: True)
            
        Returns:
            bool: True if successful, False if there was an error
        """
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, "a", encoding=FILE_ENCODING) as log_file:
                if add_newlines:
                    log_file.write("\n\n")
                    
                if add_timestamp:
                    timestamp = datetime.datetime.now().strftime(DEFAULT_DATE_FORMAT)
                    log_file.write(f"--- {message} at {timestamp} ---\n")
                else:
                    log_file.write(f"{message}\n")
                    
            return True
        except Exception as e:
            self.error(f"Error writing to log file {file_path}: {e}")
            return False

    def print_dir_tree(self, directory, max_depth=3, current_depth=0, log_level="error"):
        """Print a directory tree structure for debugging.
        
        Args:
            directory: Directory to print
            max_depth: Maximum depth to explore
            current_depth: Current recursion depth (used internally)
            log_level: Log level to use ("error", "info", "debug", "warn")
        """
        log_func = getattr(self, log_level, self.error)
        
        if current_depth > max_depth:
            log_func(f"{' ' * current_depth * 2}...")
            return
        
        try:
            log_func(f"{' ' * current_depth * 2}{Path(directory).name}/")
            if Path(directory).is_dir():
                for item in Path(directory).iterdir():
                    if item.is_dir():
                        self.print_dir_tree(item, max_depth, current_depth + 1, log_level)
                    else:
                        log_func(f"{' ' * (current_depth + 1) * 2}{item.name}")
        except Exception as e:
            log_func(f"{' ' * current_depth * 2}Error: {e}")

    def log_collection(self, items, summary_format=None, item_format=None, 
                       log_level="info", key_attr=None):
        """Log a collection of items with summary and individual entries.
        
        Args:
            items: Collection of items to log
            summary_format: Format string for summary (uses len(items))
                            Default: "Found {count} items"
            item_format: Format string for each item. For item_format:
                         - If items are tuples/lists, use {0}, {1}, etc.
                         - If key_attr is provided, attribute values will be available as {attr_name}
                         Default: "  - {item}"
            log_level: Log level to use (info, debug, warn, error)
            key_attr: If items have attributes, name of attribute to use in logging
        """
        # Get the appropriate log function
        log_func = getattr(self, log_level, self.info)
        
        # Create default formats if not provided
        if summary_format is None:
            summary_format = "Found {count} items"
        if item_format is None:
            item_format = "  - {item}"
            
        # Log summary if items exist
        item_count = len(items)
        if item_count > 0:
            log_func(summary_format.format(count=item_count))
            
            # Log each item
            for item in items:
                # Handle different item types
                if isinstance(item, (tuple, list)):
                    # For tuples/lists, use positional formatting
                    formatted_str = item_format.format(*item)
                elif key_attr and hasattr(item, key_attr):
                    # For objects with key attribute
                    attrs = {key_attr: getattr(item, key_attr)}
                    formatted_str = item_format.format(**attrs)
                else:
                    # For simple items
                    formatted_str = item_format.format(item=item)
                    
                log_func(formatted_str)
        else:
            log_func(f"No items found")

    def log_module_files(self, found_modules, log_level="info"):
        """Log information about module files found during compilation.
        
        Args:
            found_modules: Dictionary mapping directory paths to info about found files
            log_level: Log level to use (default: "info")
        """
        log_func = getattr(self, log_level, self.info)
        
        for dir_path, info in found_modules.items():
            log_func(f"Found {len(info['files'])} compiled modules in {dir_path}")
            for file_name in info['files']:
                log_func(f"  {file_name}")

    def log_collection_to_file(self, file_path, items, item_format="  - {0} ({1})\n"):
        """Write a collection of items to a log file with formatting.
        
        Args:
            file_path: Path to the log file
            items: Collection of items to log (typically tuples or lists)
            item_format: Format string for each item with placeholders for tuple/list elements
                Default: "  - {0} ({1})\n"
                
        Returns:
            bool: True if successful, False if there was an error
        """
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, "a", encoding=FILE_ENCODING) as log_file:
                for item in items:
                    if isinstance(item, (tuple, list)):
                        # For tuples/lists, use positional formatting
                        log_file.write(item_format.format(*item))
                    else:
                        # For simple items
                        log_file.write(item_format.format(item))
                        
            return True
        except Exception as e:
            self.error(f"Error writing collection to log file {file_path}: {e}")
            return False

    def log_process_output(self, process, log_file_path, header=None, patterns=None):
        """Log process output to a file and console with intelligent filtering.
        
        Args:
            process: A subprocess.Popen object with stdout available for reading
            log_file_path: Path to the log file to append output
            header: Optional header to write at the top of the log section
            patterns: Dictionary mapping regex patterns to log functions or formats
                     Default patterns will be used if None provided
                     
        Returns:
            bool: True if process completed successfully, False otherwise
        """
        try:
            with open(log_file_path, "a", encoding=FILE_ENCODING) as log_file:
                # Write the header if provided
                if header:
                    log_file.write(f"\n--- {header} ---\n")
                
                # Use default patterns if none provided
                if patterns is None:
                    patterns = {
                        "Processing (.+)": lambda m: self.info(f"Processing {m.group(1)}"),
                        "Building wheel.*": lambda m: self.info(f"Building wheel: {m.group(0)}"),
                        "Created wheel for ares.*": lambda m: self.info(f"Created wheel: {m.group(0).split('Created wheel for ares: ')[1]}"),
                        "Building wheel.*started": lambda _: self.info("Building wheel package started"),
                        "Building wheel.*finished": lambda _: self.info("Building wheel package finished"),
                        "error:": lambda m: self.error(m.group(0)),
                        "warning:": lambda m: self.warn(m.group(0))
                    }
                
                # Process each line
                import re
                for line in process.stdout:
                    # Always write the raw line to the log file
                    log_file.write(line)
                    
                    # Process the line for console output based on patterns
                    line = line.strip()
                    matched = False
                    
                    for pattern, handler in patterns.items():
                        match = re.search(pattern, line, re.IGNORECASE)
                        if match:
                            handler(match)
                            matched = True
                            break
                
            # Wait for process to complete and return the status
            ret_code = process.wait()
            return ret_code == 0
            
        except Exception as e:
            self.error(f"Error logging process output: {e}")
            return False

    def track_process_output(self, process, log_file_path: Union[str, Path], 
                            error_keywords: List[str] = None,
                            max_error_lines: int = 10,
                            print_errors: bool = True) -> List[str]:
        """Track process output in real-time, capturing important error messages.
        
        Args:
            process: A subprocess.Popen object with stdout available for reading
            log_file_path: Path to the log file to append output
            error_keywords: List of keywords that indicate important messages to track
                           Default: ['error:', 'exception:', 'traceback', 'fail', 'warning:', 'nameerror']
            max_error_lines: Maximum number of error lines to track (default: 10)
            print_errors: Whether to print error lines to console (default: True)
            
        Returns:
            List[str]: The last important error lines collected during processing
        """
        if error_keywords is None:
            error_keywords = ['error:', 'exception:', 'traceback', 'fail', 'warning:', 'nameerror']
            
        # Ensure log directory exists
        if isinstance(log_file_path, str):
            log_file_path = Path(log_file_path)
        os.makedirs(log_file_path.parent, exist_ok=True)
        
        last_error_lines = []
        
        try:
            with open(log_file_path, 'a', encoding=FILE_ENCODING) as log_file:
                for line in process.stdout:
                    # Store important lines to track errors
                    if any(keyword in line.lower() for keyword in error_keywords):
                        clean_line = line.strip()
                        last_error_lines.append(clean_line)
                        if len(last_error_lines) > max_error_lines:
                            last_error_lines.pop(0)
                        
                        # Print important lines to console for better visibility
                        if print_errors:
                            print(clean_line)
                    
                    # Write all output to build log
                    log_file.write(line)
            
            return last_error_lines
            
        except Exception as e:
            self.error(f"Error tracking process output: {e}")
            return last_error_lines

    def log_error_output(self, error, log_file_path=None, log_level="error"):
        """Log error output to both console and file.
        
        Args:
            error: Exception object or error message string
            log_file_path: Optional path to log file; if None, no file logging is done
            log_level: Log level to use (default: "error")
            
        Returns:
            bool: True if successfully logged to file (or no file logging requested), 
                  False if file logging failed
        """
        # Get the appropriate log function
        log_func = getattr(self, log_level, self.error)
        
        # Extract stderr if it's an exception with stderr attribute
        stderr_output = None
        if hasattr(error, 'stderr') and error.stderr:
            stderr_output = error.stderr
            error_msg = f"Error output: {stderr_output}"
        else:
            error_msg = f"Error: {error}"
        
        # Log to console
        log_func(error_msg)
        
        # Log to file if path provided
        if log_file_path and stderr_output:
            return self.log_to_file(log_file_path, f"Error output: {stderr_output}", add_timestamp=False)
        
        return True

    def display_error_details(self, error_lines, header="Error details:", 
                             max_lines=5, indent="  ", log_level="error"):
        """Display the last few error lines with a header for better visibility.
        
        Args:
            error_lines: List of error message strings
            header: Header message to show before error lines (default: "Error details:")
            max_lines: Maximum number of lines to show (default: 5)
            indent: String to use for indentation (default: two spaces)
            log_level: Log level to use (default: "error")
            
        Returns:
            None
        """
        # Get the appropriate log function
        log_func = getattr(self, log_level, self.error)
        
        if not error_lines:
            return
            
        # Show header
        log_func(f"\n{header}")
        
        # Show the last few lines, respecting max_lines
        lines_to_show = error_lines[-max_lines:] if len(error_lines) > max_lines else error_lines
        
        for line in lines_to_show:
            log_func(f"{indent}{line}")

class Logger:
    """Singleton logger manager for the Ares Engine."""
    
    # Class variable to track initialization state
    _initialized = False
    
    # Global context-aware logger instance
    _context_logger = None
    
    # Shared handler for all loggers
    _handler = None
    
    @classmethod
    def initialize(cls) -> None:
        """Initialize logging system if not already initialized."""
        if cls._initialized:
            return
            
        # Set flag first to prevent recursion
        cls._initialized = True
        
        # Configure root logger to output to stdout
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)

        # Clear any existing handlers to avoid duplication
        if root_logger.handlers:
            root_logger.handlers.clear()

        # Add a single handler with proper formatting
        cls._handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(DEFAULT_LOG_FORMAT, datefmt=DEFAULT_DATE_FORMAT)
        cls._handler.setFormatter(formatter)
        root_logger.addHandler(cls._handler)

        # Create and configure the main logger
        main_logger = logging.getLogger('ares')
        main_logger.setLevel(logging.INFO)
        main_logger.propagate = False  # Prevent propagation to avoid duplicate logs

        # Add the same handler to our specific logger
        main_logger.handlers.clear()  # Clear any existing handlers
        main_logger.addHandler(cls._handler)
        
        # Create the context-aware logger that will be exported as 'log'
        cls._context_logger = ContextAwareLogger(main_logger)
        
        # Redirect common external loggers
        cls.redirect_external_loggers('cython', 'setuptools', 'pip', 'wheel')
    
    @classmethod
    def redirect_external_loggers(cls, *module_names: str) -> None:
        """
        Redirect logs from external libraries to our central logging system.
        
        Args:
            *module_names: Names of modules whose logs should be captured
        """
        # Don't call initialize again if we're already in initialize
        if not cls._initialized:
            cls.initialize()
            return
        
        for module_name in module_names:
            ext_logger = logging.getLogger(module_name)
            ext_logger.handlers.clear()
            ext_logger.propagate = False
            if cls._handler:
                ext_logger.addHandler(cls._handler)


# Initialize the logger singleton
Logger.initialize()

# Export a context-aware log object that automatically determines the calling module
log = Logger._context_logger

# Export the log instance for direct import
__all__ = ['log']
