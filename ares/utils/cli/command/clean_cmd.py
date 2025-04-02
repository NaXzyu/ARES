"""Clean command implementation for Ares Engine CLI."""

from typing import Any, Dict

from ares.utils.build.build_cleaner import BuildCleaner
from ares.utils.const import ERROR_RUNTIME, SUCCESS
from ares.utils.log import log
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
        try:
            log.info("Starting clean operation...")
            BuildCleaner.clean_project() 
            log.info("Clean operation completed successfully")
            return SUCCESS
        except Exception as e:
            log.error(f"Error cleaning project: {e}")
            return ERROR_RUNTIME
