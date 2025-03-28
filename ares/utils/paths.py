"""
Path management utilities for Ares Engine.
"""

import os
import sys
from pathlib import Path

class Paths:
    """Central class for managing all engine paths."""
    
    # Track if we're running in frozen mode (PyInstaller executable)
    IS_FROZEN = getattr(sys, 'frozen', False)
    
    # Base directories
    PROJECT_ROOT = Path(sys._MEIPASS) if IS_FROZEN else Path(__file__).resolve().parents[2]
    APP_DIR = Path(sys.executable).parent if IS_FROZEN else PROJECT_ROOT
    
    @classmethod
    def get_app_name(cls):
        """Get application name from project config or use default."""
        try:
            # Import here to avoid circular imports
            from ares.config.project_config import ProjectConfig
            project_config = ProjectConfig()
            return project_config.get_product_name()
        except (ImportError, AttributeError):
            # Fallback to executable name or default
            if cls.IS_FROZEN:
                return Path(sys.executable).stem
            else:
                return "AresEngine"
    
    @classmethod
    def get_user_data_dirs(cls, app_name=None):
        """Get user data directories based on platform.
        
        Args:
            app_name: Optional app name override (defaults to auto-detected app name)
            
        Returns:
            dict: Dictionary containing paths for different user data purposes
        """
        if app_name is None:
            app_name = cls.get_app_name()
        
        # Determine base directory based on platform
        if sys.platform.startswith("win"):
            try:
                base_dir = Path(os.environ.get('LOCALAPPDATA', str(Path.home() / "AppData" / "Local")))
                base_dir = base_dir / app_name
            except (KeyError, TypeError):
                base_dir = Path.home() / "AppData" / "Local" / app_name
        elif sys.platform.startswith("darwin"):
            base_dir = Path.home() / "Library" / "Application Support" / app_name
        else:
            try:
                import appdirs
                base_dir = Path(appdirs.user_data_dir("ares-engine", app_name))
            except ImportError:
                base_dir = Path.home() / ".local" / "share" / "ares-engine" / app_name
        
        # Create standard subdirectories based on the determined base directory
        return {
            "BASE_DIR": base_dir,
            "CONFIG_DIR": base_dir / "Config",
            "LOGS_DIR": base_dir / "Logs",
            "SCREENSHOTS_DIR": base_dir / "Screenshots",
            "SAVES_DIR": base_dir / "SaveGames",
            "CACHE_DIR": base_dir / "Cache"
        }

    @classmethod
    def get_project_dirs(cls):
        """Get directories for development and build operations in the project.
        
        Returns:
            dict: Dictionary containing paths for project-related directories
        """
        return {
            "PROJECT_ROOT": cls.PROJECT_ROOT,
            "APP_DIR": cls.APP_DIR,
            "BUILD_DIR": cls.PROJECT_ROOT / "build",
            "DEV_LOGS_DIR": cls.PROJECT_ROOT / "logs",
            "ENGINE_BUILD_DIR": cls.PROJECT_ROOT / "build" / "engine",
            "CACHE_DIR": cls.PROJECT_ROOT / "build" / "cache"
        }

    @classmethod
    def create_app_directories(cls, app_name=None):
        """Create all required app data directories.
        
        Args:
            app_name: Optional app name override
            
        Returns:
            dict: Dictionary of created directories
        """
        dirs = cls.get_user_data_dirs(app_name)
        for directory in dirs.values():
            try:
                os.makedirs(directory, exist_ok=True)
            except (OSError, PermissionError):
                # Silently continue if we can't create directories
                pass
        return dirs
        
    @classmethod
    def create_project_directories(cls):
        """Create all required project directories.
        
        Returns:
            dict: Dictionary of created directories
        """
        dirs = cls.get_project_dirs()
        # Only create these specific directories
        create_keys = ["BUILD_DIR", "DEV_LOGS_DIR", "ENGINE_BUILD_DIR", "CACHE_DIR"]
        for key in create_keys:
            try:
                os.makedirs(dirs[key], exist_ok=True)
            except (OSError, PermissionError):
                # Silently continue if we can't create directories
                pass
        return dirs

    @classmethod
    def get_ini_dir(cls):
        """Get the directory containing INI configuration files."""
        if cls.IS_FROZEN:
            return Path(sys._MEIPASS) / "ares" / "ini" 
        else:
            return cls.PROJECT_ROOT / "ares" / "ini"
    
    @classmethod
    def get_embedded_ini_file(cls, filename):
        """Get path to an embedded INI file in frozen applications.
        
        Args:
            filename: Name of the INI file to locate
            
        Returns:
            Path: Path to the INI file in the frozen app or development tree
        """
        return cls.get_ini_dir() / filename
    
    @classmethod
    def get_logs_dir(cls, for_app=True, app_name=None):
        """Get the appropriate logs directory (app or project).
        
        Args:
            for_app: True to get app logs dir, False to get project logs dir
            app_name: Optional app name for app logs dir
        
        Returns:
            Path: Path to appropriate logs directory
        """
        if for_app and cls.IS_FROZEN:
            # For runtime frozen apps, use the app logs directory
            return cls.get_user_data_dirs(app_name)["LOGS_DIR"]
        else:
            # For development or build logs, use project logs directory
            return cls.get_project_dirs()["DEV_LOGS_DIR"]
    
    @classmethod
    def get_log_file(cls, filename, for_app=True, app_name=None):
        """Get the path to a specific log file.
        
        Args:
            filename: Name of the log file
            for_app: True to use app logs dir, False to use project logs dir
            app_name: Optional app name for app logs
            
        Returns:
            Path: Path to the log file
        """
        return cls.get_logs_dir(for_app, app_name) / filename
    
    @classmethod
    def get_runtime_log_file(cls, app_name=None):
        """Get the path to the runtime log file."""
        if cls.IS_FROZEN:
            # For runtime, use app name and app logs directory
            app_name = app_name or cls.get_app_name()
            return cls.get_log_file(f"{app_name}.log", True, app_name)
        else:
            # For development, use engine.log in project logs directory
            return cls.get_log_file("engine.log", False)
    
    @classmethod
    def get_build_log_file(cls):
        """Get the path to the build log file.
        Always use project logs directory for build logs.
        """
        return cls.get_log_file("build.log", False)

    # This function avoids circular imports by not importing from config module directly
    @classmethod
    def get_user_config_dir(cls):
        """Get the user config directory without risking circular imports."""
        dirs = cls.get_user_data_dirs("AresEngine")  # Use hardcoded default app name instead of get_app_name
        return dirs["CONFIG_DIR"]

# Expose the USER_CONFIG_DIR safely - defer the actual creation
def get_user_config_dir():
    """Get the user config directory, creating it if needed."""
    config_dir = Paths.get_user_config_dir()
    os.makedirs(config_dir, exist_ok=True)
    return config_dir

# Only export the function, not a concrete value to avoid circular imports
__all__ = ['Paths', 'get_user_config_dir']
