"""Command type enumeration for Ares CLI."""

from enum import Enum, auto

class CommandType(Enum):
    """Enum for available CLI commands."""
    BUILD = auto()
    CLEAN = auto()
    
    def __str__(self):
        """Return lowercase command name for CLI usage."""
        return self.name.lower()
