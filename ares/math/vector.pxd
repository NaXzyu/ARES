# cython: language_level=3

"""
Vector class declarations for use in other Cython modules.
"""

cdef class Vector2:
    cdef public float x, y
    
    cpdef float length_squared(self)
    cpdef float length(self)
    cpdef float dot(self, Vector2 other)
    cpdef Vector2 normalize(self)

cdef class Vector3:
    cdef public float x, y, z

    cpdef Vector3 cross(self, Vector3 other)

cdef class Vector4:
    cdef public float x, y, z, w
