"""Build utility functions for Ares Engine."""

import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ares.utils.const import (
    CURRENT_PLATFORM,
    ENTRY_POINT_PATTERNS,
    FILE_CHUNK_SIZE,
    FILE_ENCODING,
    MAIN_SCRIPT_NAME,
    MODULE_EXTENSIONS,
    PYCACHE_DIR_NAME,
    PLATFORM_WINDOWS,
    SDL2_DLL_DESTINATION,
    SDL2_DLL_SUBDIRS,
)
from ares.utils.log import log
from ares.utils.paths import Paths

def find_main_script(path: Path) -> Optional[Path]:
    """
    Locate main.py in the directory and verify its entry point.

    Args:
        directory: Directory to search for 'main.py'

    Returns:
        Path of 'main.py' if found and valid, otherwise None
    """
    path = Path(path)
    
    # Check for main.py in the root directory
    main_script = path / MAIN_SCRIPT_NAME
    
    if not main_script.exists():
        log.error(f"{MAIN_SCRIPT_NAME} not found in {path}. Projects must have a {MAIN_SCRIPT_NAME} file in the root directory.")
        return None
        
    # Verify main.py has proper entry point
    try:
        with open(main_script, 'r', encoding=FILE_ENCODING) as f:
            content = f.read()
            if any(pattern in content for pattern in ENTRY_POINT_PATTERNS):
                return main_script
            else:
                log.error(f"{MAIN_SCRIPT_NAME} found but missing required entry point. {MAIN_SCRIPT_NAME} must contain 'if __name__ == \"__main__\":' block.")
                return None
    except Exception as e:
        log.error(f"Error reading {MAIN_SCRIPT_NAME}: {e}")
        return None

def compute_file_hash(file_path: Path) -> Optional[str]:
    """Return MD5 hex digest of a file.

    Args:
        file_path: Path to the file

    Returns:
        MD5 hash as a hexadecimal string, or None if hashing fails
    """
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(FILE_CHUNK_SIZE), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        log.warn(f"Failed to compute hash for {file_path}: {e}")
        return None

def hash_config(config: Dict[str, Any]) -> str:
    """Hash a configuration dictionary.

    Args:
        config: Configuration to hash

    Returns:
        MD5 hex digest of the configuration, or empty string if None
    """
    if not config:
        return ""
    
    try:
        # Convert any Path objects to strings before serialization
        def make_serializable(value: Any) -> Any:
            """Convert a value to a JSON serializable type."""
            if isinstance(value, Path):
                return str(value)
            elif isinstance(value, dict):
                return {k: make_serializable(v) for k, v in value.items()}
            elif isinstance(value, (list, tuple)):
                return [make_serializable(item) for item in value]
            else:
                return value
        
        # Make a serializable copy of the config
        serializable_config = make_serializable(config)
        
        # Sort keys for consistent hashing regardless of dict ordering
        config_str = json.dumps(serializable_config, sort_keys=True)
        return hashlib.md5(config_str.encode()).hexdigest()
    except Exception as e:
        log.warn(f"Failed to hash config: {e}")
        return ""

def find_cython_binaries(project_root: Optional[Path] = None) -> List[Tuple[str, str]]:
    """
    Return Cython and Python modules in the ares package.

    Args:
        project_root: Project root directory

    Returns:
        List of tuples (file_path, dest_dir) for PyInstaller binaries
    """
    # Default project root if not specified
    if project_root is None:
        project_root = Paths.PROJECT_ROOT
    else:
        project_root = Path(project_root)
    
    binaries = []
    
    # Include the entire 'ares' package instead of selective modules
    ares_root = project_root / "ares"
    
    # Walk through the entire module structure
    for root, _, files in os.walk(ares_root):
        for file in files:
            # Skip __pycache__ directories
            if PYCACHE_DIR_NAME in root:
                continue
                
            # Use normpath to properly handle path separators
            rel_path = os.path.relpath(root, project_root)
            dest_dir = os.path.normpath(rel_path)

            # Full path to the file
            file_path = Path(root) / file
            
            # Include Python files and compiled extensions
            if any(file.endswith(ext) for ext in MODULE_EXTENSIONS):
                binaries.append((str(file_path), dest_dir))
                log.debug(f"Including module file: {file_path} -> {dest_dir}")
    
    return binaries

def find_sdl2_dlls(python_exe, logger=None):
    """Find SDL2 DLLs and return them as a list of (source, destination) tuples.
    
    Args:
        python_exe: Path to Python executable to use
        logger: Optional logger function for status messages
        
    Returns:
        list: List of tuples (dll_path, destination) for PyInstaller binaries
    """
    # We only need SDL2 DLLs on Windows
    if CURRENT_PLATFORM != PLATFORM_WINDOWS:
        return []
        
    # Log if logger is provided
    def log(message):
        if logger:
            logger(message)
    
    log("Locating SDL2 libraries...")
    
    sdl2_finder = """
import os, sys, glob, site
from pathlib import Path

def find_sdl2_dlls():
    # First check if pysdl2-dll package is installed
    try:
        from sdl2dll import get_dllpath
        dll_path = get_dllpath()
        if os.path.exists(dll_path):
            dlls = glob.glob(os.path.join(dll_path, "*.dll"))
            if dlls:
                print(f"FOUND_DLLS:{dll_path}")
                for dll in dlls:
                    print(f"DLL:{os.path.basename(dll)}")
                return
    except ImportError:
        pass
    
    # Check installation in site-packages
    for site_dir in site.getsitepackages():
        for dll_subdir in {dll_subdirs}:
            check_dir = os.path.join(site_dir, dll_subdir)
            if os.path.exists(check_dir):
                dlls = glob.glob(os.path.join(check_dir, "*.dll"))
                if dlls:
                    print(f"FOUND_DLLS:{{check_dir}}")
                    for dll in dlls:
                        print(f"DLL:{{os.path.basename(dll)}}")
                    return
    
    print("NO_DLLS_FOUND")

find_sdl2_dlls()
""".format(dll_subdirs=SDL2_DLL_SUBDIRS)
    
    result = subprocess.run(
        [str(python_exe), "-c", sdl2_finder],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False
    )
    
    sdl2_dll_path = None
    sdl2_dlls = []
    
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.startswith("FOUND_DLLS:"):
            sdl2_dll_path = line[11:].strip()  # Fixed 'trip()' to 'strip()'
            log(f"Found SDL2 DLL directory: {sdl2_dll_path}")
        elif line.startswith("DLL:"):
            dll_name = line[4:].strip()
            sdl2_dlls.append(dll_name)
            log(f"Found SDL2 DLL: {dll_name}")
    
    binaries = []
    if sdl2_dll_path and sdl2_dlls:
        for dll in sdl2_dlls:
            dll_path = os.path.join(sdl2_dll_path, dll)
            if os.path.exists(dll_path):
                binaries.append((dll_path, SDL2_DLL_DESTINATION))
    
    return binaries