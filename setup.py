#!/usr/bin/env python3
"""Ares Engine setup script for environment setup and package installation."""

import os
import sys
import subprocess
import argparse
import re
from pathlib import Path
from setuptools import setup, find_packages

# Add project root to path to ensure all imports work
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# Define minimal constants needed to bootstrap
VENV_DIR = PROJECT_ROOT / ".venv"
BUILD_SCRIPT = PROJECT_ROOT / "ares" / "build" / "build_engine.py"
BUILD_DIR = PROJECT_ROOT / "build"
ENGINE_BUILD_DIR = BUILD_DIR / "engine"
LOGS_DIR = PROJECT_ROOT / "logs"

# Initialize metadata with defaults
METADATA = {
    "name": "ares",
    "version": "0.1.0",
    "description": "A cross-platform game engine with Cython acceleration",
    "author": "k. rawson",
    "author_email": "rawsonkara@gmail.com",
    "url": "https://github.com/naxzyu/ares-engine",
    "classifiers": [
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent"
    ],
    "license": "Apache 2.0",
    "python_requires": ">=3.12",
    "packages": find_packages(exclude=["examples"]),
    "include_package_data": True,
    "package_data": {
        "ares.hooks": ["*.py"],
        "ares.ini": ["*.ini"],
    },
    "zip_safe": False,
    "options": {
        "sdist": {
            "no_cfg": True
        }
    }
}

# Command classes setup
cmdclass = {}

# Import utils only if needed to avoid early imports
def import_utils():
    global check_python_version, format_version, REQUIRED_PYTHON_VERSION
    from ares.utils.utils import check_python_version, format_version
    from ares.utils.constants import REQUIRED_PYTHON_VERSION

def update_metadata():
    """Update metadata with values from package_config if available."""
    global METADATA
    try:
        from ares.config import package_config
        metadata_updates = package_config.get_package_data()
        METADATA.update(metadata_updates)
        print("Loaded package metadata from package_config")
    except (ImportError, AttributeError) as e:
        print(f"Could not load package metadata from package_config: {e}")

def get_python(args=None):
    """Get a validated Python path from arguments or find appropriate version.

    Args:
        args: Command line arguments containing optional python path

    Returns:
        Path to valid Python executable or None if not found
    """
    # If args is provided and has a python attribute, use that path
    if args and hasattr(args, 'python') and args.python:
        python_path = Path(args.python)
        if not python_path.exists():
            print(f"Error: Specified Python executable not found: {python_path}")
            return None
        
        # Verify Python version
        if not check_python_version(python_path):
            version_str = format_version(REQUIRED_PYTHON_VERSION)
            print(f"Error: Python at {python_path} does not meet version requirements ({version_str}+)")
            return None
            
        return python_path
    
    # Otherwise, try to find Python with required version
    version_str = format_version(REQUIRED_PYTHON_VERSION)
    python_commands = ["py", "python", "python3", f"python{version_str}", "py3", f"py{version_str}"]
    
    # First try the py launcher which gives version info
    if os.name == 'nt':  # Windows-specific approach using py launcher
        try:
            output = subprocess.check_output(["py", "-0p"], text=True)
            for line in output.splitlines():
                line = line.strip()
                match = re.match(r"^-V:3\.12(?:-64|-32)?\s+(\S+)", line)
                if match:
                    python_path = Path(match.group(1))
                    print(f"Found Python 3.12 at: {python_path}")
                    return python_path
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Windows py launcher not available or failed.")
    
    # Try each command systematically
    for cmd in python_commands:
        try:
            # Check if command exists and get its version
            output = subprocess.check_output(
                [cmd, "-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"], 
                text=True,
                stderr=subprocess.DEVNULL
            )
            version = output.strip()
            
            # If it's Python 3.12, return the full path
            if version == "3.12":
                # Get the full path to the Python executable
                if os.name == 'nt':
                    output = subprocess.check_output(
                        [cmd, "-c", "import sys; print(sys.executable)"], 
                        text=True
                    )
                else:
                    output = subprocess.check_output(
                        ["which", cmd], 
                        text=True
                    )
                python_path = Path(output.strip())
                print(f"Found Python 3.12 at: {python_path}")
                return python_path
            else:
                print(f"Found Python {version} at {cmd}, but need 3.12")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"Command '{cmd}' not found or failed.")
    
    print("Error: Could not find Python 3.12+ interpreter.")
    return None


def get_venv(python_path=None, skip_setup=False):
    """Get a Python executable from a virtual environment.
    
    Args:
        python_path: Optional explicit path to Python executable to use
        skip_setup: If True, only return path without setting up environment
        
    Returns:
        Path to Python executable in virtual environment
    """
    # If we're already in a virtual environment, use that Python
    if sys.prefix != sys.base_prefix:
        log.info(f"Already in virtual environment: {sys.prefix}")
        return Path(sys.executable)
    
    # Define venv Python path
    if os.name == 'nt':
        venv_python = VENV_DIR / "Scripts" / "python.exe"
    else:
        venv_python = VENV_DIR / "bin" / "python"
    
    # Create venv if needed
    if not venv_python.exists():
        # Use provided Python path or find Python 3.12
        if python_path is None:
            python_path = get_python()
            if not python_path:
                sys.exit(1)
            
        log.info(f"Creating virtual environment at {VENV_DIR} using {python_path}...")
        subprocess.run([str(python_path), "-m", "venv", str(VENV_DIR)], check=True)
        log.info("Virtual environment created successfully.")
        log.info("Upgrading pip...")
        subprocess.run([str(venv_python), "-m", "pip", "install", "--upgrade", "pip"], check=True)
    else:
        log.info(f"Using existing virtual environment at {VENV_DIR}")
        
    if skip_setup:
        return venv_python
        
    log.info("Upgrading pip...")
    subprocess.run([str(venv_python), "-m", "pip", "install", "--upgrade", "pip"], check=True)
    
    req_path = PROJECT_ROOT / "requirements.txt"
    if req_path.exists():
        log.info(f"Installing dependencies from {req_path}...")
        try:
            subprocess.run([str(venv_python), "-m", "pip", "install", "-r", str(req_path)], check=True)
        except subprocess.CalledProcessError:
            log.warn("Warning: Some dependencies could not be installed.")
    
    log.info("Installing package in development mode...")
    try:
        result = subprocess.run(
            [str(venv_python), "-m", "pip", "install", "-e", "."],
            check=False,
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": str(PROJECT_ROOT)}
        )
        if result.returncode == 0:
            log.info("Package installed in development mode successfully.")
        else:
            log.error("Error: Failed to install package in development mode.")
            log.error(f"Error output: {result.stderr}")
            log.error("This is likely due to an import error within the package.")
            log.error("You can continue with development, but some features may not work correctly.")
    except Exception as e:
        log.error(f"Exception during package installation: {e}")
        log.error("You can continue with development, but some features may not work correctly.")
    
    return venv_python


def create_parser():
    """Create the argument parser for direct CLI usage."""
    parser = argparse.ArgumentParser(
        description="Ares Engine Setup Utility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python setup.py                  Create/setup virtual environment
  python setup.py --build          Build only the engine package
  python setup.py --build path     Build a project from specified path
  python setup.py --clean          Clean up build artifacts
  python setup.py --python path    Use specific Python interpreter (optional)
  python setup.py --force          Force rebuild all Cython modules and packages
"""
    )
    parser.add_argument('--build', nargs='?', const='engine',
                        help='Build the engine (no arg) or a project (with path to project directory)')
    parser.add_argument('--clean', action='store_true',
                        help='Clean up build artifacts')
    parser.add_argument('--python', type=str,
                        help='Path to specific Python interpreter to use (must be 3.12+)')
    parser.add_argument('--force', action='store_true',
                        help='Force rebuilding all Cython modules and packages')
    return parser

def is_pip_command():
    """Check if script is being run by pip with commands like egg_info, develop, etc."""
    pip_commands = ['egg_info', 'develop', 'install', 'bdist_wheel', 'sdist']
    return any(cmd in sys.argv[1:] for cmd in pip_commands)

# Check if we're being run directly or by setuptools/pip
if __name__ == "__main__":
    # Check if this is being run by pip with a command like egg_info/develop
    if is_pip_command():
        # Update metadata and let setuptools handle it
        update_metadata()
        setup(**METADATA)
    else:
        # Import utils for our custom CLI
        import_utils()
        
        # Create our custom CLI parser
        parser = create_parser()
        args = parser.parse_args()
        
        # Determine operation mode based on arguments
        operation_mode = "clean" if args.clean else "build" if (args.build or args.force) else "setup"

        match operation_mode:
            case "clean":
                # Clean mode - Import and run clean_project directly
                from ares.build.clean_build import clean_project  # noqa: E402
                clean_project()
                
            case "build":
                # Build mode - Load configs and set up build environment
                from ares.config import get_global_configs  # noqa: E402
                from ares.config.config_types import ConfigType  # noqa: E402
                CONFIGS = get_global_configs()
                
                # Initialize logging using the config from CONFIGS
                CONFIGS[ConfigType.LOGGING].initialize(LOGS_DIR)
                
                # Import modules for non-clean operations after logging is initialized
                from ares.utils import log  # noqa: E402
                from ares.build.build_engine import check_engine_build, build_engine  # noqa: E402
                from ares.build.build_project import build_project  # noqa: E402
                
                # Ninja is a required dependency for building Ares Engine
                from ares.build.ninja_compiler import NinjaCompiler  # noqa: E402
                cmdclass["build_ext"] = NinjaCompiler
                
                # Update metadata: cmd classes & package config
                METADATA["cmdclass"] = cmdclass
                update_metadata()
                
                # Get the appropriate Python path and set up environment
                python_path = get_python(args)
                log.info("Setting up build environment...")
                python_exe = get_venv(python_path, skip_setup=True)
                
                # Determine what to build based on build argument
                build_target = args.build or "engine"
                match build_target:
                    case "engine":
                        # Default: Build engine using already loaded global configs
                        log.info(f"Building Ares Engine into {ENGINE_BUILD_DIR}...")
                        os.makedirs(ENGINE_BUILD_DIR, exist_ok=True)
                        build_engine(python_exe, args.force, ENGINE_BUILD_DIR, configs=CONFIGS)
                    case project_path if os.path.exists(project_path):
                        # First ensure the engine is built
                        if not check_engine_build(ENGINE_BUILD_DIR):
                            log.info("Engine not found or incomplete in build directory. Building engine first...")
                            build_engine(python_exe, args.force, ENGINE_BUILD_DIR, configs=CONFIGS)
                        else:
                            log.info(f"Using previously built engine from: {ENGINE_BUILD_DIR}")
                        
                        # Build a project from the specified path
                        build_project(
                            py_exe=python_exe, 
                            project_path=project_path,
                            output_dir=BUILD_DIR,
                            configs=CONFIGS,
                            force=args.force
                        )
                    case _:
                        log.error(f"Project path not found: {args.build}")
                        sys.exit(1)
            
            case "setup":
                # Setup mode - Create virtual environment and install dependencies
                from ares.config import get_global_configs  # noqa: E402
                from ares.config.config_types import ConfigType  # noqa: E402
                CONFIGS = get_global_configs()
                CONFIGS[ConfigType.LOGGING].initialize(LOGS_DIR)
                
                # Import log module after initializing logging
                from ares.utils import log  # noqa: E402
                
                # Update metadata and get Python path
                update_metadata()
                python_path = get_python(args)
                
                print("Setting up Ares Engine development environment...")
                python_exe = get_venv(python_path, skip_setup=False)
                
                print("\nAres Engine development environment is ready!")
                print("To build the engine, run: python setup.py --build")
                print("To build a project, run: python setup.py --build path/to/project")
else:
    # This only runs when the script is imported, not when run directly
    update_metadata()
    setup(**METADATA)
