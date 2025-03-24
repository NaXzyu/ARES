#!/usr/bin/env python3
"""Utility functions for finding SDL2 libraries during build."""

import os
import subprocess

def find_sdl2_dlls(python_exe, logger=None):
    """Find SDL2 DLLs and return them as a list of (source, destination) tuples."""
    # We only need SDL2 DLLs on Windows
    if os.name != 'nt':
        return []
        
    # Log if logger is provided
    def log(message):
        if logger:
            logger(message)
    
    log("Locating SDL2 libraries...")
    
    sdl2_finder = """
import os, sys, glob, site
from pathlib import Path

def find_sdl2_dlls():
    # First check if pysdl2-dll package is installed
    try:
        from sdl2dll import get_dllpath
        dll_path = get_dllpath()
        if os.path.exists(dll_path):
            dlls = glob.glob(os.path.join(dll_path, "*.dll"))
            if dlls:
                print(f"FOUND_DLLS:{dll_path}")
                for dll in dlls:
                    print(f"DLL:{os.path.basename(dll)}")
                return
    except ImportError:
        pass
    
    # Check installation in site-packages
    for site_dir in site.getsitepackages():
        for dll_subdir in ["sdl2dll/dll", "sdl2", "SDL2", "pysdl2"]:
            check_dir = os.path.join(site_dir, dll_subdir)
            if os.path.exists(check_dir):
                dlls = glob.glob(os.path.join(check_dir, "*.dll"))
                if dlls:
                    print(f"FOUND_DLLS:{check_dir}")
                    for dll in dlls:
                        print(f"DLL:{os.path.basename(dll)}")
                    return
    
    print("NO_DLLS_FOUND")

find_sdl2_dlls()
"""
    
    result = subprocess.run(
        [str(python_exe), "-c", sdl2_finder],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False
    )
    
    sdl2_dll_path = None
    sdl2_dlls = []
    
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.startswith("FOUND_DLLS:"):
            sdl2_dll_path = line[11:].strip()
            log(f"Found SDL2 DLL directory: {sdl2_dll_path}")
        elif line.startswith("DLL:"):
            dll_name = line[4:].strip()
            sdl2_dlls.append(dll_name)
            log(f"Found SDL2 DLL: {dll_name}")
    
    binaries = []
    if sdl2_dll_path and sdl2_dlls:
        for dll in sdl2_dlls:
            dll_path = os.path.join(sdl2_dll_path, dll)
            if os.path.exists(dll_path):
                binaries.append((dll_path, '.'))
    
    return binaries
