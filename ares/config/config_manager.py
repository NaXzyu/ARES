"""Configuration file management for runtime applications."""

import os
import sys
import shutil
import platform
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
