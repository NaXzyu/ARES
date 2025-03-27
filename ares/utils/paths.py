"""
Path management utilities for Ares Engine.
"""

import os
import sys
from pathlib import Path

from ares.utils.constants import CURRENT_PLATFORM

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
    def get_user_data_dirs(cls):
        """Get user data directories based on platform."""
        app_name = cls.get_app_name()
        
        # Determine base directory based on runtime mode and platform
        if cls.IS_FROZEN:
            # In frozen mode, store logs next to the executable
            base_dir = cls.APP_DIR
        else:
            # For development mode, use platform-specific directories
            if sys.platform.startswith("win"):
                try:
                    base_dir = Path(os.environ.get('LOCALAPPDATA', str(Path.home() / "AppData" / "Local")))
                    base_dir = base_dir / app_name / "Saved"
                except (KeyError, TypeError):
                    base_dir = Path.home() / "AppData" / "Local" / app_name / "Saved"
            elif sys.platform.startswith("darwin"):
                base_dir = Path.home() / "Library" / "Application Support" / app_name / "Saved"
            else:
                try:
                    import appdirs
                    base_dir = Path(appdirs.user_data_dir("ares-engine", app_name)) / "Saved"
                except ImportError:
                    base_dir = Path.home() / ".local" / "share" / "ares-engine" / "Saved"
        
        # Create standard subdirectories based on the determined base directory
        return {
            "USER_DATA_DIR": base_dir,
            "USER_CONFIG_DIR": base_dir / "Config" / CURRENT_PLATFORM,
            "USER_LOGS_DIR": base_dir / "Logs",
            "USER_SCREENSHOTS_DIR": base_dir / "Screenshots",
            "USER_SAVES_DIR": base_dir / "SaveGames"
        }

    @classmethod
    def create_directories(cls):
        """Create all required directories."""
        dirs = cls.get_user_data_dirs()
        for directory in dirs.values():
            try:
                os.makedirs(directory, exist_ok=True)
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
    def get_runtime_log_file(cls):
        """Get the path to the runtime log file."""
        if cls.IS_FROZEN:
            # For runtime, use product name from project config
            app_name = cls.get_app_name()
            return cls.get_user_data_dirs()["USER_LOGS_DIR"] / f"{app_name}.log"
        else:
            # For development, use engine.log
            return cls.get_user_data_dirs()["USER_LOGS_DIR"] / "engine.log"
    
    @classmethod
    def get_build_log_file(cls):
        """Get the path to the build log file."""
        return cls.get_user_data_dirs()["USER_LOGS_DIR"] / "build.log"


# Initialize paths
paths = Paths()
user_dirs = paths.create_directories()

# Export commonly used paths
IS_FROZEN = Paths.IS_FROZEN
PROJECT_ROOT = Paths.PROJECT_ROOT
USER_DATA_DIR = user_dirs["USER_DATA_DIR"]
USER_CONFIG_DIR = user_dirs["USER_CONFIG_DIR"]
USER_LOGS_DIR = user_dirs["USER_LOGS_DIR"]
USER_SCREENSHOTS_DIR = user_dirs["USER_SCREENSHOTS_DIR"]
USER_SAVES_DIR = user_dirs["USER_SAVES_DIR"]
