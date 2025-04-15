# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Define excluded modules/packages to avoid permission issues
excludes = ['ares.egg-info']

# Get runtime hooks dynamically from HookManager
import sys
import os
from pathlib import Path

# Use Paths API to find the project root
from ares.utils.paths import Paths
project_root = Paths.PROJECT_ROOT

# Add project root to path if needed
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Verify Python version meets requirements
from ares.utils.build.build_utils import BuildUtils
BuildUtils.verify_python()

# Get runtime hooks in proper execution order using HookManager
from ares.utils.hook.hook_manager import HookManager
hooks_path = Paths.get_hooks_path()
runtime_hooks = HookManager.get_runtime_hooks(hooks_path)

# Ensure the hooks are listed in the correct order for proper initialization
a = Analysis(
    ['{{MAIN_SCRIPT}}'],
    pathex=[],
    binaries=[],
    datas=[{{RESOURCES}}],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=runtime_hooks,  # Dynamically generated hooks list
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Manually collect all necessary files from ares, skipping egg-info
import os
from pathlib import Path

def collect_ares_files(analysis):
    # Get ares directory from sys.path
    import sys
    import ares
    ares_path = Path(ares.__file__).parent
    
    # Process ares files
    for root, dirs, files in os.walk(ares_path):
        # Skip egg-info directories
        dirs[:] = [d for d in dirs if not d.endswith('.egg-info')]
        
        rel_dir = os.path.relpath(root, ares_path.parent)
        for file in files:
            full_path = os.path.join(root, file)
            # Skip __pycache__ directories and .pyc files
            if '__pycache__' in full_path or file.endswith('.pyc'):
                continue
                
            if file.endswith(('.pyd', '.so')):
                analysis.binaries.append((os.path.join(rel_dir, file), full_path, 'BINARY'))
            elif file.endswith(('.py', '.ini')):
                analysis.datas.append((os.path.join(rel_dir, file), full_path, 'DATA'))

# Apply our custom collection instead of using collect_all
collect_ares_files(a)

# Ensure SDL2 DLLs are included
try:
    import sdl2dll
    import os
    # Fix: Use get_dllpath() instead of get_dll_path()
    dll_path = sdl2dll.get_dllpath()
    if os.path.exists(dll_path):
        print(f"SDL2 DLLs found at {dll_path}")
        import glob
        for dll in glob.glob(os.path.join(dll_path, "*.dll")):
            dll_name = os.path.basename(dll)
            # Include at both root and in sdl2dll/dll subdirectory for redundancy
            a.binaries.append((dll_name, dll, 'BINARY'))  # Root level
            sdl2_subdir = os.path.join("sdl2dll", "dll", dll_name)
            a.binaries.append((sdl2_subdir, dll, 'BINARY'))  # SDL2 subdirectory
except ImportError:
    print("Warning: sdl2dll not found - SDL2 functionality may be limited")

# Add key hidden imports - use new module paths consistently
a.hiddenimports.extend([
    'sdl2', 'sdl2.ext', 'sdl2.dll',
    'ares.core.window', 'ares.core.input',
    'ares.utils.log', 'ares.config.logging_config',
    'ares.config.config_manager',
    'ares.utils.hook.hook_type', 'ares.utils.hook.hook_manager',
    'ares.utils.hook.configs_hook', 'ares.utils.hook.logging_hook',
    'ares.utils.hook.ares_hook', 'ares.utils.hook.sdl2_hook', 'ares.utils.hook.cython_hook'
])

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{{NAME}}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console={{CONSOLE}},
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
    onefile={{ONEFILE}},
)