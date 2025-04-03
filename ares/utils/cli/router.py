#!/usr/bin/env python3
"""Command-line interface for Ares Engine operations."""

class Router:
    """Core CLI functionality handler for Ares Engine."""
    
    @classmethod
    def route(cls, args):
        """Route to the appropriate command handler based on arguments.
        
        Args:
            args: Dictionary of parsed arguments
            
        Returns:
            int: Exit code (0 for success, non-zero for failure)
        """
        command = args.get('command', '')
        
        try:
            # Only import needed command handlers when routing
            if command == 'build':
                from .command.build_cmd import BuildCommand
                return BuildCommand.execute(args)
            elif command == 'clean':
                from .command.clean_cmd import CleanCommand
                return CleanCommand.execute(args)
            else:
                from .parser import Parser
                parser = Parser.create_parser()
                print("\nAvailable commands:")
                print(parser.format_help().split("Examples:")[1])
                return 1
                
        except ImportError as e:
            print(f"Error importing command module: {e}")
            return 1
    
    @classmethod
    def handle(cls, **kwargs):
        """Execute CLI processing with optional keyword arguments.
        
        Args:
            **kwargs: Optional keyword arguments to override command line arguments
            
        Returns:
            int: Exit code (0 for success, non-zero for failure)
        """
        from .parser import Parser
        args = Parser.parse_args()
        
        # Check if any keyword arguments are provided
        if kwargs:
            args.update(kwargs)
            
        return cls.route(args)
