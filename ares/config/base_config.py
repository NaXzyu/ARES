"""Base configuration class that other configuration classes inherit from."""

import abc
import configparser
from pathlib import Path
from .config import config
from ares.utils.paths import USER_CONFIG_DIR

class BaseConfig(abc.ABC):
    """Abstract base class for all configuration objects."""

    def __init__(self, config_name="config"):
        self.config_name = config_name
        self.user_path = USER_CONFIG_DIR / f"{config_name}.ini"
        self.config = config.load(self.config_name)
    
    def load(self, override_path=None):
        """Load configuration. Called for explicit reloading.
        
        Args:
            override_path: Optional path to an override INI file
            
        Returns:
            bool: True if load was successful
        """
        self.config = config.load(self.config_name)
        
        # Apply overrides if provided
        if override_path:
            self.load_overrides(override_path)
            
        return True
    
    def save(self):
        """Save the current configuration to file."""
        if self.config:
            config.save(self.config_name, self.config)
        return True
    
    def get(self, section, option, fallback=None):
        """Get a string value from the configuration."""
        return self.config.get(section, option, fallback=fallback)
    
    def getint(self, section, option, fallback=None):
        """Get an integer value from the configuration."""
        return self.config.getint(section, option, fallback=fallback)
    
    def getfloat(self, section, option, fallback=None):
        """Get a float value from the configuration."""
        return self.config.getfloat(section, option, fallback=fallback)
    
    def getboolean(self, section, option, fallback=None):
        """Get a boolean value from the configuration."""
        return self.config.getboolean(section, option, fallback=fallback)
    
    def set(self, section, option, value):
        """Set a configuration value."""
        if not self.config.has_section(section):
            self.config.add_section(section)
        
        self.config.set(section, option, str(value))
        return True
        
    def load_overrides(self, override_file_path):
        """Load and apply configuration overrides from a specific file.
        
        Args:
            override_file_path: Path to the INI file with override values
            
        Returns:
            dict: Information about which sections/options were overridden
        """
        override_file_path = Path(override_file_path)
        if not override_file_path.exists():
            return {"overridden": False}
            
        # Load the override file
        override_config = configparser.ConfigParser()
        override_config.read(override_file_path)
        
        # Track what was overridden
        overrides = {
            "overridden": False,
            "file": str(override_file_path),
            "sections": {}
        }
        
        # Apply overrides
        for section in override_config.sections():
            if not self.config.has_section(section):
                self.config.add_section(section)
                overrides["sections"][section] = {"added": True, "options": []}
            else:
                overrides["sections"][section] = {"added": False, "options": []}
                
            for option in override_config[section]:
                value = override_config[section][option]
                self.config.set(section, option, value)
                overrides["sections"][section]["options"].append(option)
                overrides["overridden"] = True
                
        return overrides
    
    @abc.abstractmethod
    def get_override_dict(self):
        """Get dictionary of important configuration values for this config.
        
        This method must be implemented by subclasses to provide the 
        most important values from their configuration for use in other contexts.
        
        Returns:
            dict: Dictionary of key configuration values
        """
        pass
        
    @abc.abstractmethod
    def initialize(self, *args, **kwargs):
        """Initialize this configuration with any necessary setup.
        
        This method must be implemented by subclasses to provide
        configuration-specific initialization.
        
        Args:
            *args: Variable positional arguments for implementation-specific use
            **kwargs: Variable keyword arguments for implementation-specific use
            
        Returns:
            bool: True if initialization was successful
        """
        pass
