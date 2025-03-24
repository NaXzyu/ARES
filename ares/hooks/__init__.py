"""
Runtime hooks for PyInstaller.

These hooks ensure proper operation of Ares Engine components in frozen applications:
- hook_sdl2.py: SDL2 library loading
- hook_cython_modules.py: Extension module loading
- hook_runtime_logging.py: Logging configuration and output capture
"""
