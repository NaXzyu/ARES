"""Configuration initialization hook - sets up engine configuration system in frozen applications"""

import sys
from pathlib import Path

from ares.utils.const import (
    DEFAULT_ENGINE_NAME,
    ERROR_INVALID_CONFIGURATION
)

# Track if we're initialized
_configs_initialized = False

def init_configs():
    """Initialize the configuration system for frozen applications."""
    global _configs_initialized
    
    if _configs_initialized:
        return
    
    if getattr(sys, 'frozen', False):
        # We're running in a PyInstaller bundle
        app_name = Path(sys.executable).stem
    else:
        # We're running in a normal Python environment
        app_name = Path(sys.argv[0]).stem if sys.argv else DEFAULT_ENGINE_NAME
    
    # Get paths from centralized Paths utility
    from ares.utils.paths import Paths
    app_dirs = Paths.create_app_paths(app_name)
    config_dir = app_dirs["CONFIG_DIR"]
    
    print(f"Initializing configuration system for {app_name}")
    
    try:
        # Initialize the configuration system
        from ares.config.config_manager import ConfigManager
        
        # Extract all embedded config files if needed
        if getattr(sys, 'frozen', False):
            ConfigManager.extract_embedded_configs(app_name, config_dir=config_dir)
        
        # Get the configs dictionary - this will automatically initialize configs if needed
        from ares.config import get_global_configs
        CONFIGS = get_global_configs()
        
        if CONFIGS:
            print(f"Configuration system initialized successfully")
            
            # Log initialization with our logging system
            try:
                from ares.utils import log
                log.info(f"Configuration system initialized for {app_name}")
                log.info(f"Configuration directory: {config_dir}")
            except ImportError:
                # Logging may not be ready yet
                pass
        else:
            print("Warning: Configuration initialization may have failed")
            
        _configs_initialized = True
        
    except Exception as e:
        import traceback
        print(f"Error initializing configuration system: {e}")
        traceback.print_exc()
        sys.exit(ERROR_INVALID_CONFIGURATION)

# Run immediately when hook is loaded
init_configs()
