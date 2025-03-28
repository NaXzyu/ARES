#!/usr/bin/env python3
"""Build script for cleaning Ares Engine project files."""

import os
import shutil
import time
from pathlib import Path
from ares.utils.utils import format_time

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BUILD_DIR = PROJECT_ROOT / "build"
LOGS_DIR = PROJECT_ROOT / "logs"

def clean_project():
    """Clean up build artifacts from the project directory."""
    print("Cleaning up build artifacts...")
    
    # Start timing
    start_time = time.time()
    
    paths_to_clean = [
        BUILD_DIR,
        PROJECT_ROOT / "dist",
        PROJECT_ROOT / "ares.egg-info",
        PROJECT_ROOT / "__pycache__",
        LOGS_DIR,
    ]
    
    # Add .pyd, .c, and __pycache__ files from the project
    for root, dirs, files in os.walk(PROJECT_ROOT):
        root_path = Path(root)
        
        # Skip the venv directory
        if ".venv" in root_path.parts:
            continue
            
        # Clean __pycache__ directories
        if "__pycache__" in dirs:
            paths_to_clean.append(root_path / "__pycache__")
            
        # Clean generated files - look for compiled extensions and generated C files
        for file in files:
            if (file.endswith(('.pyd', '.c', '.so')) and 
                (file.startswith('_') or not file.endswith('.pyx.c'))):
                file_path = root_path / file
                if os.path.exists(file_path):
                    paths_to_clean.append(file_path)
    
    # Clean each path
    for path in paths_to_clean:
        try:
            if path.is_dir():
                print(f"Removing directory: {path}")
                shutil.rmtree(path, onexc=handle_remove_readonly)
            elif path.exists():
                print(f"Removing file: {path}")
                path.unlink()
        except Exception as e:
            print(f"WARNING: Could not remove {path}: {e}")
    
    # Calculate elapsed time and use the utility function
    elapsed_time = time.time() - start_time
    print(f"Clean completed successfully in {format_time(elapsed_time)}.")
    return True

# Helper function to handle read-only files on Windows
def handle_remove_readonly(func, path, exc):
    """Handle read-only files during deletion (Windows)."""
    import stat
    if os.name == 'nt':
        if func in (os.unlink, os.remove, os.rmdir) and exc[1].errno == 5:  # Access Denied
            os.chmod(path, stat.S_IWRITE)
            func(path)
        else:
            raise

def clean_egg_info():
    """Clean only egg-info directories - useful for pre-build cleanup."""
    # Import logging system from ares.utils
    from ares.utils import log
    
    for egg_info in PROJECT_ROOT.glob("*.egg-info"):
        if egg_info.is_dir():
            log.info(f"Removing {egg_info}")
            try:
                shutil.rmtree(egg_info, onexc=handle_remove_readonly)
                log.info(f"Successfully removed {egg_info}")
            except Exception as e:
                log.warn(f"WARNING: Could not remove {egg_info} - {e}")
    
    # Also clean __pycache__ directories
    for pycache in PROJECT_ROOT.glob("**/__pycache__"):
        if pycache.is_dir():
            try:
                shutil.rmtree(pycache, onexc=handle_remove_readonly)
            except Exception:
                pass
