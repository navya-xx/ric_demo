import time

import numpy as np

from applications.ideenexpo.src.twipr_manager import TWIPR_Manager
from device_manager.devices.robots.twipr.twipr import TWIPR
from extensions.joystick.joystick_manager import Joystick


def streamCallback(stream, device, *args, **kwargs):
    print(
        f"Data received from {device.information.device_id} with theta = {np.rad2deg(stream.data['estimation']['state']['theta'])}")


def robot_manager_example_1():
    max_forward_torque_cmd = 0.10
    max_turning_torque_cmd = 0.10
    robot: TWIPR = None
    joystick: Joystick = None

    manager = TWIPR_Manager()
    manager.init()
    manager.start()

    def new_robot_callback(new_robot, *args, **kwargs):
        nonlocal robot
        if new_robot.device.information.device_id == 'twipr2':
            robot = new_robot

    def new_joystick_callback(new_joystick, *args, **kwargs):
        nonlocal joystick
        joystick = new_joystick

    manager.registerCallback('new_joystick', new_joystick_callback)
    manager.registerCallback('new_robot', new_robot_callback)
    manager.registerCallback('stream', streamCallback)

    # manager.registerCallback('stream', streamCallback)

    while True:
        if robot is not None and joystick is not None:
            if joystick.uuid not in manager.joystick_assignments.keys():
                manager.assignJoystick(robot, joystick)
            else:
                val1 = joystick.axis[1] * max_forward_torque_cmd
                val2 = joystick.axis[2] * max_turning_torque_cmd
                if robot.device.connection.connected:
                    robot.setInput([val1 + val2, val1 - val2])
        time.sleep(0.1)


if __name__ == '__main__':
    robot_manager_example_1()
