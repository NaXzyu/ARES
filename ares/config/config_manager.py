"""Configuration file management for runtime applications."""

import os
import sys
import shutil
import platform
import configparser
from pathlib import Path

def get_app_config_dir(app_name=None):
    """Get the appropriate config directory for this application based on platform standards."""
    if app_name is None:
        # Try to detect app name from executable
        if getattr(sys, 'frozen', False):
            app_name = Path(sys.executable).stem
        else:
            app_name = "ares-engine"
    
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

def extract_embedded_configs(app_name=None):
    """Extract config files from the embedded resources to the user config directory."""
    if not getattr(sys, 'frozen', False):
        # Only needed in frozen applications
        return None
    
    # Get appropriate config directory
    config_dir = get_app_config_dir(app_name)
    
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

def get_config_file_path(filename, app_name=None, create_default=True):
    """Get the path to a config file, extracting from embedded resources if needed."""
    config_dir = get_app_config_dir(app_name)
    config_path = config_dir / filename
    
    # If the file doesn't exist and we should create defaults
    if not config_path.exists() and create_default and getattr(sys, 'frozen', False):
        # Check for the file in the embedded resources
        embedded_file = Path(sys._MEIPASS) / "ares" / "ini" / filename
        if embedded_file.exists():
            try:
                shutil.copy2(embedded_file, config_path)
                print(f"Created default config file: {config_path}")
            except Exception as e:
                print(f"Error creating default config file: {e}")
    
    return config_path

def initialize_configuration(app_name=None):
    """Initialize application configuration system.
    
    This should be called early in your application startup.
    It extracts embedded config files and sets up the config paths.
    """
    # Extract configs from embedded resources if in frozen app
    if getattr(sys, 'frozen', False):
        config_dir = extract_embedded_configs(app_name)
        print(f"Application config directory: {config_dir}")
        return config_dir
    
    # For development mode, just use the appropriate directory
    config_dir = get_app_config_dir(app_name)
    print(f"Using development config directory: {config_dir}")
    return config_dir

def load_project_config(project_path):
    """Load project configuration, prioritizing local project.ini if it exists.
    
    Args:
        project_path: Path to the project directory
        
    Returns:
        dict: Dictionary of project configuration values
    """
    from ares.config import initialize, project_config, build_config
    # Initialize default config first
    initialize()
    
    # Check if the project has its own project.ini
    local_project_ini = Path(project_path) / "project.ini"
    
    if local_project_ini.exists():
        print("\n== Using project-specific configuration ==")
        print(f"Location: {local_project_ini}")
        
        # Load the local project.ini
        local_config = configparser.ConfigParser()
        local_config.read(local_project_ini)
        
        # Override the global project_config with local settings
        # We'll return these settings as a dictionary so we don't modify the global config
        config_values = {
            "console": local_config.getboolean("project", "console", fallback=project_config.is_console_enabled()),
            "onefile": local_config.getboolean("project", "onefile", fallback=project_config.is_onefile_enabled()),
            "include_resources": local_config.getboolean("resources", "include_resources", 
                                             fallback=project_config.getboolean("resources", "include_resources", True)),
            "resource_dir_name": local_config.get("resources", "resource_dir_name", 
                                      fallback=project_config.get("resources", "resource_dir_name", "resources")),
            # Get product_name now from build_config instead, but check local project.ini first
            "product_name": (
                local_config.get("package", "product_name", fallback=None) 
                or build_config.get_product_name()
            )
        }
    else:
        print("\n== Using default project configuration ==")
        try:
            # Guard against project_config being None
            config_path = str(project_config.user_path) if project_config and hasattr(project_config, 'user_path') else "global defaults"
            print(f"Location: {config_path}")
        except (AttributeError, TypeError):
            print("Location: <default configuration>")
            
        # Use global settings with safe defaults in case project_config is not fully initialized
        if project_config and build_config:
            config_values = {
                "console": project_config.is_console_enabled(),
                "onefile": project_config.is_onefile_enabled(),
                "include_resources": project_config.getboolean("resources", "include_resources", True),
                "resource_dir_name": project_config.get("resources", "resource_dir_name", "resources"),
                "product_name": build_config.get_product_name()
            }
        else:
            # Even when configs are not initialized, try to use build_config values as fallback defaults
            # This makes the defaults consistent with our INI files
            print("Warning: Project configuration is not initialized. Using default configuration values.")
            try:
                # Try to load basic values from build.ini directly if possible
                from ares.config.config import config
                build_ini = config.load("build")
                fallback_product_name = build_ini.get("package", "product_name", "Ares") if build_ini else "Ares"
            except Exception:
                # If we can't load from build.ini, use hardcoded fallback that matches build.ini default
                fallback_product_name = "Ares"
            
            config_values = {
                "console": True,
                "onefile": True, 
                "include_resources": True,
                "resource_dir_name": "resources",
                "product_name": fallback_product_name
            }
        
    return config_values

def load_build_config(project_path):
    """Load build configuration, checking for project-specific references.
    
    Args:
        project_path: Path to the project directory
        
    Returns:
        ConfigParser object: The loaded build configuration
    """
    from ares.config import initialize, project_config, config
    
    initialize()
    
    # Check if the project has its own project.ini
    local_project_ini = Path(project_path) / "project.ini"
    build_config_file = "build.ini"  # Default
    
    if local_project_ini.exists():
        local_config = configparser.ConfigParser()
        local_config.read(local_project_ini)
        
        # Check for custom build config file
        if local_config.has_option("project", "build_config_file"):
            build_config_file = local_config.get("project", "build_config_file")
    else:
        # Check if project_config is properly initialized
        if project_config is not None and hasattr(project_config, 'get_build_config_file'):
            try:
                build_config_file = project_config.get_build_config_file()
            except (AttributeError, TypeError):
                build_config_file = "build.ini"  # Fallback to default
    
    # Check if the specified build config exists in the project directory
    custom_build_config = Path(project_path) / build_config_file
    if custom_build_config.exists():
        return config.load(custom_build_config.stem)
    
    # Fall back to default build config
    return config.load("build")
