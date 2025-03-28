"""Hook type definitions for the Ares Engine."""

from enum import Enum


class HookType(Enum):
    """Enum representing different hook types."""
    # Update enum values with new filenames
    ARES = "ares_hook.py"
    INIT_CONFIGS = "configs_hook.py"
    RUNTIME_LOGGING = "logging_hook.py"
    SDL2 = "sdl2_hook.py"
    CYTHON_MODULES = "cython_hook.py"

    def __str__(self):
        """Return the string value of the enum."""
        return self.value
