import ctypes
import logging
import time

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

    x = test_struct(a=99, b=-88888)
    comm.echo(address=0x0102, value=x, type=test_struct, flag=3)
    time.sleep(60)

    comm.close()


def example_read():
    comm = TWIPR_Communication_STM32()
    comm.start()

    x = comm.read(address=1, type=INT8)
    print(f"{x=}")
    time.sleep(1)

    comm.close()


def example_function():
    comm = TWIPR_Communication_STM32()
    comm.start()

    x = comm.function(address=3, data=12.7, input_type=FLOAT, output_type=FLOAT, timeout=5)
    print(f"{x=}")
    time.sleep(1)

    comm.close()


if __name__ == '__main__':
    example_serial_communication()
    # example_read()
    # example_function()
