#!/usr/bin/env python3
"""Build script for cleaning Ares Engine project files."""

import os
import shutil
import time
import stat
from pathlib import Path
from typing import Callable

from ares.utils.log import log
from ares.utils.paths import Paths
from ares.utils.utils import format_time

class BuildCleaner:
    """Manages cleaning of build artifacts for Ares Engine."""

    @classmethod
    def clean_project(cls) -> None:
        """Clean up build artifacts from the project directory."""
        print("Cleaning up build artifacts...")
        
        # Start timing
        start_time = time.time()
        
        # First clean egg_info directories
        cls.clean_egg_info()
        
        paths_to_clean = [
            Paths.get_build_path(),
            Paths.PROJECT_ROOT / "dist",
            # egg-info is already cleaned by clean_egg_info
            Paths.PROJECT_ROOT / "__pycache__",
            Paths.get_dev_logs_path(),
        ]
        
        # Add .pyd, .c, and __pycache__ files from the project
        for root, dirs, files in os.walk(Paths.PROJECT_ROOT):
            root_path = Path(root)
            
            # Skip the venv directory
            if ".venv" in root_path.parts:
                continue
                
            # Clean __pycache__ directories
            if "__pycache__" in dirs:
                paths_to_clean.append(root_path / "__pycache__")
                
            # Clean Cython-generated files
            for file in files:
                if (file.endswith(('.pyd', '.c', '.so')) and 
                    (file.startswith('_') or not file.endswith('.pyx.c'))):
                    file_path = root_path / file
                    if os.path.exists(file_path):
                        paths_to_clean.append(file_path)
        
        # Clean each path
        for path in paths_to_clean:
            try:
                if path.is_dir():
                    print(f"Removing directory: {path}")
                    shutil.rmtree(path, onerror=cls.handle_remove_readonly)
                elif path.exists():
                    print(f"Removing file: {path}")
                    path.unlink()
            except Exception as e:
                print(f"WARNING: Could not remove {path}: {e}")
        
        # Log the cleaned paths
        elapsed_time = time.time() - start_time
        print(f"Clean completed successfully in {format_time(elapsed_time)}.")

    @staticmethod
    def handle_remove_readonly(func: Callable, path: str, exc: tuple) -> None:
        """Handle read-only files during deletion (Windows).
        
        Args:
            func: The function that failed
            path: The path being processed
            exc: The exception info (type, value, traceback)
        """
        if os.name == 'nt':
            if func in (os.unlink, os.remove, os.rmdir) and exc[1].errno == 5:  # Access Denied
                os.chmod(path, stat.S_IWRITE)
                func(path)
            else:
                raise

    @classmethod
    def clean_egg_info(cls) -> None:
        """Clean only egg-info directories - useful for pre-build cleanup."""
        log.info("Cleaning egg-info directories and __pycache__...")
        
        # Clean egg-info directories
        for egg_info in Paths.PROJECT_ROOT.glob("*.egg-info"):
            if egg_info.is_dir():
                log.info(f"Removing {egg_info}")
                try:
                    shutil.rmtree(egg_info, onerror=cls.handle_remove_readonly)
                    log.info(f"Successfully removed {egg_info}")
                except Exception as e:
                    log.warn(f"WARNING: Could not remove {egg_info} - {e}")
        
        # Clean __pycache__ directories
        for pycache in Paths.PROJECT_ROOT.glob("**/__pycache__"):
            if pycache.is_dir():
                try:
                    shutil.rmtree(pycache, onerror=cls.handle_remove_readonly)
                except Exception:
                    pass
