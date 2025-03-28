#!/usr/bin/env python3
"""Build script for creating standalone executables from Ares Engine projects."""

import os
import sys
import subprocess
import shutil
import time
import datetime
from pathlib import Path

FILE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = FILE_DIR.parent.parent
BUILD_DIR = PROJECT_ROOT / "build"
LOGS_DIR = PROJECT_ROOT / "logs"

sys.path.insert(0, str(PROJECT_ROOT))

from ares.utils.utils import format_size, format_time
from ares.utils.build_utils import find_cython_binaries
from ares.build.sdl_finder import find_sdl2_dlls
from ares.build.spec_builder import SpecBuilder
from ares.hooks.hook_manager import HookManager
from ares.build.clean_build import clean_egg_info
from ares.config import CONFIGS
from ares.config.config_types import ConfigType

class ExecutableBuilder:
    """Builds standalone executables from Python scripts using PyInstaller."""

    def __init__(self, python_exe, output_dir, main_script, name=None, resources_dir=None, console_mode=True, onefile=True):
        """Initialize the executable builder.
        
        Args:
            python_exe: Path to Python executable to use for building
            output_dir: Directory where build output will be placed
            main_script: Main Python script to build into executable
            name: Name for the executable (defaults to main script's stem)
            resources_dir: Optional resources directory to include
            console_mode: Whether to build a console app (True) or GUI app (False)
            onefile: Whether to build a single file executable (True) or directory (False)
        """
        self.python_exe = str(python_exe)
        self.output_dir = Path(output_dir)
        self.main_script = Path(main_script)
        
        # Store the name parameter as an instance attribute
        self.name = name if name else self.main_script.stem
        
        self.resources_dir = Path(resources_dir) if resources_dir else None
        self.console_mode = console_mode
        self.onefile = onefile

        # Get package data from config using CONFIGS dictionary
        self.package_data = CONFIGS[ConfigType.PACKAGE].get_package_data()
        self.extensions = CONFIGS[ConfigType.PACKAGE].get_extensions()

        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)

        # Set log file path in project logs directory
        self.build_log_path = LOGS_DIR / "build.log"
        os.makedirs(LOGS_DIR, exist_ok=True)

        # Platform-specific attributes
        self.is_windows = os.name == 'nt'
        self.executable_extension = '.exe' if self.is_windows else ''

        # Tracking variables
        self.build_start_time = None
        self.build_duration = None

    def log(self, message):
        """Logs message to both internal system and build log file"""
        # Only log to ares logging system (avoids double printing)
        from ares.utils import log
        log.info(message)

        # Also append to build log file directly for redundancy
        with open(self.build_log_path, 'a') as log_file:
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_file.write(f"[{timestamp}] {message}\n")

    def build(self):
        """Build the executable using PyInstaller."""
        # Clean any potentially locked egg-info directories
        clean_egg_info()

        self.build_start_time = time.time()
        build_start = datetime.datetime.now()

        # Start build log
        with open(self.build_log_path, "a") as log:
            log.write(f"\n\n--- Build started at {build_start.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
            log.write(f"Project name: {self.name}\n")
            log.write(f"Main script: {self.main_script}\n")
            log.write(f"Output directory: {self.output_dir}\n")

        self.log(f"Building {self.name} executable from {self.main_script}")

        # Ensure PyInstaller is installed
        try:
            subprocess.run(
                [self.python_exe, "-c", "import PyInstaller"],
                check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        except subprocess.CalledProcessError:
            self.log("PyInstaller not found. Installing...")
            try:
                subprocess.run(
                    [self.python_exe, "-m", "pip", "install", "pyinstaller"],
                    check=True
                )
            except subprocess.CalledProcessError as e:
                self.log(f"Failed to install PyInstaller: {e}")
                return False

        # Find SDL2 DLLs - call the imported function directly
        binaries = find_sdl2_dlls(self.python_exe, self.log)

        # Find Cython binaries - use the imported function directly
        cython_binaries = find_cython_binaries(PROJECT_ROOT, self.log)
        binaries.extend(cython_binaries)

        # Create runtime hooks (using the HookManager class method)
        hook_files = HookManager.create_runtime_hooks(self.output_dir)

        # Create the out subdirectory within output_dir for executable files
        out_dir = self.output_dir / "out"
        os.makedirs(out_dir, exist_ok=True)

        # Create a spec file using the SpecBuilder class
        spec_builder = SpecBuilder(
            output_dir=self.output_dir,
            main_script=self.main_script,
            name=self.name,
            resources_dir=self.resources_dir,
            console_mode=self.console_mode,
            onefile=self.onefile
        )
        spec_file = spec_builder.create_spec(binaries=binaries, hook_files=hook_files)

        if not spec_file:
            self.log("Error: Failed to create spec file")
            return False

        # Build PyInstaller command using the spec file (much shorter)
        pyinstaller_cmd = [
            self.python_exe, "-m", "PyInstaller",
            str(spec_file),
            "--clean",
            "--distpath", str(out_dir),  # Use out subdirectory for output
            "--workpath", str(self.output_dir / "temp")  # Put work files in our temp directory
        ]

        # Log the command
        self.log("Running PyInstaller with spec file:")
        self.log(f"  {' '.join(map(str, pyinstaller_cmd))}")

        # Run PyInstaller
        try:
            # Capture PyInstaller output with more detailed error handling
            process = subprocess.Popen(
                pyinstaller_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            # Log PyInstaller output in real-time
            last_error_lines = []
            with open(self.build_log_path, 'a') as log_file:
                for line in process.stdout:
                    # Store last few lines to print on error
                    last_error_lines.append(line.strip())
                    if len(last_error_lines) > 10:
                        last_error_lines.pop(0)

                    # Write to build log
                    log_file.write(line)

                    # Print important lines to console for better visibility
                    if any(keyword in line.lower() for keyword in ['error:', 'exception:', 'traceback', 'fail', 'warning:', 'nameerror']):
                        print(line.strip())

            # Wait for process to complete
            ret_code = process.wait()
            if ret_code != 0:
                self.log(f"PyInstaller failed with return code {ret_code}")
                # Print the last few lines to help diagnose the error
                print("\nError details from PyInstaller:")
                for line in last_error_lines[-5:]:  # Show last 5 lines
                    if any(keyword in line.lower() for keyword in ['error:', 'exception:', 'traceback', 'nameerror']):
                        print(f"  {line}")

                return False
        except subprocess.CalledProcessError as e:
            self.log(f"PyInstaller failed: {e}")
            # Print any error output for debugging
            if hasattr(e, 'stderr') and e.stderr:
                self.log(f"Error output: {e.stderr}")
                # Also write to the build log
                with open(self.build_log_path, 'a') as log_file:
                    log_file.write(f"Error output: {e.stderr}\n")
            return False

        # Get the executable path from the out subdirectory
        executable_name = f"{self.name}{self.executable_extension}"
        target_exe = out_dir / executable_name

        # Log name information for debugging
        self.log(f"Building executable with name: {self.name}")
        self.log(f"Expected executable: {target_exe}")

        if target_exe.exists():
            # Calculate build telemetry
            build_end_time = time.time()
            self.build_duration = build_end_time - self.build_start_time

            # Get executable size
            exe_size = os.path.getsize(target_exe)
            size_str = format_size(exe_size)

            # Write build summary to log
            with open(self.build_log_path, "a") as log:
                build_end = datetime.datetime.now()
                log.write(f"Build completed at: {build_end.strftime('%Y-%m-%d %H:%M:%S')}\n")
                log.write(f"Build duration: {format_time(self.build_duration)}\n")
                log.write(f"Executable size: {size_str} ({exe_size:,} bytes)\n")
                log.write(f"Project name: {self.name}\n")
                log.write(f"Executable path: {target_exe}\n")

            # Display build summary - remove leading newline and make consistent with other build output
            self.log("="*50)
            self.log(" BUILD SUMMARY ".center(50, "="))
            self.log("="*50)
            self.log(f"Build time:      {format_time(self.build_duration)}")
            self.log(f"Executable size: {size_str}")
            self.log(f"Executable path: {target_exe}")
            self.log(f"Build log:       {self.build_log_path}")
            self.log("="*50)
            
            # Add installation instructions if this is a package
            if "ares-" in self.name.lower() and target_exe.suffix in ['.whl', '.tar.gz']:
                self.log(f"To install the engine, run:")
                self.log(f"  pip install {target_exe}")

            # Clean up PyInstaller artifacts
            build_temp_dir = self.output_dir / "temp"
            if build_temp_dir.exists():
                shutil.rmtree(build_temp_dir)

            # After PyInstaller finishes, explicitly remove PROJECT ROOT dist directory if it was created
            # This is different from our output out directory
            temp_dist_dir = PROJECT_ROOT / "dist"
            if temp_dist_dir.exists() and temp_dist_dir.is_dir() and temp_dist_dir != out_dir:
                try:
                    shutil.rmtree(temp_dist_dir)
                    self.log("Removed temporary PyInstaller dist directory")
                except (PermissionError, OSError) as e:
                    self.log(f"Warning: Could not remove temporary dist directory: {e}")

            # Also clean up egg-info again for good measure
            clean_egg_info()

            return True
        else:
            self.log(f"Error: Expected executable not found at {target_exe}")

            # Search for alternative executables that might have been created
            for file in out_dir.glob(f"*{self.executable_extension}"):
                self.log(f"Found executable: {file}")

            return False

    @classmethod
    def create(cls, python_exe, script_path, output_dir, name=None, resources_dir=None, console_mode=True, onefile=True):
        """Factory method to create and build an executable in one step.
        
        Args:
            python_exe: Path to Python executable
            script_path: Path to main script
            output_dir: Output directory
            name: Name for the executable (default: script filename)
            resources_dir: Optional resources directory
            console_mode: Whether to build console app (True) or GUI app (False)
            onefile: Whether to build single-file exe (True) or directory (False)
            
        Returns:
            bool: True if build succeeded, False otherwise
        """
        # Clean egg-info first to prevent permission issues
        clean_egg_info()

        builder = cls(
            python_exe=python_exe,
            output_dir=output_dir,
            main_script=script_path,
            name=name,
            resources_dir=resources_dir,
            console_mode=console_mode,
            onefile=onefile
        )

        return builder.build()
