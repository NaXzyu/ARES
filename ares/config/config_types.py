"""Configuration type definitions for the Ares Engine."""

from enum import Enum

class ConfigType(Enum):
    """Enum representing different configuration types."""
    ENGINE = "engine"
    BUILD = "build"
    PROJECT = "project"
    LOGGING = "logging"
    PACKAGE = "package" 
    COMPILER = "compiler"
    ASSETS = "assets"
    
    def __str__(self):
        """Return the string value of the enum."""
        return self.value
