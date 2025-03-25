#!/usr/bin/env python3
"""Build script for cleaning Ares Engine project files."""

import os
import sys
import shutil
from pathlib import Path

# Always use SimpleLogger for clean operations to avoid log file locking issues
from ares.utils.log import SimpleLogger

# Create a log instance for this module
log = SimpleLogger()

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"

def clean_project():
    """Clean up build artifacts from the project directory."""
    log.info("Cleaning up build artifacts...")

    # Remove egg-info directory - enhanced version with more robust error handling
    for egg_info in PROJECT_ROOT.glob("*.egg-info"):
        if egg_info.is_dir():
            log.info(f"Removing {egg_info}")
            try:
                # Try with aggressive removal
                if os.name == 'nt':  # Windows specific
                    try:
                        os.system(f'rd /s /q "{egg_info}"')
                    except Exception:
                        # Fall back to regular method if command fails
                        shutil.rmtree(egg_info, onerror=handle_remove_readonly)
                else:
                    shutil.rmtree(egg_info, onerror=handle_remove_readonly)
            except Exception as e:
                log.warn(f"Warning: Could not remove {egg_info} - {e}")
                # Additional attempts for stubborn directories
                try:
                    for item in egg_info.glob("*"):
                        try:
                            if item.is_file():
                                item.unlink(missing_ok=True)
                            elif item.is_dir():
                                shutil.rmtree(item, ignore_errors=True)
                        except Exception:
                            pass
                except Exception:
                    pass

    # Remove build directory
    build_dir = PROJECT_ROOT / "build"
    if build_dir.exists():
        log.info(f"Removing {build_dir}")
        try:
            shutil.rmtree(build_dir, onerror=handle_remove_readonly)
        except Exception as e:
            log.warn(f"Warning: Could not completely remove {build_dir} - {e}")
            log.info("Tip: Close any running executables or processes that might be using these files")
            # Try to remove subdirectories that aren't locked
            for subdir in build_dir.glob("*"):
                if subdir.is_dir():
                    try:
                        shutil.rmtree(subdir, onerror=handle_remove_readonly)
                        log.info(f"Successfully removed {subdir}")
                    except Exception as e:
                        log.warn(f"Could not remove {subdir} - {e}")

    # Remove logs directory
    if LOGS_DIR.exists():
        log.info(f"Removing {LOGS_DIR}")
        try:
            shutil.rmtree(LOGS_DIR, onerror=handle_remove_readonly)
        except Exception as e:
            log.warn(f"Warning: Could not remove logs directory - {e}")
            # Try to remove individual log files
            for log_file in LOGS_DIR.glob("*.log"):
                try:
                    log_file.unlink()
                    log.info(f"Removed log file: {log_file.name}")
                except Exception as e:
                    log.warn(f"Could not remove log file: {log_file.name} - {e}")

    # Remove generated C files and compiled extensions
    for root, _, files in os.walk(PROJECT_ROOT / "ares"):
        for file in files:
            if file.endswith(".c") or file.endswith(".pyd") or file.endswith(".so"):
                path = Path(root) / file
                log.info(f"Removing {path}")
                try:
                    path.unlink()
                except Exception as e:
                    log.warn(f"Warning: Could not remove {path} - {e}")

    # Remove __pycache__ directories
    for pycache in PROJECT_ROOT.glob("**/__pycache__"):
        if pycache.is_dir():
            log.info(f"Removing {pycache}")
            try:
                shutil.rmtree(pycache, onerror=handle_remove_readonly)
            except Exception as e:
                log.warn(f"Warning: Could not remove {pycache} - {e}")

    log.info("Clean up completed!")

# Add this function to handle read-only files on Windows
def handle_remove_readonly(func, path, exc):
    """Handle read-only files during deletion (Windows)."""
    import stat
    if os.name == 'nt':
        if func in (os.unlink, os.remove, os.rmdir) and exc[1].errno == 5:  # Access Denied
            os.chmod(path, stat.S_IWRITE)
            func(path)
        else:
            raise

# Enhance with specialized egg_info cleaning function
def clean_egg_info():
    """Clean only egg-info directories - useful for pre-build cleanup."""
    for egg_info in PROJECT_ROOT.glob("*.egg-info"):
        if egg_info.is_dir():
            log.info(f"Removing {egg_info}")
            try:
                if os.name == 'nt':  # Windows specific
                    try:
                        os.system(f'rd /s /q "{egg_info}"')
                    except Exception:
                        shutil.rmtree(egg_info, onerror=handle_remove_readonly)
                else:
                    shutil.rmtree(egg_info, onerror=handle_remove_readonly)
                log.info(f"Successfully removed {egg_info}")
            except Exception as e:
                log.warn(f"Warning: Could not remove {egg_info} - {e}")
    
    # Also clean __pycache__ directories
    for pycache in PROJECT_ROOT.glob("**/__pycache__"):
        if pycache.is_dir():
            try:
                shutil.rmtree(pycache, onerror=handle_remove_readonly)
            except Exception:
                pass

# Execute only if run directly
if __name__ == "__main__":
    # No need for complex initialization, always use SimpleLogger
    clean_project()
