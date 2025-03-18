# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True

"""
Matrix math implementation for 3x3 and 4x4 matrices.
"""

from libc.math cimport tan
from ares.math.vector cimport Vector3

cdef class Matrix3x3:
    def __init__(self):
        self.m00 = 1.0
        self.m01 = 0.0
        self.m02 = 0.0
        self.m10 = 0.0
        self.m11 = 1.0
        self.m12 = 0.0
        self.m20 = 0.0
        self.m21 = 0.0
        self.m22 = 1.0
    
    def __repr__(self):
        return (f"Matrix3x3(\n"
                f"  [{self.m00}, {self.m01}, {self.m02}]\n"
                f"  [{self.m10}, {self.m11}, {self.m12}]\n"
                f"  [{self.m20}, {self.m21}, {self.m22}]\n)")
                
    @staticmethod
    def identity():
        return Matrix3x3()
        
    @staticmethod
    def from_values(float m00, float m01, float m02, 
                    float m10, float m11, float m12,
                    float m20, float m21, float m22):
        cdef Matrix3x3 mat = Matrix3x3()
        mat.m00 = m00
        mat.m01 = m01
        mat.m02 = m02
        mat.m10 = m10
        mat.m11 = m11
        mat.m12 = m12
        mat.m20 = m20
        mat.m21 = m21
        mat.m22 = m22
        return mat

    def __mul__(a, b):
        if isinstance(a, Matrix3x3) and isinstance(b, Matrix3x3):
            return Matrix3x3.from_values(
                a.m00 * b.m00 + a.m01 * b.m10 + a.m02 * b.m20,
                a.m00 * b.m01 + a.m01 * b.m11 + a.m02 * b.m21,
                a.m00 * b.m02 + a.m01 * b.m12 + a.m02 * b.m22,
                
                a.m10 * b.m00 + a.m11 * b.m10 + a.m12 * b.m20,
                a.m10 * b.m01 + a.m11 * b.m11 + a.m12 * b.m21,
                a.m10 * b.m02 + a.m11 * b.m12 + a.m12 * b.m22,
                
                a.m20 * b.m00 + a.m21 * b.m10 + a.m22 * b.m20,
                a.m20 * b.m01 + a.m21 * b.m11 + a.m22 * b.m21,
                a.m20 * b.m02 + a.m21 * b.m12 + a.m22 * b.m22
            )
        return NotImplemented

cdef class Matrix4x4:
    def __init__(self):
        self.m00 = 1.0
        self.m01 = 0.0
        self.m02 = 0.0
        self.m03 = 0.0
        self.m10 = 0.0
        self.m11 = 1.0
        self.m12 = 0.0
        self.m13 = 0.0
        self.m20 = 0.0
        self.m21 = 0.0
        self.m22 = 1.0
        self.m23 = 0.0
        self.m30 = 0.0
        self.m31 = 0.0
        self.m32 = 0.0
        self.m33 = 1.0
        
    def __repr__(self):
        return (f"Matrix4x4(\n"
                f"  [{self.m00}, {self.m01}, {self.m02}, {self.m03}]\n"
                f"  [{self.m10}, {self.m11}, {self.m12}, {self.m13}]\n"
                f"  [{self.m20}, {self.m21}, {self.m22}, {self.m23}]\n"
                f"  [{self.m30}, {self.m31}, {self.m32}, {self.m33}])")
                
    @staticmethod
    def identity():
        return Matrix4x4()
        
    @staticmethod
    def from_values(float m00, float m01, float m02, float m03,
                    float m10, float m11, float m12, float m13,
                    float m20, float m21, float m22, float m23,
                    float m30, float m31, float m32, float m33):
        cdef Matrix4x4 mat = Matrix4x4()
        mat.m00 = m00
        mat.m01 = m01
        mat.m02 = m02
        mat.m03 = m03
        mat.m10 = m10
        mat.m11 = m11
        mat.m12 = m12
        mat.m13 = m13
        mat.m20 = m20
        mat.m21 = m21
        mat.m22 = m22
        mat.m23 = m23
        mat.m30 = m30
        mat.m31 = m31
        mat.m32 = m32
        mat.m33 = m33
        return mat

    @staticmethod
    def perspective(float fov_y, float aspect, float near, float far):
        cdef float f = 1.0 / tan(fov_y / 2.0)
        cdef float range_inv = 1.0 / (near - far)
        
        cdef Matrix4x4 mat = Matrix4x4()
        mat.m00 = f / aspect
        mat.m11 = f
        mat.m22 = (near + far) * range_inv
        mat.m23 = 2.0 * near * far * range_inv
        mat.m32 = -1.0
        mat.m33 = 0.0
        return mat
    
    @staticmethod
    def look_at(Vector3 eye, Vector3 target, Vector3 up):
        cdef Vector3 f = Vector3.normalize(Vector3.subtract(target, eye))
        cdef Vector3 s = Vector3.normalize(Vector3.cross(f, up))
        cdef Vector3 u = Vector3.cross(s, f)
        
        cdef Matrix4x4 mat = Matrix4x4()
        mat.m00 = s.x
        mat.m01 = s.y
        mat.m02 = s.z
        mat.m10 = u.x
        mat.m11 = u.y
        mat.m12 = u.z
        mat.m20 = -f.x
        mat.m21 = -f.y
        mat.m22 = -f.z
        mat.m03 = -Vector3.dot(s, eye)
        mat.m13 = -Vector3.dot(u, eye)
        mat.m23 = Vector3.dot(f, eye)
        return mat

    def __mul__(a, b):
        if isinstance(a, Matrix4x4) and isinstance(b, Matrix4x4):
            return Matrix4x4.from_values(
                a.m00 * b.m00 + a.m01 * b.m10 + a.m02 * b.m20 + a.m03 * b.m30,
                a.m00 * b.m01 + a.m01 * b.m11 + a.m02 * b.m21 + a.m03 * b.m31,
                a.m00 * b.m02 + a.m01 * b.m12 + a.m02 * b.m22 + a.m03 * b.m32,
                a.m00 * b.m03 + a.m01 * b.m13 + a.m02 * b.m23 + a.m03 * b.m33,
                
                a.m10 * b.m00 + a.m11 * b.m10 + a.m12 * b.m20 + a.m13 * b.m30,
                a.m10 * b.m01 + a.m11 * b.m11 + a.m12 * b.m21 + a.m13 * b.m31,
                a.m10 * b.m02 + a.m11 * b.m12 + a.m12 * b.m22 + a.m13 * b.m32,
                a.m10 * b.m03 + a.m11 * b.m13 + a.m12 * b.m23 + a.m13 * b.m33,
                
                a.m20 * b.m00 + a.m21 * b.m10 + a.m22 * b.m20 + a.m23 * b.m30,
                a.m20 * b.m01 + a.m21 * b.m11 + a.m22 * b.m21 + a.m23 * b.m31,
                a.m20 * b.m02 + a.m21 * b.m12 + a.m22 * b.m22 + a.m23 * b.m32,
                a.m20 * b.m03 + a.m21 * b.m13 + a.m22 * b.m23 + a.m23 * b.m33,
                
                a.m30 * b.m00 + a.m31 * b.m10 + a.m32 * b.m20 + a.m33 * b.m30,
                a.m30 * b.m01 + a.m31 * b.m11 + a.m32 * b.m21 + a.m33 * b.m31,
                a.m30 * b.m02 + a.m31 * b.m12 + a.m32 * b.m22 + a.m33 * b.m32,
                a.m30 * b.m03 + a.m31 * b.m13 + a.m32 * b.m23 + a.m33 * b.m33
            )
        return NotImplemented
