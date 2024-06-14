import time

from applications.visionrobots.visionrobot_manager import VisionRobotManager

robot = None
joystick = None


def streamCallback(stream, device, *args, **kwargs):
    print(f"New Stream {stream}")


def example_1():
    def robot_connected_callback(new_robot, *args, **kwargs):
        global robot
        if new_robot.device.information.device_id == 'visionrobot1':
            robot = new_robot

    def joystick_connected_callback(new_joystick, *args, **kwargs):
        global joystick
        joystick = new_joystick

    manager = VisionRobotManager()
    manager.init()
    manager.start()

    manager.registerCallback('new_robot', robot_connected_callback)
    manager.registerCallback('new_joystick', joystick_connected_callback)
    manager.registerCallback('stream', streamCallback)

    while True:
        if robot is not None and joystick is not None:
            val1 = -joystick.axis[1]
            val2 = joystick.axis[2]
            speed_left = 0.5 * val1 + 0.5 * val2
            speed_right = 0.5 * val1 - 0.5 * val2
            robot.device.command('setSpeed', {'speed': [speed_left, speed_right]})
        time.sleep(0.1)


if __name__ == '__main__':
    example_1()
