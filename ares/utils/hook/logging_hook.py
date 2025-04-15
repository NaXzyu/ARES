"""Runtime logging hook - integrates with Ares Engine logging system in frozen applications"""

import sys
import logging
import traceback
from pathlib import Path

from ares.utils.build.build_utils import BuildUtils
from ares.utils.const import (
    DEFAULT_LOG_FORMAT,
    DEFAULT_DATE_FORMAT,
    ERROR_RUNTIME
)

# Store original stdout/stderr for fallback
_original_stdout = sys.stdout
_original_stderr = sys.stderr

# Track if we're initialized
_hook_initialized = False

class LoggerWriter:
    '''Redirects stdout/stderr to logger'''
    def __init__(self, logger, level):
        self.logger = logger
        self.level = level
        self.buffer = ""
        
    def write(self, message):
        # Write to original stdout/stderr
        if self.level == logging.ERROR:
            _original_stderr.write(message)
        else:
            _original_stdout.write(message)
        
        # Also log the message (only if it contains something)
        message = message.strip()
        if message:
            # Look for warnings and errors and upgrade their log level
            lower_message = message.lower()
            if any(keyword in lower_message for keyword in ['error:', 'exception:', 'failed']):
                self.logger.error(message)
            elif any(keyword in lower_message for keyword in ['warning:', 'warn']):
                self.logger.warning(message)
            # Avoid recursive logging loops by checking for certain patterns
            elif self.level == logging.ERROR and "- root - ERROR -" in message:
                return
            else:
                self.logger.log(self.level, message)
            
    def flush(self):
        # Need to implement flush for file compatibility
        if self.level == logging.ERROR:
            _original_stderr.flush()
        else:
            _original_stdout.flush()

def handle_exception(exc_type, exc_value, exc_traceback):
    """Records unhandled exceptions to log file"""
    if issubclass(exc_type, KeyboardInterrupt):
        # Don't log keyboard interrupt
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    # Get the traceback as a string
    tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
    tb_text = ''.join(tb_lines)
    
    # Use our log module directly
    from ares.utils import log
    log.error(f"UNHANDLED EXCEPTION: {exc_type.__name__}: {exc_value}")
    for line in tb_text.splitlines():
        log.error(f"  {line}")
    
    # Also print to original stderr
    _original_stderr.write(f"UNHANDLED EXCEPTION: {exc_type.__name__}: {exc_value}\n")
    _original_stderr.write(tb_text)
    
    # For critical errors that aren't keyboard interrupts, exit with error code
    if not issubclass(exc_type, (KeyboardInterrupt, SystemExit)):
        sys.exit(ERROR_RUNTIME)

def setup_runtime_logging():
    """Configures logging system for frozen applications"""
    global _hook_initialized
    
    if (_hook_initialized):
        return
    
    # Set up consistent paths
    if getattr(sys, 'frozen', False):
        # We're running in a PyInstaller bundle
        exe_dir = Path(sys.executable).parent
        meipass_dir = Path(sys._MEIPASS)
        app_name = Path(sys.executable).stem
    else:
        # We're running in a normal Python environment
        exe_dir = Path(__file__).parent
        meipass_dir = None
        
        # Use the BuildUtils class for consistent app name resolution
        from ares.utils.build.build_utils import BuildUtils
        app_name = BuildUtils.get_app_name()
    
    # Get paths from centralized Paths utility
    from ares.utils.paths import Paths
    
    # Create app directories structure with the consistent app_name
    app_dirs = Paths.create_app_paths(app_name)
    logs_dir = app_dirs["LOGS_DIR"]
    config_dir = app_dirs["CONFIG_DIR"]
    
    print(f"App name: {app_name}")
    print(f"Config directory: {config_dir}")
    print(f"Logs directory: {logs_dir}")
    
    # Configure basic logging as a starting point
    log_file = logs_dir / f"{app_name}.log"
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format=DEFAULT_LOG_FORMAT,
        datefmt=DEFAULT_DATE_FORMAT,
        filemode='a'
    )
    print(f"Basic logging initialized to {log_file}")
    
    # Initialize logging without try-except - let errors propagate naturally
    # Use the global CONFIGS dictionary to access logging config
    from ares.config import CONFIGS
    from ares.config.config_types import ConfigType
    
    # Initialize logging using the already configured logging object
    if ConfigType.LOGGING in CONFIGS and CONFIGS[ConfigType.LOGGING]:
        CONFIGS[ConfigType.LOGGING].initialize(logs_dir, log_filename=f"{app_name}.log")
        from ares.utils import log
        log.info(f"Advanced logging configuration initialized for {app_name}")
    else:
        raise RuntimeError("Logging configuration not available in CONFIGS")
    
    # Get the log utility for application logging - no try-except
    from ares.utils import log
    
    # Log startup information
    log.info(f"Starting {app_name}")
    log.info(f"Executable directory: {exe_dir}")
    log.info(f"Configuration directory: {config_dir}")
    log.info(f"Log directory: {logs_dir}")
    
    # Log PyInstaller info
    if getattr(sys, 'frozen', False):
        log.info(f"Running in PyInstaller bundle")
        log.info(f"Temporary directory: {meipass_dir}")
    
    # Set up exception hook
    sys.excepthook = handle_exception
    
    # Redirect stdout and stderr through our logger
    sys.stdout = LoggerWriter(logging.getLogger(), logging.INFO)
    sys.stderr = LoggerWriter(logging.getLogger(), logging.ERROR)
    
    _hook_initialized = True

def dump_module_search_paths():
    """Logs Python module search paths to help debugging import issues"""
    if not getattr(sys, 'frozen', False):
        return
        
    # Use our debug_utils module directly - no fallback needed
    from ares.utils import log
    from ares.utils.debug import utils
    utils.dump_module_paths(log)

# Run immediately when hook is loaded
setup_runtime_logging()
dump_module_search_paths()
