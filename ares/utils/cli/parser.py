#!/usr/bin/env python3
"""Command-line argument parsing for Ares Engine CLI."""

import sys
import argparse

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
            epilog="""
Examples:
  ares build                       Build only the engine package
  ares build path/to/project       Build a project from specified path
  ares clean                       Clean up build artifacts
  ares build --force               Force rebuild all Cython modules and packages
  ares build --python path/to/python     Use specific Python interpreter (must be 3.12+)
"""
        )
        # Create subparsers for different commands
        subparsers = parser.add_subparsers(dest='command', help='Command to execute')
        
        # Build command
        build_parser = subparsers.add_parser('build', help='Build the engine or a project')
        build_parser.add_argument('project_path', nargs='?', default='engine', 
                                help='Path to project directory (defaults to engine)')
        build_parser.add_argument('--force', action='store_true', 
                                help='Force rebuilding all Cython modules and packages')
        build_parser.add_argument('--python', type=str, 
                                help='Path to specific Python interpreter to use (must be 3.12+)')
        
        # Clean command
        clean_parser = subparsers.add_parser('clean', help='Clean build artifacts')
        
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
        
        # Default to help if no command specified
        if args is None and len(sys.argv) == 1:
            parser.print_help()
            sys.exit(1)
            
        parsed_args = parser.parse_args(args)
        return vars(parsed_args)
