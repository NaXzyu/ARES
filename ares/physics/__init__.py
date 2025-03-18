"""
Physics engine components accelerated with Cython.
"""

from __future__ import annotations

# Import primary components with error handling
try:
    from .collision import AABB, Sphere, aabb_vs_aabb, sphere_vs_sphere, point_vs_aabb
except ImportError:
    import warnings
    warnings.warn("Cython physics modules not available.")

# Define what gets imported with "from ares.physics import *"
__all__ = [
    'AABB', 'Sphere',
    'aabb_vs_aabb', 'sphere_vs_sphere', 'point_vs_aabb'
]
