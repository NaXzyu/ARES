"""SDL2 runtime hook - configures library paths for frozen applications"""

import os
import sys
import ctypes

# Configure SDL2 paths before import
if getattr(sys, 'frozen', False):
    # We're running in a PyInstaller bundle
    dll_path = sys._MEIPASS
    os.environ["PYSDL2_DLL_PATH"] = dll_path
    print(f"Ares Engine: Setting PYSDL2_DLL_PATH to {dll_path}")
    
    # Try to manually load the DLLs
    try:
        for dll_name in ["SDL2.dll", "SDL2_ttf.dll", "SDL2_image.dll", "SDL2_mixer.dll"]:
            dll_path = os.path.join(sys._MEIPASS, dll_name)
            if os.path.exists(dll_path):
                ctypes.CDLL(dll_path)
                print(f"Ares Engine: Loaded {dll_name}")
    except Exception as e:
        print(f"Ares Engine: Warning - Error loading SDL2 DLLs manually: {e}")

# Do not import sdl2 here - it will be imported by the application
