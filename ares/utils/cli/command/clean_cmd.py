"""Clean command implementation for Ares Engine CLI."""

from typing import Any, Dict
from .cmd_type import CommandType
from .command import Command

class CleanCommand(Command):
    """Command for cleaning build artifacts."""
    
    @classmethod
    def get_command_type(cls) -> CommandType:
        """Get the type of this command."""
        return CommandType.CLEAN
    
    @classmethod
    def execute(cls, args: Dict[str, Any]) -> int:
        """Execute the clean command."""
        # Only import heavy modules when executing the command
        try:
            from ares.utils.build.build_cleaner import BuildCleaner
            from ares.utils.const import ERROR_RUNTIME, SUCCESS
            
            # Simple log output that doesn't require full logging initialization
            print("Starting clean operation...")
            
            BuildCleaner.clean_project()
            
            print("Clean operation completed successfully")
            return SUCCESS
        except Exception as e:
            print(f"Error cleaning project: {e}")
            return ERROR_RUNTIME
