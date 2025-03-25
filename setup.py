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

# Import SimpleLogger which doesn't rely on file logging
from ares.utils.log import SimpleLogger, simple_logger

# Create a simple logger for early operations
log = simple_logger

# Package metadata with PyInstaller dependency added through requirements.txt
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

# Command classes setup will be initialized after determining mode
cmdclass = {}

def find_python_3_12():
    """Find Python 3.12 installation using the py launcher."""
    try:
        output = subprocess.check_output(["py", "-0p"], text=True)
        for line in output.splitlines():
            line = line.strip()
            match = re.match(r"^-V:3\.12(?:-64|-32)?\s+(\S+)", line)
            if match:
                python_path = Path(match.group(1))
                log.info(f"Found Python 3.12 at: {python_path}")
                return python_path
        log.warn("Python 3.12 not found.")
        return None
    except subprocess.CalledProcessError as e:
        log.error(f"Error executing 'py -0p': {e}")
        return None

def check_python_version(python_path, required_version=(3, 12)):
    """Check if the Python interpreter meets the version requirements."""
    try:
        result = subprocess.run(
            [str(python_path), "-c", f"import sys; sys.exit(0 if sys.version_info >= {required_version} else 1)"],
            check=False
        )
        return result.returncode == 0
    except Exception:
        return False

def detect_existing_venv():
    """Detect existing virtual environments in the project directory."""
    venv_dirs = [
        VENV_DIR,
        PROJECT_ROOT / "venv",
        PROJECT_ROOT / "env",
        PROJECT_ROOT / ".env",
        PROJECT_ROOT / "virtualenv",
        PROJECT_ROOT / ".conda_env"
    ]
    for venv_dir in venv_dirs:
        if not venv_dir.exists():
            continue
        if os.name == 'nt':
            python_exe = venv_dir / "Scripts" / "python.exe"
        else:
            python_exe = venv_dir / "bin" / "python"
        if python_exe.exists() and check_python_version(python_exe):
            return venv_dir
    return None

def get_venv_python(skip_setup=False):
    """Get a Python executable from a virtual environment, with optional setup."""
    if sys.prefix != sys.base_prefix:
        log.info(f"Already in virtual environment: {sys.prefix}")
        return Path(sys.executable)
    if os.name == 'nt':
        venv_python = VENV_DIR / "Scripts" / "python.exe"
    else:
        venv_python = VENV_DIR / "bin" / "python"
    if not venv_python.exists():
        python_path = find_python_3_12()
        if not python_path:
            log.error("Error: Python 3.12+ is required but not found.")
            sys.exit(1)
        log.info(f"Creating virtual environment at {VENV_DIR}...")
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
  py setup.py                  Create/setup virtual environment
  py setup.py --build          Build the engine package
  py setup.py --build path     Build a project from specified path
  py setup.py --clean          Clean up build artifacts
  py setup.py --force          Force rebuild all Cython modules and packages
"""
    )
    parser.add_argument('--build', nargs='?', const='engine',
                        help='Build the engine (no arg) or a project (with path to project directory)')
    parser.add_argument('--clean', action='store_true',
                        help='Clean up build artifacts')
    parser.add_argument('--force', action='store_true',
                        help='Force rebuilding all Cython modules and packages')
    return parser

def build_engine(py_exe, force=False):
    """Build the Ares Engine into the engine directory."""
    # Only import build_engine when needed
    from ares.build.build_engine import build_engine as _build_engine
    
    log.info(f"Building Ares Engine into {ENGINE_BUILD_DIR}...")
    os.makedirs(ENGINE_BUILD_DIR, exist_ok=True)

    cmd = [str(py_exe), str(BUILD_SCRIPT), "--python", str(py_exe)]
    if force:
        cmd.append("--force")

    # Add output directory parameter
    cmd.extend(["--output-dir", str(ENGINE_BUILD_DIR)])

    try:
        log.info(f"Running build command: {' '.join(str(c) for c in cmd)}")
        return _build_engine(py_exe, force, ENGINE_BUILD_DIR)
    except Exception as e:
        log.error(f"Error building engine: {e}")
        return False

# Check if we're running a standard setuptools command
setuptools_commands = ['egg_info', 'bdist_wheel', 'install', 'develop', 'sdist', 'build_ext']
is_setuptools_command = len(sys.argv) > 1 and sys.argv[1] in setuptools_commands

# Special case for pip handling setuptools commands
if is_setuptools_command:
    # Initialize Ninja command class if available
    try:
        from ares.build.ninja_compiler import NinjaCompiler
        if NinjaCompiler is not None:
            cmdclass["build_ext"] = NinjaCompiler
    except ImportError:
        pass
    
    # Update metadata with command classes
    METADATA["cmdclass"] = cmdclass
    
    # For setuptools commands, just call setup() and exit
    setup(**METADATA)
    sys.exit(0)

# For our custom commands, use the normal CLI handling
if __name__ == "__main__":
    parser = create_parser()
    args, unknown_args = parser.parse_known_args()
    
    # Handle unknown arguments as error
    if unknown_args:
        # Pass through to setup() for any setuptools commands we didn't explicitly check for
        if unknown_args[0] in ['--help', '-h'] or unknown_args[0].startswith('--'):
            setup(**METADATA)
            sys.exit(0)
        else:
            parser.print_help()
            print(f"\nError: Unrecognized arguments: {' '.join(unknown_args)}")
            sys.exit(1)
    
    # Special handling for clean mode
    if args.clean:
        # When cleaning, just run clean_project directly without initializing logging
        print("Cleaning up build artifacts...")
        from ares.build.clean_build import clean_project
        clean_project()
        print("Clean up completed!")
    else:
        # For all other modes, initialize real logging and imports
        from ares.config.logging_config import initialize_logging
        initialize_logging(LOGS_DIR)
        
        # Import modules for non-clean operations
        from ares.utils import log
        from ares.utils.build_utils import find_main_script, get_cython_module_dirs
        from ares.build.build_engine import check_engine_built
        from ares.build.ninja_compiler import NinjaCompiler
        from ares.build.build_project import build_project
        from ares.build.clean_build import clean_project
        
        # Define flag for Ninja extension availability for non-clean operations
        HAVE_NINJA_EXT = NinjaCompiler is not None
        if HAVE_NINJA_EXT:
            cmdclass["build_ext"] = NinjaCompiler
        
        # Update metadata with command classes
        METADATA["cmdclass"] = cmdclass
        
        # Handle build operations
        if args.build or args.force:
            log.info("Setting up build environment...")
            py_exe = get_venv_python(skip_setup=True)
            
            if args.build == 'engine' or args.build is None:
                # Default case: build the engine
                build_engine(py_exe, args.force)
            elif os.path.exists(args.build):
                # First ensure the engine is built
                if not check_engine_built(ENGINE_BUILD_DIR):
                    log.info("Engine not found or incomplete in build directory. Building engine first...")
                    if not build_engine(py_exe, args.force):
                        log.error("Failed to build engine. Cannot build project.")
                        sys.exit(1)
                else:
                    log.info(f"Using previously built engine from: {ENGINE_BUILD_DIR}")
                
                # Build a project from the specified path
                build_project(py_exe, args.build, args.force)
        else:
            log.info("Setting up Ares Engine development environment...")
            py_exe = get_venv_python(skip_setup=False)
            log.info("\nAres Engine development environment is ready!")
            log.info("To build the engine, run: py setup.py --build")
            log.info("To build a project, run: py setup.py --build path/to/project")
else:
    # This only runs when the script is imported, not when run directly
    setup(**METADATA)
