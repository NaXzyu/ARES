"""PyInstaller hook for Ares Engine."""

import os
import sys
from pathlib import Path

from ares.utils.const import (
    ERROR_MISSING_DEPENDENCY,
    PYD_EXTENSION,
    SO_EXTENSION,
    PYTHON_EXT
)

def get_ares_path():
    """Get the path to the ares package."""
    try:
        import ares
        return Path(ares.__file__).parent
    except ImportError as e:
        print(f"Error: Could not import ares package: {e}")
        sys.exit(ERROR_MISSING_DEPENDENCY)

def collect_ares_files():
    """Collect all Ares Engine files."""
    datas = []
    binaries = []
    
    # Get the ares package path
    ares_path = get_ares_path()
    
    # Walk through the package
    for root, _, files in os.walk(ares_path):
        # Skip __pycache__ directories
        if "__pycache__" in root:
            continue
            
        for file in files:
            # Skip __pycache__ files and .pyc files
            if "__pycache__" in file or file.endswith('.pyc'):
                continue
                
            src_path = os.path.join(root, file)
            dest_dir = os.path.relpath(root, ares_path.parent)
            
            if file.endswith((PYD_EXTENSION, SO_EXTENSION)):
                binaries.append((src_path, dest_dir))
            elif file.endswith((PYTHON_EXT, '.ini')):
                datas.append((src_path, dest_dir))
    
    return datas, binaries

# Tell PyInstaller about our data files
datas, binaries = collect_ares_files()

# Tell PyInstaller what hidden imports to include
hiddenimports = [
    # SDL2 modules
    'sdl2.dll', 'sdl2.sdlttf', 'sdl2.sdlimage', 'sdl2.sdlmixer',
    
    # Core ares modules
    'ares.math.vector', 'ares.math.matrix', 
    'ares.physics.collision', 
    'ares.core.window', 'ares.core.input',
    
    # Configuration/logging system
    'ares.config.config_manager', 
    'ares.config.logging_config',
    'ares.config.config_types',
    'ares.config',
    'ares.config.base_config',
    
    # Utils
    'ares.utils.log',
    'ares.utils.paths',
    'ares.utils.const',
    
    # Hook modules - updated paths to utils.hook 
    'ares.utils.hook.configs_hook',
    'ares.utils.hook.logging_hook',
    'ares.utils.hook.sdl2_hook',
    'ares.utils.hook.cython_hook'
]
