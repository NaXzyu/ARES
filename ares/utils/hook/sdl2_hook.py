"""SDL2 runtime hook - configures library paths for frozen applications"""

import os
import sys
import ctypes
from pathlib import Path

from ares.utils.const import (
    PLATFORM_WINDOWS,
    CURRENT_PLATFORM,
    ERROR_MISSING_DEPENDENCY
)

# Early hook function that runs before any SDL2 imports
def configure_sdl2_paths():
    """Configure SDL2 paths and preload DLLs if needed"""
    if not getattr(sys, 'frozen', False):
        # Only needed in frozen applications
        return

    # Get the directory where the executable is located
    base_dir = Path(sys._MEIPASS)
    print(f"Ares Engine: Looking for SDL2 DLLs in {base_dir}")
    
    # List of possible subdirectories where SDL2 DLLs might be located
    search_paths = [
        base_dir,                    # Root directory
        base_dir / "SDL2",           # SDL2 subdirectory
        base_dir / "sdl2dll",        # sdl2dll directory
        base_dir / "sdl2dll/dll",    # sdl2dll/dll directory
        base_dir / "lib",            # lib directory
        Path(sys.executable).parent  # Directory containing the executable
    ]
    
    # SDL2 DLLs to look for
    sdl2_dlls = ["SDL2.dll", "SDL2_ttf.dll", "SDL2_image.dll", "SDL2_mixer.dll", "SDL2_gfx.dll"]
    
    # Find the directory containing SDL2.dll
    sdl2_dir = None
    for path in search_paths:
        if not path.exists():
            continue
            
        # Check if this directory contains SDL2.dll
        if (path / "SDL2.dll").exists():
            sdl2_dir = path
            print(f"Ares Engine: Found SDL2.dll in {sdl2_dir}")
            break
            
        # Recursive search for SDL2.dll (one level deep)
        for subdir in path.iterdir():
            if subdir.is_dir() and (subdir / "SDL2.dll").exists():
                sdl2_dir = subdir
                print(f"Ares Engine: Found SDL2.dll in {sdl2_dir}")
                break
        
        if sdl2_dir:
            break
    
    # If we found a directory with SDL2.dll, use it
    if sdl2_dir:
        # Set PYSDL2_DLL_PATH environment variable
        sdl2_dir_str = str(sdl2_dir)
        os.environ["PYSDL2_DLL_PATH"] = sdl2_dir_str
        os.environ["SDL_AUDIO_ALSA_SET_BUFFER_SIZE"] = "1"  # Performance tweak
        print(f"Ares Engine: Set PYSDL2_DLL_PATH to {sdl2_dir_str}")
        
        # Add to PATH on Windows to help find the DLLs
        if CURRENT_PLATFORM == PLATFORM_WINDOWS:
            old_path = os.environ.get('PATH', '')
            os.environ['PATH'] = f"{sdl2_dir_str};{old_path}"
        
        # Try to preload the DLLs
        for dll_name in sdl2_dlls:
            dll_path = sdl2_dir / dll_name
            if dll_path.exists():
                try:
                    ctypes.CDLL(str(dll_path))
                    print(f"Ares Engine: Successfully loaded {dll_name}")
                except Exception as e:
                    print(f"Ares Engine: Warning - Failed to load {dll_name}: {e}")
    else:
        print("Ares Engine: Warning - Could not find SDL2.dll in any expected location")
        # As a last resort, try to copy the DLLs to the executable directory
        try:
            # Look for DLLs in MEIPASS root
            for dll_name in sdl2_dlls:
                src_path = base_dir / dll_name
                if src_path.exists():
                    dest_dir = Path(sys.executable).parent
                    dest_path = dest_dir / dll_name
                    if not dest_path.exists():
                        import shutil
                        shutil.copy2(src_path, dest_path)
                        print(f"Ares Engine: Copied {dll_name} to {dest_dir}")
                        # After copying, set the directory and try to load
                        if dll_name == "SDL2.dll":
                            os.environ["PYSDL2_DLL_PATH"] = str(dest_dir)
                            try:
                                ctypes.CDLL(str(dest_path))
                                print(f"Ares Engine: Successfully loaded {dll_name} after copying")
                            except Exception as e:
                                print(f"Ares Engine: Warning - Failed to load {dll_name} after copying: {e}")
        except Exception as e:
            print(f"Ares Engine: Error during DLL copying: {e}")
            sys.exit(ERROR_MISSING_DEPENDENCY)

# Run the configuration immediately
configure_sdl2_paths()

# Don't import sdl2 here to avoid import issues
