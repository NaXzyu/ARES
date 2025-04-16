"""Path management utilities for Ares Engine."""

import os
import sys
from pathlib import Path
from typing import Dict, Optional

from ares.utils.const import (
    # Directory names
    APP_CACHE_DIR_NAME, APP_CONFIG_DIR_NAME, APP_LOGS_DIR_NAME,
    BUILD_DIR_NAME, CACHE_DIR_NAME, CONFIG_INI_DIR_NAME, DIST_PATH_NAME,
    ENGINE_DIR_NAME, EXECUTABLE_OUTPUT_DIR_NAME, HOOKS_PATH_NAME,
    INI_DIR_NAME, LOGS_DIR_NAME, SAVE_GAMES_DIR_NAME, SCREENSHOTS_DIR_NAME,
    
    # Default names
    BUILD_CACHE_FILE, BUILD_LOG_FILE, DEFAULT_LOG_FILE,
    
    # Path patterns and search patterns
    COMPILED_MODULE_PATTERNS, WHEEL_SEARCH_PATTERN,
    
    # Project subdirectories
    ARES_CHILD_PATH, CORE_SUBDIR, MATH_SUBDIR, PHYSICS_SUBDIR,
    RENDERER_SUBDIR, SPEC_CHILD_PATH
)

# Define standalone function for config modules to use
# This is independent of the Paths class to avoid circular imports
def get_user_config_dir() -> Path:
    """Get user configuration directory, creating it if needed.
    
    Returns:
        Path: Path to the user configuration directory
    """
    from ares.utils.build.build_utils import BuildUtils

    # Get the app name consistently
    app_name = BuildUtils.get_app_name()
    
    # Determine the base directory based on the platform
    if BuildUtils.is_windows():
        try:
            base_dir = Path(os.environ.get('LOCALAPPDATA', str(Path.home() / "AppData" / "Local")))
            base_dir = base_dir / app_name  # Use app_name directly, not hardcoded
        except (KeyError, TypeError):
            base_dir = Path.home() / "AppData" / "Local" / app_name
    elif BuildUtils.is_macos():
        base_dir = Path.home() / "Library" / "Application Support" / app_name
    else:
        # Linux and other platforms
        try:
            import appdirs
            base_dir = Path(appdirs.user_data_dir("ares-engine", app_name))
        except ImportError:
            base_dir = Path.home() / ".local" / "share" / "ares-engine" / app_name
    
    # Build the config directory path
    config_dir = base_dir / APP_CONFIG_DIR_NAME
    
    # Create the directory if it doesn't exist
    os.makedirs(config_dir, exist_ok=True)
    
    return config_dir


class Paths:
    """Central class for managing all engine paths with singleton pattern."""
    
    # Constants
    IS_FROZEN = getattr(sys, 'frozen', False)
    
    # Base directories
    PROJECT_ROOT = Path(sys._MEIPASS) if IS_FROZEN else Path(__file__).resolve().parents[2]
    APP_DIR = Path(sys.executable).parent if IS_FROZEN else PROJECT_ROOT
    
    # Cache data
    _initialized = False
    _user_dirs_cache = {}
    _project_cache_path = None
    
    
    @classmethod
    def _initialize(cls):
        """Perform any initialization needed for the paths system"""
        if cls._initialized:
            return
            
        # Set flag first to prevent recursion
        cls._initialized = True
        
        # Pre-compute the project paths to avoid recursive calls
        project_paths = {
            "PROJECT_ROOT": cls.PROJECT_ROOT,
            "APP_DIR": cls.APP_DIR,
            "BUILD_DIR": cls.PROJECT_ROOT / BUILD_DIR_NAME,
            "DEV_LOGS_DIR": cls.PROJECT_ROOT / LOGS_DIR_NAME,
            "ENGINE_BUILD_DIR": cls.PROJECT_ROOT / BUILD_DIR_NAME / ENGINE_DIR_NAME,
            "CACHE_DIR": cls.PROJECT_ROOT / BUILD_DIR_NAME / CACHE_DIR_NAME
        }
        
        # Cache the project paths
        cls._project_cache_path = project_paths
        
        # Create directories without causing recursive calls
        for key in ["BUILD_DIR", "DEV_LOGS_DIR", "ENGINE_BUILD_DIR", "CACHE_DIR"]:
            try:
                os.makedirs(project_paths[key], exist_ok=True)
            except (OSError, PermissionError):
                pass
    
    @classmethod
    def get_user_data_paths(cls, app_name: Optional[str] = None) -> Dict[str, Path]:
        """Get user data directories based on platform.
        
        Args:
            app_name: Optional app name override (defaults to auto-detected app name)
            
        Returns:
            dict: Dictionary containing paths for different user data purposes
        """
        from ares.utils.build.build_utils import BuildUtils

        # Ensure initialized
        if not cls._initialized:
            cls._initialize()
        
        # Use cached results if available
        cache_key = app_name or "default"
        if cache_key in cls._user_dirs_cache:
            return cls._user_dirs_cache[cache_key]
            
        if app_name is None:
            app_name = BuildUtils.get_app_name()
        
        # Determine the base directory based on the platform
        if BuildUtils.is_windows():
            try:
                base_dir = Path(os.environ.get('LOCALAPPDATA', str(Path.home() / "AppData" / "Local")))
                base_dir = base_dir / app_name
            except (KeyError, TypeError):
                base_dir = Path.home() / "AppData" / "Local" / app_name
        elif BuildUtils.is_macos():
            base_dir = Path.home() / "Library" / "Application Support" / app_name
        else:
            # Linux and other platforms
            try:
                import appdirs
                base_dir = Path(appdirs.user_data_dir("ares-engine", app_name))
            except ImportError:
                base_dir = Path.home() / ".local" / "share" / "ares-engine" / app_name
        
        # Create the base directory if it doesn't exist
        paths = {
            "BASE_DIR": base_dir,
            "CONFIG_DIR": base_dir / APP_CONFIG_DIR_NAME,
            "LOGS_DIR": base_dir / APP_LOGS_DIR_NAME,
            "SCREENSHOTS_DIR": base_dir / SCREENSHOTS_DIR_NAME,
            "SAVES_DIR": base_dir / SAVE_GAMES_DIR_NAME,
            "CACHE_DIR": base_dir / APP_CACHE_DIR_NAME
        }
        
        # Cache the result
        cls._user_dirs_cache[cache_key] = paths
        return paths


    @classmethod
    def get_project_paths(cls) -> Dict[str, Path]:
        """Get directories for development and build operations in the project.
        
        Returns:
            dict: Dictionary containing paths for project-related directories
        """
        # Ensure initialized without recursive calls
        if not cls._initialized:
            cls._initialize()
        
        # Return the cached paths
        return cls._project_cache_path


    @classmethod
    def create_app_paths(cls, app_name: Optional[str] = None) -> Dict[str, Path]:
        """Create all required app data directories.
        
        Args:
            app_name: Optional app name override
            
        Returns:
            dict: Dictionary of created directories
        """
        paths = cls.get_user_data_paths(app_name)
        for directory in paths.values():
            try:
                os.makedirs(directory, exist_ok=True)
            except (OSError, PermissionError):
                pass
        return paths


    @classmethod
    def create_project_paths(cls) -> Dict[str, Path]:
        """Create all required project directories.
        
        Returns:
            dict: Dictionary of created directories
        """
        # Make sure we're initialized
        if not cls._initialized:
            cls._initialize()
            
        # Return the cached project paths
        return cls._project_cache_path


    @classmethod
    def get_ini_dir(cls) -> Path:
        """Get the directory containing INI configuration files."""
        if cls.IS_FROZEN:
            return Path(sys._MEIPASS) / ARES_CHILD_PATH / CONFIG_INI_DIR_NAME
        else:
            return cls.PROJECT_ROOT / ARES_CHILD_PATH / "config" / CONFIG_INI_DIR_NAME
    

    @classmethod
    def get_embedded_ini_file(cls, filename: str) -> Path:
        """Get path to an embedded INI file in frozen applications.
        
        Args:
            filename: Name of the INI file to locate
            
        Returns:
            Path: Path to the INI file in the frozen app or development tree
        """
        return cls.get_ini_dir() / filename
    

    @classmethod
    def get_logs_path(cls, for_app: bool = True, app_name: Optional[str] = None) -> Path:
        """Get the appropriate logs directory (app or project).
        
        Args:
            for_app: True to get app logs dir, False to get project logs dir
            app_name: Optional app name for app logs dir
        
        Returns:
            Path: Path to appropriate logs directory
        """
        if for_app and cls.IS_FROZEN:
            # For runtime frozen apps, use the app logs directory
            return cls.get_user_data_paths(app_name)["LOGS_DIR"]
        else:
            # For development or build logs, use project logs directory
            return cls.get_project_paths()["DEV_LOGS_DIR"]
    

    @classmethod
    def get_log_file(cls, filename: str, for_app: bool = True, app_name: Optional[str] = None) -> Path:
        """Get the path to a specific log file.
        
        Args:
            filename: Name of the log file
            for_app: True to use app logs dir, False to use project logs dir
            app_name: Optional app name for app logs
            
        Returns:
            Path: Path to the log file
        """
        return cls.get_logs_path(for_app, app_name) / filename
    

    @classmethod
    def get_runtime_log_file(cls, app_name: Optional[str] = None) -> Path:
        """Get the path to the runtime log file."""
        if cls.IS_FROZEN:
            from ares.utils import BuildUtils
            app_name = app_name or BuildUtils.get_app_name()
            return cls.get_log_file(f"{app_name}.log", True, app_name)
        else:
            # For development, use engine.log in project logs directory
            return cls.get_log_file(DEFAULT_LOG_FILE, False)
    

    @classmethod
    def get_build_log_file(cls) -> Path:
        """Get the path to the build log file.
        Always use project logs directory for build logs.
        """
        return cls.get_log_file(BUILD_LOG_FILE, False)


    @classmethod
    def get_user_config_path(cls) -> Path:
        """Get the user config directory without risking circular imports."""
        # Use the standalone function to avoid circular imports
        return get_user_config_dir()
    

    @classmethod
    def get_user_data_path(cls, app_name: Optional[str] = None) -> Path:
        """Get the user data directory, creating it if needed."""
        dirs = cls.create_app_paths(app_name)
        return dirs["BASE_DIR"]
    

    @classmethod
    def get_user_logs_path(cls, app_name: Optional[str] = None) -> Path:
        """Get the user logs directory, creating it if needed."""
        dirs = cls.create_app_paths(app_name)
        return dirs["LOGS_DIR"]
    

    @classmethod
    def get_user_screenshots_path(cls, app_name: Optional[str] = None) -> Path:
        """Get the user screenshots directory, creating it if needed."""
        dirs = cls.create_app_paths(app_name)
        return dirs["SCREENSHOTS_DIR"]
    

    @classmethod
    def get_user_saves_path(cls, app_name: Optional[str] = None) -> Path:
        """Get the user saves directory, creating it if needed."""
        dirs = cls.create_app_paths(app_name)
        return dirs["SAVES_DIR"]


    @classmethod
    def get_build_path(cls) -> Path:
        """Get the project build directory path."""
        return cls.get_project_paths()["BUILD_DIR"]
    

    @classmethod
    def get_cache_path(cls) -> Path:
        """Get the build cache directory path."""
        return cls.get_project_paths()["CACHE_DIR"]
    

    @classmethod
    def get_build_cache_file(cls) -> Path:
        """Get the path to the build cache JSON file."""
        return cls.get_cache_path() / BUILD_CACHE_FILE
    

    @classmethod
    def get_dev_logs_path(cls) -> Path:
        """Get the development logs directory."""
        return cls.get_project_paths()["DEV_LOGS_DIR"]


    @classmethod
    def find_wheel_files(cls, path=None):
        """Find wheel package files in the specified directory.
        
        Args:
            directory: Directory to search for wheel files (default: build directory)
            
        Returns:
            list: List of Path objects for wheel files
        """
        if path is None:
            path = cls.get_build_path()
        else:
            path = Path(path)
            
        return list(path.glob(WHEEL_SEARCH_PATTERN))


    @classmethod
    def get_dist_path(cls) -> Path:
        """Get the distribution directory path within the project."""
        return cls.PROJECT_ROOT / DIST_PATH_NAME


    @classmethod
    def get_formatted_file_size(cls, file_path):
        """Get the formatted size of a file with appropriate units.
        
        Args:
            file_path: Path to the file
            
        Returns:
            str: Human-readable formatted file size (e.g., "1.25 MB")
        """
        try:
            from ares.utils.build.build_utils import BuildUtils

            size_bytes = os.path.getsize(file_path)
            return BuildUtils.format_size(size_bytes)
        except (OSError, FileNotFoundError) as e:
            from ares.utils import log
            log.warn(f"Error getting size of {file_path}: {e}")
            return "unknown size"


    @classmethod
    def get_module_path(cls, module_name):
        """Get the path to a module within the Ares package.
        
        Args:
            module_name: Name of the module
            
        Returns:
            Path: Path to the module directory
        """
        return cls.PROJECT_ROOT / ARES_CHILD_PATH / module_name
    

    @classmethod
    def get_default_cython_paths(cls):
        """Get the default Cython module directories.
        
        Returns:
            list: List of tuples containing (path, description) for Cython modules
        """
        paths = [
            (cls.get_module_path(CORE_SUBDIR), "core modules"),
            (cls.get_module_path(MATH_SUBDIR), "math modules"),
            (cls.get_module_path(PHYSICS_SUBDIR), "physics modules"),
            (cls.get_module_path(RENDERER_SUBDIR), "renderer modules")
        ]
        return paths
    

    @classmethod
    def get_ini_path(cls, filename):
        """Get the path to an INI file within the Ares INI directory.
        
        Args:
            filename: Name of the INI file
            
        Returns:
            Path: Path to the INI file
        """
        return cls.PROJECT_ROOT / ARES_CHILD_PATH / "config" / INI_DIR_NAME / filename


    @classmethod
    def get_python_module_path(cls, relative_path):
        """Get the full path to a Python module within the project.
        
        Args:
            relative_path: Relative path to the Python module from project root
            
        Returns:
            Path: Full path to the Python module
        """
        return cls.PROJECT_ROOT / relative_path


    @classmethod
    def find_compiled_module_files(cls, path):
        """Find all compiled module files in a directory.
        
        Args:
            directory: Directory to search
            
        Returns:
            set: Set of module filenames found
        """
        found_files = set()
        
        # Search using all the compiled module patterns from constants
        for pattern in COMPILED_MODULE_PATTERNS:
            for file in Path(path).glob(pattern):
                found_files.add(file.name)
            
        return found_files


    @classmethod
    def find_lib_paths(cls, base_path):
        """Find library directories matching lib.*
        
        Args:
            base_directory: Base directory to search
            
        Returns:
            list: List of found library directories
        """
        return list(Path(base_path).glob("lib.*"))


    @classmethod
    def get_module_build_path(cls, ares_path, module_name):
        """Get the build directory for a specific module.
        
        Args:
            ares_dir: Ares package directory in the build
            module_name: Module name or Path object with name attribute
            
        Returns:
            Path: Module build directory
        """
        if hasattr(module_name, 'name'):
            module_name = module_name.name
            
        return Path(ares_path) / module_name


    @classmethod
    def get_cython_module_path(cls):
        """Get Cython module directories from project configuration.
        
        Returns:
            list: List of tuples containing (path, description) for Cython modules
            
        Raises:
            ValueError: If no valid Cython module directories are found
        """
        # Helper function to parse module directories string
        def parse_module_paths(module_dirs_str):
            if not module_dirs_str:
                return []
                
            parsed_modules = []
            for module_pair in module_dirs_str.split(','):
                module_pair = module_pair.strip()
                if ':' in module_pair:
                    module_name, description = module_pair.split(':', 1)
                    module_path = cls.get_module_path(module_name.strip())
                    parsed_modules.append((module_path, description.strip()))
            return parsed_modules
        
        # Try to use CONFIGS dictionary first
        try:
            from ares.config.config_types import ConfigType
            from ares.config import CONFIGS
            
            if ConfigType.BUILD in CONFIGS and CONFIGS[ConfigType.BUILD] is not None:
                module_paths_str = CONFIGS[ConfigType.BUILD].get_raw_cython_module_dirs()
                cython_paths = parse_module_paths(module_paths_str)
                if cython_paths:
                    return cython_paths
        except (ImportError, KeyError, AttributeError):
            from ares.utils import log
            log.warn("Could not access BuildConfig from CONFIGS. Trying direct file access.")
        
        # Try to read from build.ini file
        ini_path = cls.get_ini_path("build.ini")
        if ini_path and ini_path.exists():  # Add None check
            import configparser
            parser = configparser.ConfigParser()
            parser.read(ini_path)
            
            if 'cython' in parser and 'module_dirs' in parser['cython']:
                module_paths_str = parser['cython']['module_dirs']
                cython_paths = parse_module_paths(module_paths_str)
                if cython_paths:
                    return cython_paths
        
        # If no valid paths found, raise an error
        from ares.utils import log
        log.error("Error: No valid Cython module directories defined.")
        log.error("Please define module_dirs in the [cython] section of build.ini.")
        raise ValueError("No valid Cython module directories found in configuration.")

    @classmethod
    def get_ares_path(cls, base_dir):
        """Get the ares package directory within a base directory.
        
        Args:
            base_dir: Base directory containing the ares package
            
        Returns:
            Path: Path to the ares package directory
        """
        return Path(base_dir) / ARES_CHILD_PATH

    @classmethod
    def get_hooks_path(cls) -> Path:
        """Get the directory containing hook files.
        
        Returns:
            Path: Path to the hooks directory
        """
        return cls.PROJECT_ROOT / ARES_CHILD_PATH / "utils" / "hook"
    
    @classmethod
    def get_hook_file(cls, hook_name: str) -> Path:
        """Get the path to a specific hook file.
        
        Args:
            hook_name: Name of the hook file (with or without .py extension)
            
        Returns:
            Path: Path to the hook file
        """
        if not hook_name.endswith('.py'):
            hook_name = f"{hook_name}.py"
        return cls.get_hooks_path() / hook_name

    @classmethod
    def get_project_source_path(cls, project_path):
        """Convert a project path to a Path object if needed.
        
        Args:
            project_path: Path to the project as string or Path
            
        Returns:
            Path: Path object for the project source directory
        """
        return Path(project_path) if project_path and not isinstance(project_path, Path) else project_path
    
    @classmethod
    def get_project_build_path(cls, app_name, output_path=None):
        """Get the build directory for a project.
        
        Args:
            product_name: Name of the product/project
            output_dir: Optional custom output directory
            
        Returns:
            Path: Path to the project build directory
        """
        if output_path:
            return Path(output_path)
        return cls.get_build_path() / app_name
    
    @classmethod
    def find_files(cls, path, pattern):
        """Find files matching a pattern in a directory.
        
        Args:
            directory: Directory to search in
            pattern: Glob pattern to match
            
        Returns:
            list: List of files found
        """
        return list(Path(path).glob(pattern))
    
    @classmethod
    def find_extension_paths(cls, project_path):
        """Find extension directories in a project.
        
        Args:
            project_dir: Path to the project directory
            
        Returns:
            list: List of extension directories found
        """
        project_path = cls.get_project_source_path(project_path)
        return [d for d in project_path.iterdir() if d.is_dir() and (d / "extensions").exists()]

    @classmethod
    def get_resources_path(cls, project_path, resource_dir_name):
        """Get the resources directory for a project.
        
        Args:
            project_dir: Path to the project directory
            resource_dir_name: Name of the resources subdirectory
            
        Returns:
            Path: Path to the resources directory if it exists, None otherwise
        """
        project_path = cls.get_project_source_path(project_path)
        res_path = project_path / resource_dir_name
        return res_path if res_path.exists() else None

    @classmethod
    def get_spec_path(cls) -> Path:
        """Get the directory containing PyInstaller spec templates.
        
        Returns:
            Path: Path to the spec template directory
        """
        return cls.PROJECT_ROOT / ARES_CHILD_PATH / SPEC_CHILD_PATH
    
    @classmethod
    def get_spec_template(cls, template_name) -> Path:
        """Get the path to a PyInstaller spec template file.
        
        Args:
            template_name: Name of the template file (defaults to exe.spec)
            
        Returns:
            Path: Path to the spec template file
        """
        return cls.get_spec_path() / template_name

    @classmethod
    def get_executable_output_path(cls, build_dir: Path) -> Path:
        """Get the directory where compiled executables should be placed.
        
        Args:
            build_dir: Base build directory for the project
            
        Returns:
            Path: Path to the executable output directory
        """
        path = build_dir / EXECUTABLE_OUTPUT_DIR_NAME
        os.makedirs(path, exist_ok=True)
        return path

    @classmethod
    def get_engine_build_dir(cls) -> Path:
        return cls.PROJECT_ROOT / "build" / "engine"


# Initialize the Paths class to set up directories
Paths._initialize()

# Assign the Paths class to a variable for easier access
paths = Paths
