"""Build utility functions for Ares Engine."""

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ares.utils.const import (
    CURRENT_PLATFORM,
    DEFAULT_APP_NAME,
    ENTRY_POINT_PATTERNS,
    ERROR_PYTHON_VERSION,
    FILE_CHUNK_SIZE,
    FILE_ENCODING,
    GB,
    KB,
    MAIN_SCRIPT_NAME,
    MB,
    MODULE_EXTENSIONS,
    PYCACHE_DIR_NAME,
    PLATFORM_LINUX,
    PLATFORM_MACOS,
    PLATFORM_WINDOWS,
    REQUIRED_PYTHON_VERSION,
    REQUIRED_PYTHON_VERSION_STR,
    SDL2_DLL_DESTINATION,
    SDL2_DLL_SUBDIRS,
    ERROR_MISSING_DEPENDENCY,
)
from ares.utils.log import log
from ares.utils.paths import Paths

class BuildUtils:
    """Utility functions for the Ares Engine build system."""
    
    # Flag to detect recursive calls for get_app_name
    _loading_config = False

    @staticmethod
    def is_windows():
        """Check if the current platform is Windows."""
        return CURRENT_PLATFORM == PLATFORM_WINDOWS

    @staticmethod
    def is_macos():
        """Check if the current platform is macOS."""
        return CURRENT_PLATFORM == PLATFORM_MACOS

    @staticmethod
    def is_linux():
        """Check if the current platform is Linux."""
        return CURRENT_PLATFORM == PLATFORM_LINUX

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def format_version(version_tuple):
        """Format a version tuple into a string.
        
        Args:
            version_tuple: Tuple of (major, minor) version numbers
            
        Returns:
            str: Formatted version string (e.g. "3.12")
        """
        return '.'.join(map(str, version_tuple))

    @staticmethod
    def get_current_python_version():
        """Get the current Python version as a tuple.
        
        Returns:
            tuple: Current Python version as (major, minor)
        """
        return (sys.version_info.major, sys.version_info.minor)

    @staticmethod
    def is_python_version_compatible():
        """Check if the current Python version meets requirements.
        
        Returns:
            bool: True if current Python version meets or exceeds the required version
        """
        return sys.version_info[:2] >= REQUIRED_PYTHON_VERSION

    @staticmethod
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

    @staticmethod
    def verify_python():
        """Verify the current Python version meets requirements.
        
        Terminates program with error code if version is incompatible.
        
        Returns:
            bool: True if version is compatible (program continues)
            
        Note: This function will exit the program if incompatible.
        """
        current_version = BuildUtils.get_current_python_version()
        current_version_str = BuildUtils.format_version(current_version)
        
        # Check if the current Python version is compatible
        if not BuildUtils.is_python_version_compatible():
            print(f"Error: Python {REQUIRED_PYTHON_VERSION_STR}+ is required.")
            print(f"Current Python version is {current_version_str}.")
            print(f"Please upgrade Python or use a different interpreter.")
            sys.exit(ERROR_PYTHON_VERSION)
        
        return True

    @staticmethod
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

    @classmethod
    def get_app_name(cls) -> str:
        """Get application name from project config or use default.
        
        Returns:
            str: Application name from project config or fallback default
        """
        # If running in a frozen application (compiled executable)
        if getattr(sys, 'frozen', False):
            return Path(sys.executable).stem
            
        # If we're already in the process of loading configuration,
        # don't try to load project_config again to avoid recursion
        if cls._loading_config:
            return DEFAULT_APP_NAME
        
        try:
            # Set flag to prevent recursion
            cls._loading_config = True
            
            # Import here to avoid circular imports
            from ares.config.project_config import ProjectConfig
            project_config = ProjectConfig()
            app_name = project_config.get_product_name()
            
            # Reset flag
            cls._loading_config = False
            
            # Return the name or default if empty
            return app_name if app_name else DEFAULT_APP_NAME
            
        except (ImportError, AttributeError, RecursionError):
            # Reset flag
            cls._loading_config = False
            return DEFAULT_APP_NAME

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def find_cython_binaries(project_root: Optional[Path] = None, log_fn = None) -> List[Tuple[str, str]]:
        """
        Return Cython and Python modules in the ares package.

        Args:
            project_root: Project root directory
            log_fn: Optional logging function

        Returns:
            List of tuples (file_path, dest_dir) for PyInstaller binaries
        """
        # Default project root if not specified
        if project_root is None:
            project_root = Paths.PROJECT_ROOT
        else:
            project_root = Path(project_root)
        
        # Use provided log function or default to debug
        log_debug = log_fn if log_fn else log.debug
        
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
                    log_debug(f"Including module file: {file_path} -> {dest_dir}")
        
        return binaries

    @staticmethod
    def find_sdl2_dlls(python_exe, log_fn=None):
        """Find SDL2 DLLs that need to be included in the build."""
        if log_fn is None:
            log_fn = log.info
        
        log_fn("Locating SDL2 libraries...")
        
        # Prepare the list of subdirectories as a string representation for direct inclusion
        dll_subdirs_str = repr(list(SDL2_DLL_SUBDIRS))
        
        # Create the Python script without using .format() to avoid conflicts with f-strings
        sdl2_finder = f"""
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
                print(f"FOUND_DLLS:{{dll_path}}")
                for dll in dlls:
                    print(f"DLL:{{os.path.basename(dll)}}")
                return
    except ImportError:
        pass
    
    # Check installation in site-packages
    for site_dir in site.getsitepackages():
        for dll_subdir in {dll_subdirs_str}:
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
"""
        
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
                sdl2_dll_path = line[11:].strip()
                log_fn(f"Found SDL2 DLL directory: {sdl2_dll_path}")
            elif line.startswith("DLL:"):
                dll_name = line[4:].strip()
                sdl2_dlls.append(dll_name)
                log_fn(f"Found SDL2 DLL: {dll_name}")
        
        binaries = []
        if sdl2_dll_path and sdl2_dlls:
            for dll in sdl2_dlls:
                dll_path = os.path.join(sdl2_dll_path, dll)
                if os.path.exists(dll_path):
                    binaries.append((dll_path, SDL2_DLL_DESTINATION))
        
        return binaries

    @staticmethod
    def validate_hooks(output_path) -> List[str]:
        """
        Validate that required hook files exist and create runtime hooks.
        
        Args:
            output_path: Path where runtime hooks will be created
            
        Returns:
            List of created hook files if successful, exits process if validation failed
        """
        
        # Ensure we have a hooks directory
        hooks_dir = Paths.get_hooks_path()
        if not hooks_dir or not os.path.exists(hooks_dir):
            log.error(f"CRITICAL ERROR: Hooks directory not found at {hooks_dir}")
            log.error("Build cannot continue without hook files")
            sys.exit(ERROR_MISSING_DEPENDENCY)

        # Verify required hook files exist
        required_hooks = ['ares_hook.py']
        missing_hooks = []
        for hook in required_hooks:
            hook_path = Paths.get_hook_file(hook.split('.')[0])
            if not hook_path or not os.path.exists(hook_path):
                missing_hooks.append(hook)
        
        if missing_hooks:
            log.error(f"CRITICAL ERROR: Required hook files missing: {', '.join(missing_hooks)}")
            log.error(f"Looked in directory: {hooks_dir}")
            log.error("Build cannot continue without required hook files")
            sys.exit(ERROR_MISSING_DEPENDENCY)

        try:
            from ares.utils.hook.hook_manager import HookManager
            hooks = HookManager.create_runtime_hooks(output_path)
            if not hooks:
                log.error("CRITICAL ERROR: Failed to create runtime hooks")
                sys.exit(ERROR_MISSING_DEPENDENCY)
            return hooks
        except Exception as e:
            log.error(f"CRITICAL ERROR: Error creating runtime hooks: {e}")
            sys.exit(ERROR_MISSING_DEPENDENCY)