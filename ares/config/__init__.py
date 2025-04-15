"""
Configuration module for the Ares Engine.

This module provides configuration settings and management for the engine.
"""

from __future__ import annotations

from pathlib import Path
import os

# Define standard paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
# TODO this should use config.py
DEFAULT_CONFIG_DIR = PROJECT_ROOT / "ares" / "config" / "ini"

# Import user paths function from paths module to avoid circular imports
from ares.utils.paths import get_user_config_dir
CONFIG_FILES_DIR = DEFAULT_CONFIG_DIR

# Create config directories lazily - don't call at import time
def ensure_config_dir():
    """Ensure the user config directory exists.""" 
    user_config_dir = get_user_config_dir()
    os.makedirs(user_config_dir, exist_ok=True)
    return user_config_dir

# Get user config dir only when needed
USER_CONFIG_DIR = None  # Will be set when needed

# Rest of imports
from .config import config, get_config
from .config_manager import ConfigManager
from .engine_config import EngineConfig
from .build_config import BuildConfig
from .compiler_config import CompilerConfig
from .project_config import ProjectConfig
from .package_config import PackageConfig

from .assets_config import AssetsConfig
from .logging_config import LoggingConfig

# Create global instances
engine_config = EngineConfig()
build_config = BuildConfig()
project_config = ProjectConfig()
package_config = PackageConfig()
assets_config = AssetsConfig()
compiler_config = CompilerConfig()
logging_config = LoggingConfig()

# Flag to track initialization status
_initialized = False

# Global configs dictionary used for sharing with subprocesses
_global_configs = None
CONFIGS = None # Alias as CONFIGS for consistency with usage in setup.py

def initialize() -> bool:
    """Initialize the configuration system."""
    global _initialized, USER_CONFIG_DIR
    
    if not _initialized:
        # Lazily create config directories now
        USER_CONFIG_DIR = ensure_config_dir()
        
        # Make sure all configs are loaded
        engine_config.load()
        build_config.load()
        project_config.load()
        package_config.load()
        compiler_config.load()
        assets_config.load()
        logging_config.load()
        
        _initialized = True
    
    return _initialized

def set_global_configs(configs):
    """Store the fully loaded configs for use across modules."""
    global _global_configs, CONFIGS
    _global_configs = configs
    CONFIGS = configs
    
def get_global_configs():
    """Get the globally stored configs if available.
    
    If configs aren't available yet, automatically load them from PROJECT_ROOT.
    
    Returns:
        dict: Dictionary of configuration objects by ConfigType
    """
    global _global_configs, CONFIGS
    
    if _global_configs is None:
        # Import here to avoid circular imports
        from .config_manager import ConfigManager
        _global_configs = ConfigManager.load_all_configs(PROJECT_ROOT)
        CONFIGS = _global_configs
        
    return _global_configs

__all__ = [
    'config', 'get_config', 
    'engine_config', 'build_config', 'project_config', 'package_config', 
    'compiler_config', 'assets_config', 'logging_config',
    'initialize', 'ConfigManager',
    'PROJECT_ROOT', 'DEFAULT_CONFIG_DIR', 'USER_CONFIG_DIR', 'CONFIG_FILES_DIR',
    'set_global_configs', 'get_global_configs', 'CONFIGS'
]
