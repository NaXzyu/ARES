"""
Mathematics utilities accelerated with Cython.
"""

from __future__ import annotations

# Import primary components with error handling
try:
    from .vector import Vector2, Vector3, Vector4
    from .matrix import Matrix3x3, Matrix4x4
except ImportError:
    import warnings
    warnings.warn("Cython math modules not available.")

# Define what gets imported with "from ares.math import *"
__all__ = [
    'Vector2', 'Vector3', 'Vector4',
    'Matrix3x3', 'Matrix4x4'
]
