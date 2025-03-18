#!/usr/bin/env python3
"""
Ares Engine setup script for environment setup and package installation.
"""

import os
import sys
import subprocess
import argparse
import re
import shutil
import configparser
from pathlib import Path
from setuptools import setup, find_packages

# Define minimal constants needed to bootstrap
PROJECT_ROOT = Path(__file__).resolve().parent
VENV_DIR = PROJECT_ROOT / ".venv"
BUILD_SCRIPT = PROJECT_ROOT / "ares" / "build" / "build_engine.py"  # Updated path

# Package metadata
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
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent"
    ],
    "python_requires": ">=3.12",
    "packages": find_packages(exclude=["examples"]),
    "include_package_data": True,
    "zip_safe": False
}

def find_python_3_12():
    """Find Python 3.12 installation using the py launcher."""
    try:
        output = subprocess.check_output(["py", "-0p"], text=True)
        for line in output.splitlines():
            line = line.strip()
            match = re.match(r"^-V:3\.12(?:-64|-32)?\s+(\S+)", line)
            if match:
                python_path = Path(match.group(1))
                print(f"Found Python 3.12 at: {python_path}")
                return python_path
        print("Python 3.12 not found.")
        return None
    except subprocess.CalledProcessError as e:
        print(f"Error executing 'py -0p': {e}")
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
    """Get a Python executable from a virtual environment, with optional setup.
    
    Args:
        skip_setup: If True, only verifies the venv exists without updating packages
    """
    if sys.prefix != sys.base_prefix:
        print(f"Already in virtual environment: {sys.prefix}")
        return Path(sys.executable)
    if os.name == 'nt':
        venv_python = VENV_DIR / "Scripts" / "python.exe"
    else:
        venv_python = VENV_DIR / "bin" / "python"
    if not venv_python.exists():
        python_path = find_python_3_12()
        if not python_path:
            print("Error: Python 3.12+ is required but not found.")
            sys.exit(1)
        print(f"Creating virtual environment at {VENV_DIR}...")
        subprocess.run([str(python_path), "-m", "venv", str(VENV_DIR)], check=True)
        print("Virtual environment created successfully.")
        print("Upgrading pip...")
        subprocess.run([str(venv_python), "-m", "pip", "install", "--upgrade", "pip"], check=True)
    else:
        print(f"Using existing virtual environment at {VENV_DIR}")
    if skip_setup:
        return venv_python
    print("Upgrading pip...")
    subprocess.run([str(venv_python), "-m", "pip", "install", "--upgrade", "pip"], check=True)
    req_path = PROJECT_ROOT / "requirements.txt"
    if req_path.exists():
        print(f"Installing dependencies from {req_path}...")
        try:
            subprocess.run([str(venv_python), "-m", "pip", "install", "-r", str(req_path)], check=True)
        except subprocess.CalledProcessError:
            print("Warning: Some dependencies could not be installed.")
    print("Installing package in development mode...")
    try:
        result = subprocess.run(
            [str(venv_python), "-m", "pip", "install", "-e", "."],
            check=False,
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": str(PROJECT_ROOT)}
        )
        if result.returncode == 0:
            print("Package installed in development mode successfully.")
        else:
            print("Error: Failed to install package in development mode.")
            print(f"Error output: {result.stderr}")
            print("This is likely due to an import error within the package.")
            print("You can continue with development, but some features may not work correctly.")
    except Exception as e:
        print(f"Exception during package installation: {e}")
        print("You can continue with development, but some features may not work correctly.")
    return venv_python

def clean_project():
    """Clean up build artifacts from the project directory."""
    print("Cleaning up build artifacts...")
    
    # Remove egg-info directory
    for egg_info in PROJECT_ROOT.glob("*.egg-info"):
        if egg_info.is_dir():
            print(f"Removing {egg_info}")
            shutil.rmtree(egg_info)
    
    # Remove build directory
    build_dir = PROJECT_ROOT / "build"
    if build_dir.exists():
        print(f"Removing {build_dir}")
        shutil.rmtree(build_dir)
    
    # Remove generated C files and compiled extensions
    for root, _, files in os.walk(PROJECT_ROOT / "ares"):
        for file in files:
            if file.endswith(".c") or file.endswith(".pyd") or file.endswith(".so"):
                path = Path(root) / file
                print(f"Removing {path}")
                path.unlink()
    
    # Remove __pycache__ directories
    for pycache in PROJECT_ROOT.glob("**/__pycache__"):
        if pycache.is_dir():
            print(f"Removing {pycache}")
            shutil.rmtree(pycache)
    
    print("Clean up completed!")

def create_parser():
    """Create the argument parser for direct CLI usage."""
    parser = argparse.ArgumentParser(
        description="Ares Engine Setup Utility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  py setup.py             Create/setup virtual environment
  py setup.py --build     Build the engine package
  py setup.py --clean     Clean up build artifacts
  py setup.py --build --force   Force rebuild all Cython modules
"""
    )
    parser.add_argument('--build', action='store_true', help='Build the engine into a distributable package')
    parser.add_argument('--clean', action='store_true', help='Clean up build artifacts')
    parser.add_argument('--force', action='store_true', help='Force rebuilding all Cython modules and packages')
    
    return parser

# Try to import the build_ext class if available
cmdclass = {}
try:
    from ares.build.build_ext_ninja import BuildExtWithNinja  # Updated import path
    cmdclass["build_ext"] = BuildExtWithNinja
except ImportError:
    pass

# Update metadata with command classes
METADATA["cmdclass"] = cmdclass

if __name__ == "__main__":
    # Check for standard setuptools commands
    setuptools_commands = ['egg_info', 'bdist_wheel', 'install', 'develop', 'sdist', 'build_ext']
    if len(sys.argv) > 1 and sys.argv[1] in setuptools_commands:
        setup(**METADATA)
    else:
        # Parse our own arguments for CLI usage
        parser = create_parser()
        args = parser.parse_args()
        
        if args.clean:
            clean_project()
        elif args.build:
            print("Setting up build environment...")
            py_exe = get_venv_python(skip_setup=True)
            print(f"Running build with '{py_exe}'")
            try:
                cmd = [str(py_exe), str(BUILD_SCRIPT), "--python", str(py_exe)]
                if args.force:
                    cmd.append("--force")
                subprocess.run(cmd, check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error running build script: {e}")
                sys.exit(1)
        else:
            print("Setting up Ares Engine development environment...")
            py_exe = get_venv_python(skip_setup=False)
            print("\nAres Engine development environment is ready!")
            print("To build the engine, run: py setup.py --build\n")
else:
    # This only runs when the script is imported, not when run directly
    setup(**METADATA)
