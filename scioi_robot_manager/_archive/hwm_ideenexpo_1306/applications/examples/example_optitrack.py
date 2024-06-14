import time

from applications.robot_manager import RobotManager
from device_manager.devices.robots.twipr.twipr import TWIPR
from extensions.joystick.joystick_manager import Joystick


def main():
    manager = RobotManager(optitrack=True)

    manager.init()
    manager.start()

    while True:
        time.sleep(1)


if __name__ == '__main__':
    main()
