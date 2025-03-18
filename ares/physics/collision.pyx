# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True

"""
Physics collision detection utilities.
"""

from libc.math cimport sqrt, pow
from ares.math.vector cimport Vector2, Vector3

cdef class AABB:
    """Axis-Aligned Bounding Box"""
    def __init__(self, float min_x=0.0, float min_y=0.0, float max_x=0.0, float max_y=0.0):
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y
    
    def __repr__(self):
        return f"AABB(min=({self.min_x}, {self.min_y}), max=({self.max_x}, {self.max_y}))"
    
    cpdef float width(self):
        return self.max_x - self.min_x
    
    cpdef float height(self):
        return self.max_y - self.min_y
    
    cpdef Vector2 center(self):
        return Vector2(
            self.min_x + (self.max_x - self.min_x) * 0.5, 
            self.min_y + (self.max_y - self.min_y) * 0.5
        )

cdef class Sphere:
    """3D Sphere collision shape"""
    def __init__(self, Vector3 center=None, float radius=1.0):
        if center is None:
            self.center = Vector3(0, 0, 0)
        else:
            self.center = center
        self.radius = radius
    
    def __repr__(self):
        return f"Sphere(center=({self.center.x}, {self.center.y}, {self.center.z}), radius={self.radius})"

# Collision detection functions
cpdef bint aabb_vs_aabb(AABB a, AABB b):
    """Check if two AABBs are colliding."""
    return (a.min_x <= b.max_x and a.max_x >= b.min_x and
            a.min_y <= b.max_y and a.max_y >= b.min_y)

cpdef bint sphere_vs_sphere(Sphere a, Sphere b):
    """Check if two spheres are colliding."""
    cdef float dist_squared = (
        pow(a.center.x - b.center.x, 2) +
        pow(a.center.y - b.center.y, 2) +
        pow(a.center.z - b.center.z, 2)
    )
    cdef float radii_sum = a.radius + b.radius
    return dist_squared <= pow(radii_sum, 2)

cpdef bint point_vs_aabb(float x, float y, AABB box):
    """Check if a point is inside an AABB."""
    return (x >= box.min_x and x <= box.max_x and
            y >= box.min_y and y <= box.max_y)
