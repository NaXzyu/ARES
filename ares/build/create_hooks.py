#!/usr/bin/env python3
"""Utility for creating PyInstaller runtime hooks for Ares Engine."""

import os
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def create_runtime_hooks(output_dir):
    """Create PyInstaller runtime hooks for SDL2 and Cython modules.
    
    Args:
        output_dir: Directory where hooks should be created
        
    Returns:
        list: List of paths to the created hook files
    """
    hooks_dir = Path(output_dir) / "hooks"
    os.makedirs(hooks_dir, exist_ok=True)
    
    hooks = []
    source_hooks_dir = PROJECT_ROOT / "ares" / "hooks"
    
    # Create SDL2 hook
    sdl2_hook_src = source_hooks_dir / "hook_sdl2.py" 
    if sdl2_hook_src.exists():
        sdl2_hook = hooks_dir / "hook-sdl2.py"
        shutil.copy2(sdl2_hook_src, sdl2_hook)
        hooks.append(sdl2_hook)
    
    # Create Cython modules hook
    cython_hook_src = source_hooks_dir / "hook_cython_modules.py"
    if cython_hook_src.exists():
        cython_hook = hooks_dir / "hook-cython_modules.py"
        shutil.copy2(cython_hook_src, cython_hook)
        hooks.append(cython_hook)
    
    # Create logging hook if it exists
    logging_hook_src = source_hooks_dir / "hook_runtime_logging.py"
    if logging_hook_src.exists():
        logging_hook = hooks_dir / "hook-runtime_logging.py"
        shutil.copy2(logging_hook_src, logging_hook)
        hooks.append(logging_hook)
    
    return hooks  # Return list, not tuple

def create_basic_runtime_hooks(output_dir):
    """Create only the essential PyInstaller runtime hooks for Ares Engine.
    
    Args:
        output_dir: Directory where hooks should be created
        
    Returns:
        list: List of paths to the created hook files
    """
    hooks_dir = Path(output_dir) / "hooks"
    os.makedirs(hooks_dir, exist_ok=True)
    
    hooks = []
    source_hooks_dir = PROJECT_ROOT / "ares" / "hooks"
    
    # Create SDL2 hook
    sdl2_hook_src = source_hooks_dir / "hook_sdl2.py" 
    if sdl2_hook_src.exists():
        sdl2_hook = hooks_dir / "hook-sdl2.py"
        shutil.copy2(sdl2_hook_src, sdl2_hook)
        hooks.append(sdl2_hook)
    
    # Create Cython modules hook
    cython_hook_src = source_hooks_dir / "hook_cython_modules.py"
    if cython_hook_src.exists():
        cython_hook = hooks_dir / "hook-cython_modules.py"
        shutil.copy2(cython_hook_src, cython_hook)
        hooks.append(cython_hook)
    
    return hooks
