"""
Configuration module for the Ares Engine.

This module provides configuration settings and management for the engine.
"""

from __future__ import annotations

from pathlib import Path
import os

# Define standard paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_DIR = PROJECT_ROOT / "ares" / "ini"
USER_CONFIG_DIR = Path.home() / ".ares" / "config"
CONFIG_FILES_DIR = DEFAULT_CONFIG_DIR

# Create config directories if they don't exist
os.makedirs(USER_CONFIG_DIR, exist_ok=True)

# Import and create configuration objects
from .config import config, get_config
from .engine_config import EngineConfig
from .build_config import BuildConfig
from .compiler_config import CompilerConfig, compiler_config
from .project_config import ProjectConfig
from .package_config import PackageConfig
from .config_manager import initialize_configuration, get_app_config_dir

# Create global instances
engine_config = EngineConfig()
build_config = BuildConfig()
project_config = ProjectConfig()
package_config = PackageConfig()

# Flag to track initialization status
_initialized = False

def initialize() -> bool:
    """Initialize the configuration system.
    
    Returns:
        bool: True if initialization was successful
    """
    global _initialized
    
    if not _initialized:
        # Create config directories
        os.makedirs(USER_CONFIG_DIR, exist_ok=True)
        
        # Make sure all configs are loaded
        engine_config.load()
        build_config.load()
        project_config.load()
        package_config.load()
        compiler_config.load()
        
        _initialized = True
    
    return _initialized

# Auto-initialize when the module is imported
if not _initialized:
    initialize()

__all__ = [
    'config', 'get_config', 
    'engine_config', 'build_config', 'project_config', 'package_config', 'compiler_config',
    'initialize', 'initialize_configuration', 'get_app_config_dir',
    'PROJECT_ROOT', 'DEFAULT_CONFIG_DIR', 'USER_CONFIG_DIR', 'CONFIG_FILES_DIR'
]
