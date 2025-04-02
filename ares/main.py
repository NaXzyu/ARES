#!/usr/bin/env python3
"""Main entry point for Ares Engine CLI commands."""

import sys

from ares.utils.cli.router import Router
from ares.utils.utils import verify_python

if __name__ == "__main__":
    
    # Verify Python version
    verify_python()
    
    # Route to the appropriate command handler
    sys.exit(Router.handle())
