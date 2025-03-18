"""
Base configuration class that other configuration classes inherit from.
"""

from .config import config
from . import USER_CONFIG_DIR

class BaseConfig:

    def __init__(self, config_name="config"):
        self.config_name = config_name
        self.user_path = USER_CONFIG_DIR / f"{config_name}.ini"
        self.config = config.load(self.config_name)
    
    def load(self):
        """Load configuration. Called for explicit reloading."""
        self.config = config.load(self.config_name)
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
