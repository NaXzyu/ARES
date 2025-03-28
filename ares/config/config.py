"""Base configuration management class and utilities."""

import os
import configparser
from pathlib import Path

from ares.utils.paths import get_user_config_dir

class Config:
    """Base configuration class for the Ares Engine.
    
    This provides standard methods for loading, saving, and managing configuration files.
    """
    
    def __init__(self, config_name="config", section="DEFAULT"):
        """Initialize the configuration.
        
        Args:
            config_name: Base name for the config file (without .ini)
            section: Default section to use in the INI file
        """
        # Get user configuration directory
        self.config_dir = get_user_config_dir()
        os.makedirs(self.config_dir, exist_ok=True)
        
        self.config_name = config_name
        self.config_file = self.config_dir / f"{config_name}.ini"
        self.section = section
        self.parser = configparser.ConfigParser()
        
        # Load initial configuration if available
        self.load()
    
    def load(self):
        """Load configuration from file."""
        # Always ensure section exists
        if not self.section in self.parser:
            self.parser[self.section] = {}
            
        # Try to load from file if it exists
        if self.config_file.exists():
            try:
                self.parser.read(self.config_file)
                return True
            except configparser.Error:
                print(f"Warning: Could not parse config file {self.config_file}")
                return False
        
        return True  # Return success even if file doesn't exist
                    
    def save(self):
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w') as config_file:
                self.parser.write(config_file)
            return True
        except (OSError, PermissionError) as e:
            print(f"Error saving config to {self.config_file}: {e}")
            return False
    
    def get(self, key, default=None, section=None):
        """Get a configuration value.
        
        Args:
            key: Configuration key to retrieve
            default: Default value to return if key not found
            section: Section to look in (defaults to self.section)
            
        Returns:
            Configuration value or default if not found
        """
        section = section or self.section
        
        if section in self.parser and key in self.parser[section]:
            return self.parser[section][key]
        
        return default
        
    def set(self, key, value, section=None):
        """Set a configuration value.
        
        Args:
            key: Configuration key to set
            value: Value to set
            section: Section to use (defaults to self.section)
            
        Returns:
            bool: Whether the value was set successfully
        """
        section = section or self.section
        
        # Ensure section exists
        if not section in self.parser:
            self.parser[section] = {}
            
        # Store value as string
        self.parser[section][key] = str(value)
        return True
        
    def get_section(self, section=None):
        """Get all key-value pairs in a section.
        
        Args:
            section: Section name (defaults to self.section)
            
        Returns:
            dict: Dictionary of key-value pairs in the section
        """
        section = section or self.section
        
        if section in self.parser:
            return dict(self.parser[section])
        
        return {}
        
    def load_overrides(self, filename):
        """Load configuration overrides from an external file.
        
        Args:
            filename: Path to the override file
            
        Returns:
            dict: Dictionary containing:
                - "overridden": bool indicating if any values were overridden
                - "section": name of the section that was overridden
                - "values": dictionary of overridden values
        """
        result = {
            "overridden": False,
            "section": self.section,
            "values": {}
        }
        
        if not Path(filename).exists():
            return result
            
        # Create a new parser for the override file
        override_parser = configparser.ConfigParser()
        try:
            override_parser.read(filename)
        except configparser.Error:
            return result
            
        # Check if our section exists
        if not self.section in override_parser:
            return result
            
        # Apply overrides
        for key, value in override_parser[self.section].items():
            old_value = self.get(key)
            self.set(key, value)
            if old_value != value:
                result["overridden"] = True
                result["values"][key] = value
                
        return result
            

# Create a global config instance
config = Config()

def get_config():
    """Get the global configuration instance."""
    return config