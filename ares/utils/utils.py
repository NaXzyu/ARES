#!/usr/bin/env python3
"""General utility functions for the Ares Engine."""

import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

from ares.utils.const import (
    CURRENT_PLATFORM,
    DEFAULT_APP_NAME,
    ERROR_PYTHON_VERSION,
    KB,
    MB,
    GB,
    PLATFORM_LINUX,
    PLATFORM_MACOS,
    PLATFORM_WINDOWS,
    REQUIRED_PYTHON_VERSION,
    REQUIRED_PYTHON_VERSION_STR,
)

def is_windows():
    """Check if the current platform is Windows."""
    return CURRENT_PLATFORM == PLATFORM_WINDOWS

def is_macos():
    """Check if the current platform is macOS."""
    return CURRENT_PLATFORM == PLATFORM_MACOS

def is_linux():
    """Check if the current platform is Linux."""
    return CURRENT_PLATFORM == PLATFORM_LINUX

def format_size(size_bytes):
    """Format a size in bytes to a human-readable string.

    Args:
        size_bytes: Number of bytes to format

    Returns:
        str: Human-readable size string with units (e.g. "1.23 MB")
    """
    if size_bytes < KB:
        return f"{size_bytes:.2f} B"
    elif size_bytes < MB:
        return f"{size_bytes/KB:.2f} KB"
    elif size_bytes < GB:
        return f"{size_bytes/MB:.2f} MB"
    else:
        return f"{size_bytes/GB:.2f} GB"

def format_time(seconds):
    """Format seconds into a human-readable duration string.

    Args:
        seconds: Number of seconds to format

    Returns:
        str: Human-readable time string (e.g. "5 min 30.5 sec")
    """
    if seconds < 0.1:
        return f"{seconds*1000:.0f} milliseconds"
    elif seconds < 60:
        return f"{seconds:.2f} seconds"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} and {secs:.2f} seconds"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours} hr {minutes} min"

def compute_file_hash(file_path):
    """Compute the MD5 hash of a file.
    
    Args:
        file_path: Path to the file to hash

    Returns:
        str: MD5 hash as hexadecimal string, or None if hashing fails
    """
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        print(f"Warning: Failed to compute hash for {file_path}: {e}")
        return None

def format_version(version_tuple):
    """Format a version tuple into a string.
    
    Args:
        version_tuple: Tuple of (major, minor) version numbers
        
    Returns:
        str: Formatted version string (e.g. "3.12")
    """
    return '.'.join(map(str, version_tuple))

def get_current_python_version():
    """Get the current Python version as a tuple.
    
    Returns:
        tuple: Current Python version as (major, minor)
    """
    return (sys.version_info.major, sys.version_info.minor)

def is_python_version_compatible():
    """Check if the current Python version meets requirements.
    
    Returns:
        bool: True if current Python version meets or exceeds the required version
    """
    return sys.version_info[:2] >= REQUIRED_PYTHON_VERSION

def check_python_version(python_path, required_version=REQUIRED_PYTHON_VERSION):
    """Check if a Python interpreter meets version requirements.

    Args:
        python_path: Path to Python executable to check
        required_version: Tuple of (major, minor) version required

    Returns:
        bool: True if Python version meets or exceeds required_version
    """
    try:
        result = subprocess.run(
            [str(python_path), "-c", f"import sys; sys.exit(0 if sys.version_info >= {required_version} else 1)"],
            check=False
        )
        return result.returncode == 0
    except Exception:
        return False

def verify_python():
    """Verify the current Python version meets requirements.
    
    Terminates program with error code if version is incompatible.
    
    Returns:
        bool: True if version is compatible (program continues)
        
    Note: This function will exit the program if incompatible.
    """
    current_version = get_current_python_version()
    current_version_str = format_version(current_version)
    
    # Check if the current Python version is compatible
    if not is_python_version_compatible():
        print(f"Error: Python {REQUIRED_PYTHON_VERSION_STR}+ is required.")
        print(f"Current Python version is {current_version_str}.")
        print(f"Please upgrade Python or use a different interpreter.")
        sys.exit(ERROR_PYTHON_VERSION)
    
    return True

def copy_file_with_logging(source, dest):
    """Copy a file with error logging.
    
    Args:
        source: Source file path
        dest: Destination file path
        
    Returns:
        bool: True if copy succeeded, False if failed
    """
    try:
        shutil.copy2(source, dest)
        print(f"Created file: {dest}")
        return True
    except Exception as e:
        print(f"Error copying file {source} to {dest}: {e}")
        return False

# Flag to detect recursive calls for get_app_name
_loading_config = False

def get_app_name() -> str:
    """Get application name from project config or use default.
    
    Returns:
        str: Application name from project config or fallback default
    """
    global _loading_config
    
    # If we're already in the process of loading configuration,
    # don't try to load project_config again to avoid recursion
    if _loading_config:
        if getattr(sys, 'frozen', False):
            return Path(sys.executable).stem
        else:
            return DEFAULT_APP_NAME
    
    try:
        # Set flag to prevent recursion
        _loading_config = True
        
        # Import here to avoid circular imports
        from ares.config.project_config import ProjectConfig
        project_config = ProjectConfig()
        app_name = project_config.get_product_name()
        
        # Reset flag
        _loading_config = False
        
        return app_name
    except (ImportError, AttributeError, RecursionError):
        # Reset flag
        _loading_config = False
        
        # Fallback to executable name or default
        if getattr(sys, 'frozen', False):
            return Path(sys.executable).stem
        else:
            return DEFAULT_APP_NAME
