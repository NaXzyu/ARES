"""
Ares Engine - A cross-platform game engine with Cython acceleration.
"""

from __future__ import annotations

# Use lazy imports so utilities can be imported without pulling in SDL2
__all__ = ['Window', 'Input', 'Renderer']

def __getattr__(name):
    if name == 'Window':
        from ares.core import Window
        return Window
    elif name == 'Input':
        from ares.core import Input
        return Input
    elif name == 'Renderer':
        from ares.renderer import Renderer
        return Renderer
    
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
