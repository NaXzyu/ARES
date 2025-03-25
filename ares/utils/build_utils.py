"""
Build utility functions for Ares Engine.
"""
from pathlib import Path
import sys
import os
import hashlib
import json

def find_main_script(directory):
    """Find a Python script with an entry point in the directory.
    
    Searches for main.py in the directory root and verifies it has a proper 
    entry point with "if __name__ == '__main__':" block.
    
    Args:
        directory: Path to search for main.py entry point
        
    Returns:
        Path to the main.py script or None if not found or invalid
    """
    directory = Path(directory)
    
    # Check for main.py in the root directory
    main_script = directory / "main.py"
    
    if not main_script.exists():
        print(f"Error: main.py not found in {directory}")
        print("Projects must have a main.py file in the root directory.")
        return None
        
    # Verify main.py has proper entry point
    try:
        with open(main_script, 'r', encoding='utf-8') as f:
            content = f.read()
            if "if __name__ == '__main__':" in content or 'if __name__ == "__main__":' in content:
                return main_script
            else:
                print(f"Error: main.py found but missing required entry point.")
                print("main.py must contain 'if __name__ == \"__main__\":' block.")
                return None
    except Exception as e:
        print(f"Error reading main.py: {e}")
        return None

def get_cython_module_dirs(project_root=None, error_on_missing=False):
    """Get Cython module directories from project configuration.
    
    Args:
        project_root: Optional path to project root directory
        error_on_missing: If True, raise an error when no modules defined
        
    Returns:
        List of tuples (module_path, description)
    """
    # Default project root if not specified
    if project_root is None:
        # Find the project root from the current file
        project_root = Path(__file__).resolve().parent.parent.parent
    
    # Ensure project_root is a Path object
    project_root = Path(project_root)
    
    # Add project root to path to ensure imports work
    sys.path.insert(0, str(project_root))
    
    try:
        from ares.config import config
        project_config = config.load("project")
        
        cython_dirs = []
        if project_config and project_config.has_option("cython", "module_dirs"):
            module_dirs_str = project_config.get("cython", "module_dirs")
            
            # Parse the comma-separated list of module_name:description pairs
            for module_pair in module_dirs_str.split(','):
                module_pair = module_pair.strip()
                if ':' in module_pair:
                    module_name, description = module_pair.split(':', 1)
                    module_path = project_root / "ares" / module_name.strip()
                    cython_dirs.append((module_path, description.strip()))
        
        if not cython_dirs:
            error_msg = "Error: No Cython module directories defined in project.ini."
            error_details = "Please define module_dirs in the [cython] section of project.ini."
            
            # Import logging if available
            try:
                from ares.utils import log
                log.error(error_msg)
                log.error(error_details)
            except ImportError:
                print(error_msg)
                print(error_details)
            
            return []
        
        return cython_dirs
    except ImportError as e:
        # Handle case where config module can't be imported
        print(f"Error: Could not load project configuration: {e}")
        return []

def compute_file_hash(file_path):
    """Compute the MD5 hash of a file.
    
    Args:
        file_path: Path to the file to hash
        
    Returns:
        MD5 hash of the file as a hex string
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
        config: Dictionary containing configuration to hash
        
    Returns:
        str: MD5 hash of the configuration as a hex string, or empty string if config is None
    """
    if not config:
        return ""
    try:
        # Sort keys for consistent hashing regardless of dict ordering
        config_str = json.dumps(config, sort_keys=True)
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
    """Find all compiled Cython modules and Python files in the ares package.
    
    Args:
        project_root: Optional path to project root directory
        logger: Optional logging function to use for debug output
        
    Returns:
        list: List of tuples (file_path, dest_dir) for PyInstaller binaries
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
    for root, dirs, files in os.walk(ares_root):
        for file in files:
            # Skip __pycache__ directories
            if "__pycache__" in root:
                continue
                
            # Get relative path from ares root to create proper destination
            rel_path = os.path.relpath(root, project_root)
            dest_dir = rel_path.replace("\\", "/")  # Normalize path separators
            
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
