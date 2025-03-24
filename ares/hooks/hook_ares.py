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
        for file in files:
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
    'sdl2.dll', 'sdl2.sdlttf', 'sdl2.sdlimage', 'sdl2.sdlmixer',
    'ares.math.vector', 'ares.math.matrix', 
    'ares.physics.collision', 
    'ares.core.window', 'ares.core.input',
    'ares.config.logging_config', 'ares.utils.log'
]
