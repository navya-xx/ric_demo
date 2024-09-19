import ctypes
import time

from robot.TWIPR.communication.twipr_comm_stm import TWIPR_Communication_STM32
from robot.TWIPR.communication.twipr_comm_utils import reset_uart


K = [0.02,0.04,0.005,0.02,
      0.02,0.04,0.005,-0.02]

def set_K(K):
    assert(isinstance(K, list))

    reset_uart()
    comm = TWIPR_Communication_STM32()
    comm.start()
    comm.function(module=0x02, address=8, data=K, input_type=ctypes.c_float, output_type=None)
    time.sleep(1)

def test_controller_on_off():
    reset_uart()
    comm = TWIPR_Communication_STM32()
    comm.start()
    comm.function(module=0x02, address=4, data=0, input_type=ctypes.c_uint8, output_type=None)
    time.sleep(1)


if __name__ == '__main__':
    set_K(K)
    test_controller_on_off()