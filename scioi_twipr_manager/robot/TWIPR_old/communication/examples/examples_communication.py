import ctypes
import logging
import time

from robot.TWIPR.communication.twipr_comm_utils import reset_uart

# import numpy as np

from robot.TWIPR.settings import *
from robot.TWIPR.communication.twipr_comm_stm import *
import cm4_core.utils as utils

logging.Formatter(
    fmt='%(asctime)s.%(msecs)03d',
    datefmt='%Y-%m-%d,%H:%M:%S'
)

logging.basicConfig(
    format='%(asctime)s.%(msecs)03d %(levelname)-8s %(name)-8s %(message)s',
    level=logging.INFO,
    datefmt='%H:%M:%S'
)


def example_serial_communication():
    def rx_callback(message, *args, **kwargs):
        x = utils.ctypes.struct_to_dict(test_struct.from_buffer_copy(message.data))
        print(x)
        pass

    comm = TWIPR_Communication_STM32()
    comm.registerCallback('rx', rx_callback)
    comm.start()

    x = test_struct(a=99, b=-88888, c=ctypes.c_wchar_p("HELLO"))
    comm.echo(address=0x0102, value=x, type=test_struct, flag=3)
    time.sleep(5)

    comm.close()


def example_write():
    def rx_callback(message, *args, **kwargs):
        print(message)
        pass

    comm = TWIPR_Communication_STM32()
    comm.registerCallback('rx', rx_callback)
    comm.start()

    comm.write(module=0x01, address=2, value=5, type=ctypes.c_uint8)
    time.sleep(5)

    comm.close()


def example_readwrite():

    reset_uart()
    comm = TWIPR_Communication_STM32()
    comm.start()

    comm.write(module=0x01, address=2, value=40, type=ctypes.c_uint8)
    time.sleep(0.1)
    value = comm.read(module=0x01, address=2, type=ctypes.c_uint8)
    print(value)
    comm.close()


def example_read():
    comm = TWIPR_Communication_STM32()
    comm.start()

    x = comm.read(address=1, type=INT8)
    print(f"{x=}")
    time.sleep(1)

    comm.close()


def example_function():
    class struct_trajectory(ctypes.Structure):
        _fields_ = [('step', ctypes.c_uint16), ('id', ctypes.c_uint16), ("length", ctypes.c_uint16)]

    comm = TWIPR_Communication_STM32()
    comm.start()

    data = struct_trajectory(step=0, id=5, length=500)
    comm.function(module=0x02, address=5, data=data, input_type=struct_trajectory, output_type=None)
    time.sleep(1)
    comm.close()


if __name__ == '__main__':
    # example_serial_communication()
    # example_read()
    # example_function()
    # example_write()
    example_readwrite()
