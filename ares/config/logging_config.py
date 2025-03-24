"""Logging configuration for Ares Engine."""

import sys
import logging
import logging.config
from pathlib import Path

from ares.utils.log import Log

# Get project root and logs directory
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LOG_DIR = PROJECT_ROOT / "logs"
INI_DIR = PROJECT_ROOT / "ares" / "ini"
LOGGING_INI = INI_DIR / "logging.ini"

# Track initialization status
_logging_initialized = False
subprocess_log_handler = None

def initialize_logging(log_dir=None, log_filename=None):
    """Sets up logging system from config or defaults"""
    global _logging_initialized, subprocess_log_handler
    
    # Skip if already initialized
    if _logging_initialized:
        return

    # Set up log directory
    if log_dir is None:
        log_dir = DEFAULT_LOG_DIR
    
    if isinstance(log_dir, str):
        log_dir = Path(log_dir)
        
    # Create logs directory if it doesn't exist
    log_dir.mkdir(exist_ok=True, parents=True)
    
    # Set default log directory for Log utility
    Log.set_default_log_dir(log_dir)
    
    # Use app-specific filename or default
    if not log_filename:
        # Try to get executable name for better log identification
        if getattr(sys, 'frozen', False):
            log_filename = f"{Path(sys.executable).stem}.log"
        else:
            # Changed default from ares.log to engine.log
            log_filename = "engine.log"
    
    # Full path to the log file
    log_file_path = log_dir / log_filename
    
    # Create a log redirector for capturing child process output
    build_log_path = log_dir / "build.log"
    subprocess_log_handler = logging.FileHandler(build_log_path)
    subprocess_log_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - SUBPROCESS - %(message)s", "%Y.%m.%d:%H:%M:%S")
    subprocess_log_handler.setFormatter(formatter)
    
    # Try to find logging.ini in multiple locations
    logging_ini_paths = [
        # Check for user config directory first if in frozen app
        Path(log_dir.parent) / "logging.ini" if getattr(sys, 'frozen', False) else None,
        log_dir / "logging.ini",  # Check in log directory
        LOGGING_INI,  # Default location
    ]
    
    logging_ini = None
    for ini_path in logging_ini_paths:
        if ini_path and ini_path.exists():
            logging_ini = ini_path
            break
    
    if logging_ini:
        try:
            # Convert Windows paths to posix format to avoid escape character issues
            log_dir_str = str(log_dir).replace('\\', '/')
            log_file_str = str(log_file_path).replace('\\', '/')
            
            # Verify the INI file contains all required sections
            has_valid_format = verify_ini_file(logging_ini)
            if not has_valid_format:
                print(f"Warning: logging.ini has missing sections. Using default configuration.")
                configure_basic_logging(log_dir, log_filename)
                return
            
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
        except Exception as e:
            print(f"Error loading logging configuration: {e}")
            # Fall back to basic config
            configure_basic_logging(log_dir, log_filename)
    else:
        print(f"Logging INI file not found. Using default configuration.")
        configure_basic_logging(log_dir, log_filename)
    
    # Mark logging as initialized
    _logging_initialized = True

def verify_ini_file(ini_path):
    """Verify that the INI file contains all required sections."""
    import configparser
    config = configparser.ConfigParser()
    try:
        config.read(ini_path)
        required_sections = ['loggers', 'handlers', 'formatters']
        for section in required_sections:
            if not config.has_section(section):
                print(f"Missing required section '{section}' in {ini_path}")
                return False
        return True
    except Exception as e:
        print(f"Error reading INI file {ini_path}: {e}")
        return False

def configure_basic_logging(log_dir, log_filename=None):
    """Sets up minimal logging when config fails"""
    log_file = log_dir / (log_filename or "engine.log")  # Changed from ares.log to engine.log
    
    # Clear any existing handlers from the root logger
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create a basic file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    
    # Create a console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Configure ares logger
    ares_logger = logging.getLogger("ares")
    ares_logger.setLevel(logging.INFO)
    
    print(f"Basic logging configuration applied. Log file: {log_file}")

def set_level(level):
    """Updates log level for all Ares loggers"""
    Log.set_level(level)
    
    # Also update the configured loggers
    for logger_name in ["", "ares", "ares.build", "ares.project"]:
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)

# Subprocess output redirection
def get_subprocess_logger():
    """Returns handler for capturing subprocess output"""
    return subprocess_log_handler
