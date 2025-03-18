"""
Mathematics utilities accelerated with Cython.
"""

try:
    from .vector import Vector2, Vector3, Vector4
    from .matrix import Matrix3x3, Matrix4x4
except ImportError:
    import warnings
    warnings.warn("Cython modules not available.")
