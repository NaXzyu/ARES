"""
PyInstaller hook for Ares Engine.

This automatically includes all required modules and binaries.
"""
import os
from pathlib import Path

def get_ares_path():
    """Get the path to the ares package."""
    import ares
    return Path(ares.__file__).parent

def collect_ares_files():
    """Collect all Ares Engine files."""
    datas = []
    binaries = []
    
    # Get the ares package path
    ares_path = get_ares_path()
    
    # Walk through the package
    for root, dirs, files in os.walk(ares_path):
        # Skip __pycache__ directories
        if "__pycache__" in root:
            continue
            
        for file in files:
            # Skip __pycache__ files and .pyc files
            if "__pycache__" in file or file.endswith('.pyc'):
                continue
                
            src_path = os.path.join(root, file)
            dest_dir = os.path.relpath(root, ares_path.parent)
            
            if file.endswith(('.pyd', '.so')):
                binaries.append((src_path, dest_dir))
            elif file.endswith(('.py', '.ini')):
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
    'ares.utils.log',
    'ares.utils.paths',
    'ares.utils.constants',
    'ares.utils.utils',
    'ares.utils.debug_utils',
    
    # Hook modules - consistently using new naming convention
    'ares.hooks.configs_hook',
    'ares.hooks.logging_hook',
    'ares.hooks.sdl2_hook',
    'ares.hooks.cython_hook'
]
