#!/usr/bin/env python3
"""Command-line argument parsing for Ares Engine CLI."""

import sys
import argparse
from .help import get_main_help, get_command_help

class Parser:
    """Parser for Ares Engine CLI arguments."""
    
    @classmethod
    def create_parser(cls):
        """Create the argument parser for the CLI.
        
        Returns:
            argparse.ArgumentParser: Configured argument parser
        """
        parser = argparse.ArgumentParser(
            description="Ares Engine CLI Utility",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            usage="ares [command] [options]",
            add_help=False  # We'll handle help ourselves
        )
        
        # Add help option manually
        parser.add_argument('-h', '--help', action='store_true', 
                          help='Show this help message and exit')
        
        # Create subparsers for different commands
        subparsers = parser.add_subparsers(dest='command', help='Command to execute')
        
        # Build command
        build_parser = subparsers.add_parser('build', help='Build the engine or a project', add_help=False)
        build_parser.add_argument('-h', '--help', action='store_true', help='Show build command help')
        build_parser.add_argument('project_path', nargs='?', default='engine', 
                                help='Path to project directory (defaults to engine)')
        build_parser.add_argument('--force', action='store_true', 
                                help='Force rebuilding all Cython modules and packages')
        build_parser.add_argument('--python', type=str, 
                                help='Path to specific Python interpreter to use (must be 3.12+)')
        
        # Clean command
        clean_parser = subparsers.add_parser('clean', help='Clean build artifacts', add_help=False)
        clean_parser.add_argument('-h', '--help', action='store_true', help='Show clean command help')
        
        return parser
    
    @classmethod
    def parse_args(cls, args=None):
        """Parse command line arguments.
        
        Args:
            args: Optional list of arguments to parse (defaults to sys.argv)
            
        Returns:
            dict: Dictionary of parsed arguments
        """
        parser = cls.create_parser()
        
        # Handle empty arguments - show main help
        if args is None and len(sys.argv) == 1:
            print(get_main_help())
            sys.exit(1)
        
        # Parse arguments but catch help requests
        parsed_args, unknown = parser.parse_known_args(args)
        parsed_dict = vars(parsed_args)
        
        # Handle help for specific commands
        if parsed_dict.get('help'):
            print(get_command_help(parsed_dict.get('command')))
            sys.exit(0)
            
        # Check for unknown arguments
        if unknown:
            print(f"Unknown arguments: {' '.join(unknown)}")
            print(get_command_help(parsed_dict.get('command')))
            sys.exit(1)
            
        return parsed_dict
