# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True

"""
Vector math implementation for 2D, 3D, and 4D vectors.
"""

from libc.math cimport sqrt

cdef class Vector2:
    def __init__(self, float x=0.0, float y=0.0):
        self.x = x
        self.y = y
    
    def __repr__(self):
        return f"Vector2({self.x}, {self.y})"
    
    cpdef float length_squared(self):
        return self.x * self.x + self.y * self.y
    
    cpdef float length(self):
        return sqrt(self.length_squared())
    
    cpdef float dot(self, Vector2 other):
        return self.x * other.x + self.y * other.y
    
    cpdef Vector2 normalize(self):
        cdef float l = self.length()
        if l > 0:
            return Vector2(self.x / l, self.y / l)
        return Vector2()

cdef class Vector3:
    def __init__(self, float x=0.0, float y=0.0, float z=0.0):
        self.x = x
        self.y = y
        self.z = z
    
    def __repr__(self):
        return f"Vector3({self.x}, {self.y}, {self.z})"
    
    cpdef Vector3 cross(self, Vector3 other):
        return Vector3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x
        )

cdef class Vector4:
    def __init__(self, float x=0.0, float y=0.0, float z=0.0, float w=1.0):
        self.x = x
        self.y = y
        self.z = z
        self.w = w
    
    def __repr__(self):
        return f"Vector4({self.x}, {self.y}, {self.z}, {self.w})"
    
    @staticmethod
    def from_vector3(Vector3 v, float w=1.0):
        return Vector4(v.x, v.y, v.z, w)

# Static methods for Vector2
@staticmethod
def Vector2_add(Vector2 a, Vector2 b):
    return Vector2(a.x + b.x, a.y + b.y)

@staticmethod
def Vector2_subtract(Vector2 a, Vector2 b):
    return Vector2(a.x - b.x, a.y - b.y)

@staticmethod
def Vector2_multiply(Vector2 a, float scalar):
    return Vector2(a.x * scalar, a.y * scalar)

@staticmethod
def Vector2_normalize(Vector2 v):
    return v.normalize()

@staticmethod
def Vector2_dot(Vector2 a, Vector2 b):
    return a.dot(b)

# Static methods for Vector3
@staticmethod
def Vector3_add(Vector3 a, Vector3 b):
    return Vector3(a.x + b.x, a.y + b.y, a.z + b.z)

@staticmethod
def Vector3_subtract(Vector3 a, Vector3 b):
    return Vector3(a.x - b.x, a.y - b.y, a.z - b.z)

@staticmethod
def Vector3_multiply(Vector3 a, float scalar):
    return Vector3(a.x * scalar, a.y * scalar, a.z * scalar)

@staticmethod
def Vector3_normalize(Vector3 v):
    cdef float length = sqrt(v.x * v.x + v.y * v.y + v.z * v.z)
    if length > 0:
        return Vector3(v.x / length, v.y / length, v.z / length)
    return Vector3()

@staticmethod
def Vector3_cross(Vector3 a, Vector3 b):
    return a.cross(b)

@staticmethod
def Vector3_dot(Vector3 a, Vector3 b):
    return a.x * b.x + a.y * b.y + a.z * b.z

# Add these methods to the classes
Vector2.add = Vector2_add
Vector2.subtract = Vector2_subtract
Vector2.multiply = Vector2_multiply
Vector2.normalize = Vector2_normalize
Vector2.dot = Vector2_dot

Vector3.add = Vector3_add
Vector3.subtract = Vector3_subtract
Vector3.multiply = Vector3_multiply
Vector3.normalize = Vector3_normalize
Vector3.cross = Vector3_cross
Vector3.dot = Vector3_dot
