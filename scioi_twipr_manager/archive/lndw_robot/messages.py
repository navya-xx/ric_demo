import ctypes
from archive.cm4_core_old2.communication.serial.protocols.uart_protocol import UART_Message


class UART_MSG_CORE_Write_Led(UART_Message):
    cmd = 1
    msg = 0x03
    add = [0, 0]

    led_num: int
    led_state: int

    class _data(ctypes.Structure):
        _pack_ = 1
        _fields_ = [("led_num", ctypes.c_uint8), ("led_state", ctypes.c_int8)]

    def encode(self):
        # noinspection PyTypeChecker
        self.data = bytes(self._data(self.led_num, self.led_state))
        return super().encode()


class UART_MSG_CORE_Write_Motors(UART_Message):
    cmd = 1
    msg = 0x03
    add = [1, 0]

    motor_left_state: int
    motor_right_state: int
    motor_left_speed: float
    motor_right_speed: float

    class _data(ctypes.Structure):
        _pack_ = 1
        _fields_ = [("motor_left_state", ctypes.c_uint8), ("motor_left_speed", ctypes.c_float),
                    ("motor_right_state", ctypes.c_uint8), ("motor_right_speed", ctypes.c_float)]

    def encode(self):
        # noinspection PyTypeChecker
        self.data = bytes(
            self._data(self.motor_left_state, self.motor_left_speed, self.motor_right_state, self.motor_right_speed))
        return super().encode()
