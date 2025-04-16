"""Help text and formatting for Ares Engine CLI."""

# Main description displayed at the top
DESCRIPTION = """Ares Engine CLI utility for building and managing projects."""

USAGE = "ares [command] [options]"

# Command descriptions with detailed formatting
COMMANDS = """
Commands:
  build <engine|path>     Build the engine or a project
  clean                   Clean up build artifacts
"""

# Build command options
BUILD_OPTIONS = """
Build options:
  project_path          Path to project directory (defaults to engine)
  --force               Force rebuilding all Cython modules and packages
  --python <path>       Path to specific Python interpreter to use (must be 3.12+)
"""

# Clean command options
CLEAN_OPTIONS = """
Clean options:
  No additional options
"""

# Help text for the CLI
EXAMPLES = """
Examples:
  ares build engine             Build only the engine package
  ares build <path>             Build a project from specified path
  ares build --force            Force rebuild all Cython modules and packages
  ares build --python <path>    Use specific Python interpreter
  ares clean                    Clean up build artifacts
"""

def get_main_help():
    """Get the main help text for the CLI."""
    return f"\n{DESCRIPTION}\n\nUsage: {USAGE}\n{COMMANDS}\n{EXAMPLES}"

def get_command_help(command):
    """Get help text for a specific command."""
    if command == "build":
        return f"\n{DESCRIPTION}\n\nUsage: ares build [project_path] [options]\n{BUILD_OPTIONS}\n{EXAMPLES}"
    elif command == "clean":
        return f"\n{DESCRIPTION}\n\nUsage: ares clean\n{CLEAN_OPTIONS}\n{EXAMPLES}"
    else:
        return get_main_help()
