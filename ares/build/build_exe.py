#!/usr/bin/env python3
"""Build script for creating standalone executables from Ares Engine examples."""

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
from ares.build.sdl_finder import find_sdl2_dlls
from ares.build.build_template import create_spec_file, create_spec_from_template
from ares.build.create_hooks import create_runtime_hooks
from ares.build.clean_build import clean_egg_info  # Add this import

class ExecutableBuilder:
    """Builds standalone executables from Python scripts using PyInstaller."""
    
    def __init__(self, python_exe, output_dir, main_script, name=None, resources_dir=None):
        """Initialize the executable builder."""
        self.python_exe = str(python_exe)
        self.output_dir = Path(output_dir)
        self.main_script = Path(main_script)
        self.name = name or self.main_script.stem
        self.resources_dir = Path(resources_dir) if resources_dir else None
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Create logs directory if it doesn't exist
        os.makedirs(LOGS_DIR, exist_ok=True)
        
        # Set log file paths - build log goes to logs directory
        self.build_log_path = LOGS_DIR / "build.log"
        
        # Platform-specific attributes
        self.is_windows = os.name == 'nt'
        self.executable_extension = '.exe' if self.is_windows else ''
        
        # Build settings
        self.console_mode = True  # Set to False for windowed applications
        self.onefile = True       # Set to False for directory mode
        
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

    def find_cython_binaries(self):
        """Find all compiled Cython modules and Python files in the ares package."""
        binaries = []
        
        # Include the entire 'ares' package instead of selective modules
        ares_root = PROJECT_ROOT / "ares"
        
        # Walk through the entire module structure
        for root, dirs, files in os.walk(ares_root):
            for file in files:
                # Skip __pycache__ directories
                if "__pycache__" in root:
                    continue
                    
                # Get relative path from ares root to create proper destination
                rel_path = os.path.relpath(root, PROJECT_ROOT)
                dest_dir = rel_path.replace("\\", "/")  # Normalize path separators
                
                # Full path to the file
                file_path = Path(root) / file
                
                # Include Python files and compiled extensions
                if (file.endswith('.py') or 
                    file.endswith('.pyd') or 
                    file.endswith('.so') or
                    file.endswith('.ini')):
                    binaries.append((str(file_path), dest_dir))
                    self.log(f"Including module file: {file_path} -> {dest_dir}")
        
        return binaries

    def build(self):
        """Build the executable using PyInstaller."""
        # Clean any potentially locked egg-info directories
        from ares.build.clean_build import clean_egg_info
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
        
        # Find Cython binaries
        cython_binaries = self.find_cython_binaries()
        binaries.extend(cython_binaries)
        
        # Create runtime hooks (using our new module)
        hook_files = create_runtime_hooks(self.output_dir)
        
        # Don't try to unpack hooks - just use the list directly
        # First try to create spec file from template
        spec_file = create_spec_from_template(
            self.output_dir,
            self.main_script,
            self.name,
            self.resources_dir,
            self.console_mode,
            self.onefile
        )
        
        # If template-based spec creation failed, fall back to dynamic generation
        if not spec_file:
            spec_file = create_spec_file(
                self.output_dir,
                self.main_script,
                self.name,
                binaries,
                hook_files,  # Pass the entire hook_files list
                self.resources_dir,
                self.console_mode,
                self.onefile
            )
        
        # Build PyInstaller command using the spec file (much shorter)
        pyinstaller_cmd = [
            self.python_exe, "-m", "PyInstaller", 
            str(spec_file),
            "--clean",
            "--distpath", str(self.output_dir),  # Specify output directory explicitly
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
        
        # Get the executable path directly from output directory
        executable_name = f"{self.name}{self.executable_extension}"
        target_exe = self.output_dir / executable_name
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
            
            # Display build summary
            self.log("\n" + "="*50)
            self.log(" BUILD SUMMARY ".center(50, "="))
            self.log("="*50)
            self.log(f"Build time:      {format_time(self.build_duration)}")
            self.log(f"Executable size: {size_str}")
            self.log(f"Executable path: {target_exe}")
            self.log(f"Build log:       {self.build_log_path}")
            self.log("="*50)
            
            # Clean up PyInstaller artifacts
            build_temp_dir = self.output_dir / "temp"
            if build_temp_dir.exists():
                shutil.rmtree(build_temp_dir)
            
            # After PyInstaller finishes, explicitly remove dist directory if it was created
            dist_dir = PROJECT_ROOT / "dist"
            if dist_dir.exists() and dist_dir.is_dir():
                try:
                    shutil.rmtree(dist_dir)
                    self.log("Removed temporary PyInstaller dist directory")
                except (PermissionError, OSError) as e:
                    self.log(f"Warning: Could not remove temporary dist directory: {e}")
            
            # Also clean up egg-info again for good measure
            clean_egg_info()
            
            return True
        else:
            self.log(f"Error: Expected executable not found at {target_exe}")
            return False

def build_executable(
    python_exe, 
    script_path, 
    output_dir, 
    name=None, 
    resources_dir=None, 
    console=True, 
    onefile=True
):
    """Build a standalone executable from a Python script."""
    # Clean egg-info first to prevent permission issues
    clean_egg_info()
    
    builder = ExecutableBuilder(
        python_exe=python_exe,
        output_dir=output_dir,
        main_script=script_path,
        name=name,
        resources_dir=resources_dir
    )
    builder.console_mode = console
    builder.onefile = onefile
    
    return builder.build()
