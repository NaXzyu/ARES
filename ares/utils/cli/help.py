"""Help text and formatting for Ares Engine CLI."""

# Main description displayed at the top
DESCRIPTION = """Ares Engine CLI utility for building and managing projects."""

USAGE = "ares [command] [options]"

# Command descriptions with detailed formatting
COMMANDS = """
Commands:
  build                   Build the engine or a project
  clean                   Clean up build artifacts
"""

# Options for commands with netstat-style formatting
BUILD_OPTIONS = """
Build options:
  project_path          Path to project directory (defaults to engine)
  --force               Force rebuilding all Cython modules and packages
  --python <path>       Path to specific Python interpreter to use (must be 3.12+)
"""

CLEAN_OPTIONS = """
Clean options:
  No additional options
"""

# Examples section formatted like netstat help
EXAMPLES = """
Examples:
  ares build                       Build only the engine package
  ares build path/to/project       Build a project from specified path
  ares clean                       Clean up build artifacts
  ares build --force               Force rebuild all Cython modules and packages
  ares build --python path/to/python     Use specific Python interpreter
"""

def get_main_help():
    """Get the main help text for the CLI."""
    # Added a newline at the beginning to ensure a blank line appears before the first line of output
    return f"\n{DESCRIPTION}\n\nUsage: {USAGE}\n{COMMANDS}\n{EXAMPLES}"

def get_command_help(command):
    """Get help text for a specific command."""
    if command == "build":
        # Add newline at the beginning for command help as well
        return f"\n{DESCRIPTION}\n\nUsage: ares build [project_path] [options]\n{BUILD_OPTIONS}\n{EXAMPLES}"
    elif command == "clean":
        # Add newline at the beginning for command help as well
        return f"\n{DESCRIPTION}\n\nUsage: ares clean\n{CLEAN_OPTIONS}\n{EXAMPLES}"
    else:
        return get_main_help()
