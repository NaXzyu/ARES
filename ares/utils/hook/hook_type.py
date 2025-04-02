"""Hook type definitions for the Ares Engine."""

from enum import Enum
from ares.utils.const import PYTHON_EXT

class HookType(Enum):
    """Enum representing different hook types."""
    # Update enum values with new filenames
    ARES = f"ares_hook{PYTHON_EXT}"
    INIT_CONFIGS = f"configs_hook{PYTHON_EXT}"
    RUNTIME_LOGGING = f"logging_hook{PYTHON_EXT}"
    SDL2 = f"sdl2_hook{PYTHON_EXT}"
    CMODULES = f"cython_hook{PYTHON_EXT}"

    def __str__(self):
        """Return the string value of the enum."""
        return self.value
