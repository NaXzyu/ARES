# cython: language_level=3

from ares.math.vector cimport Vector3, Vector4

cdef class Matrix3x3:
    # Public attributes
    cdef public float m00, m01, m02
    cdef public float m10, m11, m12
    cdef public float m20, m21, m22

cdef class Matrix4x4:
    # Public attributes
    cdef public float m00, m01, m02, m03
    cdef public float m10, m11, m12, m13
    cdef public float m20, m21, m22, m23
    cdef public float m30, m31, m32, m33