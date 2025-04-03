"""CLI package initialization module."""

# Define what this module exports
__all__ = [
    'Parser',
    'Router',
    'Command', 
    'CommandType',
    'get_main_help',
    'get_command_help'
]

# Only import what's needed at import time - don't import command implementations
from .parser import Parser
from .router import Router
from .command.command import Command
from .command.cmd_type import CommandType
from .help import get_main_help, get_command_help