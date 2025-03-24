# Runtime logging hook - integrates with Ares Engine logging system in frozen applications
import sys
import logging
import traceback
from pathlib import Path

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
    
    # Use our log module directly - no fallback needed
    from ares.utils import log
    log.error(f"UNHANDLED EXCEPTION: {exc_type.__name__}: {exc_value}")
    for line in tb_text.splitlines():
        log.error(f"  {line}")
    
    # Also print to original stderr
    _original_stderr.write(f"UNHANDLED EXCEPTION: {exc_type.__name__}: {exc_value}\n")
    _original_stderr.write(tb_text)

def setup_runtime_logging():
    """Configures logging system for frozen applications"""
    global _hook_initialized
    
    if _hook_initialized:
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
        app_name = Path(sys.argv[0]).stem if sys.argv else 'app'
    
    # Import config manager and initialize configuration
    try:
        from ares.config import config_manager
        config_dir = config_manager.initialize_configuration(app_name)
        
        # Now import and initialize logging with the extracted config
        from ares.config.logging_config import initialize_logging
        
        # Use the config directory
        initialize_logging(config_dir, log_filename=f"{app_name}.log")
        
    except ImportError:
        # Simplified fallback if config_manager isn't available
        logs_dir = exe_dir
        
        # Import and initialize logging directly
        from ares.config.logging_config import initialize_logging
        initialize_logging(logs_dir, log_filename=f"{app_name}.log")
    
    # Get the log utility for application logging
    from ares.utils import log
    
    # Log startup information
    log.info(f"Starting {app_name}")
    log.info(f"Executable directory: {exe_dir}")
    log.info(f"Log file: {logs_dir / f'{app_name}.log'}")
    
    # Log PyInstaller info
    if getattr(sys, 'frozen', False):
        log.info(f"Running in PyInstaller bundle")
        log.info(f"Temporary directory: {meipass_dir}")
        
        # Check for INI file presence
        ini_path = meipass_dir / "ares" / "ini" / "logging.ini"
        if ini_path.exists():
            log.info(f"Using logging configuration from {ini_path}")
        else:
            log.info("Using default logging configuration")
    
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
    from ares.utils import log, debug_utils
    debug_utils.dump_module_search_paths(log)

# Run immediately when hook is loaded
setup_runtime_logging()
dump_module_search_paths()
