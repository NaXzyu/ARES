#!/usr/bin/env python3
"""Main entry point for Ares Engine CLI commands."""

import sys

def main():
    """Main entry point for CLI command execution.
    
    Returns:
        int: Exit code (0 for success, non-zero for error)
    """
    # Defer imports until they're needed to avoid unnecessary initialization
    from ares.utils import BuildUtils
    from ares.utils.cli.parser import Parser
    
    # Verify Python version
    BuildUtils.verify_python()
    
    # Parse arguments first
    args = Parser.parse_args()
    
    # Only import Router if we need to handle a command
    if args.get('command'):
        from ares.utils.cli.router import Router
        try:
            return Router.route(args)
        except KeyError as e:
            if str(e) == "'dll_path'":
                print("ERROR: SDL2 DLL path configuration is missing.")
                print("Please ensure SDL2 is properly installed and configured in your environment.")
                print("You may need to set the SDL2_PATH environment variable or install the SDL2 development libraries.")
                return 1
            else:
                raise
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
