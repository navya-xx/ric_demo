import ctypes


# Addresses
ADDRESS_CONTROL_MODE = 0x04
ADDRESS_CONTROL_INPUT = 0x01
ADDRESS_CONTROL_K = 0x08


# Structures
class twipr_control_input(ctypes.Structure):
    _fields_ = [("u1", ctypes.c_float), ("u2", ctypes.c_float)]


class twipr_control_output(ctypes.Structure):
    _fields_ = [("u_left", ctypes.c_float), ("u_right", ctypes.c_float)]
