import copy
import dataclasses
import math

import numpy as np

from cm4_core_old.utils.joystick import rpi_joystick
from robot.TWIPR import settings
from robot.TWIPR.control.twipr_control import TWIPR_Control_Sample, TWIPR_Control_Mode
from robot.TWIPR.logging.twipr_sample import TWIPR_Sample
from robot.TWIPR.twipr import TWIPR
import time
import logging

from RPi import GPIO

from cm4_core_old.utils.stm32.stm32 import stm32_reset

from robot.TWIPR.communication.wifi.sample import twipr_wifi_sample

logging.basicConfig(level=logging.DEBUG)

# K = [0.035, 0.06, 0.01, 0.011,
#      0.035, 0.06, 0.01, -0.011]


K = [0.035, 0.06, 0.01, 0.009,
     0.035, 0.06, 0.01, -0.009]


def example_twipr_device_1():
    twipr = TWIPR()
    twipr.init()
    twipr.start()
    v = 0
    time_start = time.time()
    while True:
        if twipr.communication.wifi.interface.connected:
            sample = copy.deepcopy(twipr_wifi_sample)

            sample['general']['time'] = float(time.time())
            sample['general']['id'] = 'twipr1'
            sample['general']['name'] = 'TWIPR 1'

            v = v + 0.1
            sample['estimation']['state']['v'] = v
            sample['estimation']['state']['x'] = -1.0
            sample['estimation']['state']['y'] = -4.0
            sample['estimation']['state']['theta'] = 2 * math.pi / 2
            twipr.communication.wifi.interface.sendStreamMessage(sample)
            time.sleep(0.1)


def example_twipr_2():
    twipr = TWIPR()
    twipr.init()
    twipr.start()

    twipr.control._setStateFeedbackGain_LL(K)

    while True:
        time.sleep(1)


def printStuff():
    print("HELLO TWIPR")


def joystick_control_with_offset():
    # max_forward_torque_cmd = 0.04
    # max_turning_torque_cmd = 0.05
    max_forward_torque_cmd = 0.06
    max_turning_torque_cmd = 0.08
    offset = 0
    twipr = TWIPR()
    twipr.init()
    twipr.start()

    def buttonA():
        print(f"Set Control Mode to {TWIPR_Control_Mode.TWIPR_CONTROL_MODE_BALANCING}")
        twipr.control._setControlMode_LL(TWIPR_Control_Mode.TWIPR_CONTROL_MODE_BALANCING)

    def buttonB():
        print(f"Set Control Mode to {TWIPR_Control_Mode.TWIPR_CONTROL_MODE_OFF}")
        twipr.control._setControlMode_LL(TWIPR_Control_Mode.TWIPR_CONTROL_MODE_OFF)

    # twipr.control._setStateFeedbackGain_LL(K)

    time.sleep(1)

    joystick = rpi_joystick.RpiJoystick()
    joystick.set_callback(event=rpi_joystick.A, callback=buttonA)
    joystick.set_callback(event=rpi_joystick.B, callback=buttonB)

    #
    while True:
        val1 = joystick.axes[1] * (-max_forward_torque_cmd) + offset
        val2 = joystick.axes[2] * max_turning_torque_cmd
        twipr.control._setControlInput_LL([val1 + val2, val1 - val2])
        time.sleep(0.1)


def printStuff(*args, **kwargs):
    print("HELLO I AM A TWIPR")


def comm_test():
    # stm32_reset(0.25)
    # time.sleep(2)
    twipr = TWIPR()
    twipr.init()
    twipr.start()

    def rx_samples(samples, *args, **kwargs):
        sample = samples[0]
        print(f"Got {len(samples)} Samples. Tick= {sample['general']['tick']}")
        # print("TEST")
        print(f"{np.rad2deg(sample['estimation']['state']['theta'])}")

    twipr.communication.registerCallback('rx_samples', rx_samples)

    state = 1
    while True:
        twipr.communication.serial.debug(state)
        state = not state
        time.sleep(0.25)


if __name__ == '__main__':
    example_twipr_2()
    # example_twipr_device_1()
    # printStuff()
    # joystick_control_with_offset()

    # test_comm()
