# cython: language_level=3

"""
Physics collision detection declarations.
"""

from ares.math.vector cimport Vector2, Vector3

cdef class AABB:
    cdef public float min_x, min_y, max_x, max_y
    
    cpdef float width(self)
    cpdef float height(self)
    cpdef Vector2 center(self)

cdef class Sphere:
    cdef public Vector3 center
    cdef public float radius

cpdef bint aabb_vs_aabb(AABB a, AABB b)
cpdef bint sphere_vs_sphere(Sphere a, Sphere b)
cpdef bint point_vs_aabb(float x, float y, AABB box)
