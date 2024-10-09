import sys
sys.path.append("/home/lehmann/software/")

import time
from robot.TWIPR_old.simple.simple_twipr import SimpleTWIPR
import cm4_core_old.utils.joystick.rpi_joystick as rpi_joystick




Ts = 0.01

K = [0.025, 0.04, 0.007, 0.012,
     0.025, 0.04, 0.007, -0.012]

K = [0.035, 0.06, 0.01, 0.011,
     0.035, 0.06, 0.01, -0.011]
# K = [0.025, 0.05, 0.010, 0.010,
#      0.025, 0.05, 0.010, -0.010]

# offset = +0.0033
offset = +0.0

max_forward_torque_cmd = 0.05
max_turning_torque_cmd = 0.08


def joystick_control_with_offset():
    twipr = SimpleTWIPR(K)

    joystick = rpi_joystick.RpiJoystick()
    joystick.set_callback(event=rpi_joystick.A, callback=twipr.startBalancing)
    joystick.set_callback(event=rpi_joystick.B, callback=twipr.stopBalancing)

    while True:
        val1 = joystick.axes[1] * (-max_forward_torque_cmd) + offset
        val2 = joystick.axes[2] * max_turning_torque_cmd
        twipr.setInput([val1 + val2, val1 - val2])
        time.sleep(0.1)


def balance():
    twipr = SimpleTWIPR()
    twipr.startBalancing()
    time.sleep(10)
    twipr.stopBalancing()
    time.sleep(1)


if __name__ == '__main__':
    # print("HALLO TWIPR")
    joystick_control_with_offset()
    # balance()
