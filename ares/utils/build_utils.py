"""
Build utility functions for Ares Engine.
"""
import hashlib
import json
import os
from pathlib import Path

def find_main_script(directory):
    """
    Locate main.py in the directory and verify its entry point.

    Args:
        directory: Directory to search for 'main.py'

    Returns:
        Path of 'main.py' if found and valid, otherwise None.
    """
    directory = Path(directory)
    
    # Check for main.py in the root directory
    main_script = directory / "main.py"
    
    if not main_script.exists():
        print(f"Error: main.py not found in {directory}. Projects must have a main.py file in the root directory.")
        return None
        
    # Verify main.py has proper entry point
    try:
        with open(main_script, 'r', encoding='utf-8') as f:
            content = f.read()
            if "if __name__ == '__main__':" in content or 'if __name__ == "__main__":' in content:
                return main_script
            else:
                print("Error: main.py found but missing required entry point. main.py must contain 'if __name__ == \"__main__\":' block.")
                return None
    except Exception as e:
        print(f"Error reading main.py: {e}")
        return None

def compute_file_hash(file_path):
    """Return MD5 hex digest of a file.

    Args:
        file_path (str): Path to the file.

    Returns:
        str: MD5 hash as a hexadecimal string.
    """
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        # Import logging if available for better error reporting
        try:
            from ares.utils import log
            log.warn(f"Warning: Failed to compute hash for {file_path}: {e}")
        except ImportError:
            print(f"Warning: Failed to compute hash for {file_path}: {e}")
        return None

def hash_config(config):
    """Hash a configuration dictionary.

    Args:
        config (dict): Configuration to hash.

    Returns:
        str: MD5 hex digest of the configuration, or empty string if None.
    """
    if not config:
        return ""
    try:
        # Convert any Path objects to strings before serialization
        def make_serializable(value):
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
        # Import logging if available for better error reporting
        try:
            from ares.utils import log
            log.warn(f"Warning: Failed to hash config: {e}")
        except ImportError:
            print(f"Warning: Failed to hash config: {e}")
        return ""

def find_cython_binaries(project_root=None, logger=None):
    """
    Return Cython and Python modules in the ares package.

    Args:
        project_root (Path, optional): Project root directory.
        logger (Callable, optional): Logger for debug output.

    Returns:
        list: Tuples (file_path, dest_dir) for PyInstaller binaries.
    """
    # Default project root if not specified
    if project_root is None:
        project_root = Path(__file__).resolve().parent.parent.parent
    else:
        project_root = Path(project_root)
    
    binaries = []
    
    # Include the entire 'ares' package instead of selective modules
    ares_root = project_root / "ares"
    
    # Define a simple logging function if none provided
    log_func = logger if logger else lambda msg: None
    
    # Walk through the entire module structure
    for root, _, files in os.walk(ares_root):
        for file in files:
            # Skip __pycache__ directories
            if "__pycache__" in root:
                continue
                
            # Use normpath to properly handle path separators
            rel_path = os.path.relpath(root, project_root)
            dest_dir = os.path.normpath(rel_path)

            # Full path to the file
            file_path = Path(root) / file
            
            # Include Python files and compiled extensions
            if (file.endswith('.py') or 
                file.endswith('.pyd') or 
                file.endswith('.so') or
                file.endswith('.ini')):
                binaries.append((str(file_path), dest_dir))
                log_func(f"Including module file: {file_path} -> {dest_dir}")
    
    return binaries
