#!/usr/bin/env python3
"""General utility functions for the Ares Engine.

This module provides utility functions for formatting sizes and times,
computing file hashes, checking Python versions, and managing virtual environments.
"""

import os
import hashlib
import subprocess
import platform
import shutil
from ares.utils.constants import REQUIRED_PYTHON_VERSION

def is_windows():
    """Check if the current platform is Windows."""
    return os.name == 'nt'

def is_macos():
    """Check if the current platform is macOS."""
    return platform.system() == "Darwin"

def is_linux():
    """Check if the current platform is Linux."""
    return platform.system() == "Linux"

def format_size(size_bytes):
    """Format a size in bytes to a human-readable string.

    Args:
        size_bytes: Number of bytes to format

    Returns:
        str: Human-readable size string with units (e.g. "1.23 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024 or unit == 'GB':
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024

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

def detect_existing_venv(project_root):
    """Detect existing virtual environments in a project directory.

    Searches common virtual environment locations and verifies Python version compatibility.

    Args:
        project_root: Path to the project root directory to search

    Returns:
        Path: Path to detected virtual environment directory, or None if not found
    """
    venv_dirs = [
        project_root / ".venv",
        project_root / "venv",
        project_root / "env",
        project_root / ".env",
        project_root / "virtualenv",
        project_root / ".conda_env"
    ]
    for venv_dir in venv_dirs:
        if not venv_dir.exists():
            continue
        if os.name == 'nt':
            python_exe = venv_dir / "Scripts" / "python.exe"
        else:
            python_exe = venv_dir / "bin" / "python"
        if python_exe.exists() and check_python_version(python_exe):
            return venv_dir
    return None

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
