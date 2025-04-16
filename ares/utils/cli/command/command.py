"""Abstract base class for Ares CLI commands."""

from abc import ABC, abstractmethod
from typing import Any, Dict

from .cmd_type import CommandType

class Command(ABC):
    """Abstract base class for all CLI commands."""
    
    @classmethod
    @abstractmethod
    def get_command_type(cls) -> CommandType:
        """Get the type of this command.
        
        Returns:
            CommandType: The type of command
        """
        pass
    
    @classmethod
    @abstractmethod
    def execute(cls, args: Dict[str, Any]) -> int:
        """Execute the command.
        
        Args:
            args: Dictionary of command arguments
            
        Returns:
            int: Exit code (0 for success, non-zero for failure)
        """
        pass
