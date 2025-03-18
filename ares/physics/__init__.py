"""
Physics engine components accelerated with Cython.
"""

try:
    from .collision import AABB, Sphere, check_collision
except ImportError:
    import warnings
    warnings.warn("Cython physics modules not available.")
