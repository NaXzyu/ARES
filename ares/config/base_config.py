"""Base configuration classes for Ares Engine."""

import os
import configparser
from pathlib import Path

# Use the function instead of direct import to avoid circular dependencies
from ares.utils.paths import get_user_config_dir

class BaseConfig:
    """Base configuration class used by specialized config classes."""
    
    def __init__(self, config_name, section="DEFAULT"):
        """Initialize with config file name and section.
        
        Args:
            config_name: Name of configuration (used for filename without .ini)
            section: Section name in the INI file (default: DEFAULT)
        """
        # Get user config directory using the function
        self.config_dir = get_user_config_dir()
        os.makedirs(self.config_dir, exist_ok=True)
        
        self.config_name = config_name
        self.config_file = self.config_dir / f"{config_name}.ini"
        self.section = section
        self.parser = configparser.ConfigParser()
        self.loaded = False
        
    def ensure_section_exists(self):
        """Ensure the section exists in the config parser."""
        if not self.section in self.parser:
            self.parser[self.section] = {}
        
    def load(self):
        """Load configuration from file."""
        self.ensure_section_exists()
            
        # Try to load from file if it exists
        if self.config_file.exists():
            try:
                self.parser.read(self.config_file)
                self.loaded = True
                return True
            except configparser.Error:
                print(f"Warning: Could not parse config file {self.config_file}")
                return False
        
        self.loaded = True
        return True  # Return success even if file doesn't exist
                    
    def save(self):
        """Save configuration to file."""
        self.ensure_section_exists()
        
        try:
            os.makedirs(self.config_dir, exist_ok=True)
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
        if not self.loaded:
            self.load()
            
        section = section or self.section
        
        if section in self.parser and key in self.parser[section]:
            return self.parser[section][key]
        
        return default
        
    def get_bool(self, key, default=False, section=None):
        """Get a boolean configuration value.
        
        Args:
            key: Configuration key to retrieve
            default: Default boolean to return if key not found
            section: Section to look in (defaults to self.section)
            
        Returns:
            bool: Configuration value as boolean
        """
        value = self.get(key, str(default), section)
        return value.lower() in ('true', 'yes', 'y', '1', 'on', 't')
        
    def get_int(self, key, default=0, section=None):
        """Get an integer configuration value.
        
        Args:
            key: Configuration key to retrieve
            default: Default integer to return if key not found
            section: Section to look in (defaults to self.section)
            
        Returns:
            int: Configuration value as integer
        """
        try:
            return int(self.get(key, default, section))
        except ValueError:
            return default
        
    def get_float(self, key, default=0.0, section=None):
        """Get a float configuration value.
        
        Args:
            key: Configuration key to retrieve
            default: Default float to return if key not found
            section: Section to look in (defaults to self.section)
            
        Returns:
            float: Configuration value as float
        """
        try:
            return float(self.get(key, default, section))
        except ValueError:
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
        if not self.loaded:
            self.load()
            
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
        if not self.loaded:
            self.load()
            
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
        if not self.loaded:
            self.load()
            
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
