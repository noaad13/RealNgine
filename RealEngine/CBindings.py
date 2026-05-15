import ctypes

INVALID_TRIANGLE = 65535

class ZPixel(ctypes.Structure):
    _fields_ = [
        ("z", ctypes.c_float),
        ("triangle_id", ctypes.c_uint16)
    ]
