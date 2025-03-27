"""Configuration file management for runtime applications."""

import os
import sys
import shutil
import platform
from pathlib import Path

from .config_types import ConfigType

class ConfigManager:
    """Central class for managing application configurations."""
    
    @classmethod
    def get_app_config_dir(cls, app_name):
        """Get the appropriate config directory for this application based on platform standards.
        
        Args:
            app_name: Name of the application used for organizing config files
            
        Returns:
            Path: Directory where configuration files should be stored
        """
        # Use platform-specific locations
        if platform.system() == "Windows":
            base_dir = os.environ.get("LOCALAPPDATA", 
                         os.path.join(os.environ["USERPROFILE"], "AppData", "Local"))
            config_dir = Path(base_dir) / app_name / "Config"
        elif platform.system() == "Darwin":  # macOS
            config_dir = Path.home() / "Library" / "Application Support" / app_name / "Config"
        else:  # Linux and other Unix-like
            config_dir = Path.home() / ".config" / app_name
        
        # Create directory if it doesn't exist
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir
    
    @classmethod
    def extract_embedded_configs(cls, app_name):
        """Extract config files from the embedded resources to the user config directory."""
        if not getattr(sys, 'frozen', False):
            # Only needed in frozen applications
            return None
        
        # Get appropriate config directory
        config_dir = cls.get_app_config_dir(app_name)
        
        # Source directory in PyInstaller bundle
        meipass = Path(sys._MEIPASS)
        source_ini_dir = meipass / "ares" / "ini"
        
        # Check if source directory exists
        if not source_ini_dir.exists():
            print(f"Warning: No embedded config files found at {source_ini_dir}")
            return config_dir
        
        # Copy all INI files, don't overwrite existing ones
        for ini_file in source_ini_dir.glob("*.ini"):
            target_path = config_dir / ini_file.name
            
            # Only copy if target doesn't exist to preserve user modifications
            if not target_path.exists():
                try:
                    shutil.copy2(ini_file, target_path)
                    print(f"Extracted config file: {ini_file.name} -> {target_path}")
                except Exception as e:
                    print(f"Error extracting config file {ini_file.name}: {e}")
        
        return config_dir

    @classmethod
    def get_config_file_path(cls, filename, app_name, create_default=True):
        """Get the path to a config file, extracting from embedded resources if needed."""
        config_dir = cls.get_app_config_dir(app_name)
        config_path = config_dir / filename
        
        # If the file doesn't exist and we should create defaults
        if not config_path.exists() and create_default and getattr(sys, 'frozen', False):
            # Get embedded file path using Paths utility
            from ares.utils.paths import Paths
            embedded_file = Paths.get_embedded_ini_file(filename)
            if embedded_file.exists():
                from ares.utils.utils import copy_file_with_logging
                copy_file_with_logging(embedded_file, config_path)
        
        return config_path

    @classmethod
    def initialize_configuration(cls, app_name):
        """Initialize application configuration system.
        
        This should be called early in your application startup.
        It extracts embedded config files and sets up the config paths.
        """
        # Extract configs from embedded resources if in frozen app
        if getattr(sys, 'frozen', False):
            config_dir = cls.extract_embedded_configs(app_name)
            print(f"Application config directory: {config_dir}")
            return config_dir
        
        # For development mode, just use the appropriate directory
        config_dir = cls.get_app_config_dir(app_name)
        print(f"Using development config directory: {config_dir}")
        return config_dir

    @classmethod
    def get_config_objects(cls):
        """Get a dictionary of all available configuration objects.
        
        Returns:
            dict: Dictionary mapping config names to their respective objects
        """
        from ares.config import initialize
        from ares.config import engine_config, build_config, project_config, package_config, compiler_config, assets_config, logging_config
        
        # Initialize all configs first
        initialize()
        
        # Map of config objects by name
        return {
            ConfigType.ENGINE.value: engine_config,
            ConfigType.BUILD.value: build_config,
            ConfigType.PROJECT.value: project_config,
            ConfigType.PACKAGE.value: package_config, 
            ConfigType.COMPILER.value: compiler_config,
            ConfigType.ASSETS.value: assets_config,
            ConfigType.LOGGING.value: logging_config
        }

    @classmethod
    def load_config(cls, config_type, project_path):
        """Load a specific configuration type with project-specific overrides.
        
        Args:
            config_type: ConfigType enum value specifying which config to load
            project_path: Path to the project directory containing override INI files
            
        Returns:
            object: The loaded configuration object with any overrides applied
            
        Raises:
            TypeError: If config_type is not a ConfigType enum
            ValueError: If the specified config_type is not recognized
        """
        # Ensure config_type is a ConfigType enum
        if not isinstance(config_type, ConfigType):
            raise TypeError(f"config_type must be a ConfigType enum, got {type(config_type).__name__}")
            
        # Get all config objects
        config_objects = cls.get_config_objects()
        
        # Get the config type value for dictionary lookup
        config_type_value = config_type.value
        
        # Validate config type
        if config_type_value not in config_objects:
            valid_types = ', '.join([str(ct) for ct in ConfigType])
            raise ValueError(f"Unknown configuration type: {config_type}. Valid types are: {valid_types}")
        
        # Get the requested config object
        config_obj = config_objects[config_type_value]
        
        # Apply project-specific overrides if they exist
        project_path = Path(project_path)
        config_ini = project_path / f"{config_type_value}.ini"
        
        if config_ini.exists():
            override_info = config_obj.load_overrides(config_ini)
            if override_info["overridden"]:
                print(f"Applied {config_type} configuration overrides from {config_ini}")
        
        return config_obj
    
    @classmethod
    def load_all_configs(cls, project_path):
        """Load all configuration types with project-specific overrides.
        
        Args:
            project_path: Path to the project directory containing override INI files
            
        Returns:
            dict: Dictionary mapping config types to their respective loaded objects
        """
        configs = {}
        for config_type in ConfigType:
            configs[config_type] = cls.load_config(config_type, project_path)
            
        # Automatically set loaded configs as global configs
        from ares.config import set_global_configs
        set_global_configs(configs)
        
        return configs

