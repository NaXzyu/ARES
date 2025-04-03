#!/usr/bin/env python3
"""Main entry point for Ares Engine CLI commands."""

import sys

def main():
    """Main entry point for CLI command execution.
    
    Returns:
        int: Exit code (0 for success, non-zero for error)
    """
    # Defer imports until they're needed to avoid unnecessary initialization
    from ares.utils.utils import verify_python
    from ares.utils.cli.parser import Parser
    
    # Verify Python version
    verify_python()
    
    # Parse arguments first
    args = Parser.parse_args()
    
    # Only import Router if we need to handle a command
    if args.get('command'):
        from ares.utils.cli.router import Router
        return Router.route(args)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
