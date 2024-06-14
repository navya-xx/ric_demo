import time

from manager import HardwareManager


def stream_callback(stream, device, *args, **kwargs):
    print("X")


def new_robot(robot, *args, **kwargs):
    print(f"New Robot connected ({robot.information.device_name})")


def robot_disconnected(robot, *args, **kwargs):
    ...


def run_hardware_manager():
    hardware_manager = HardwareManager()
    hardware_manager.start()

    hardware_manager.registerCallback('stream', stream_callback)
    hardware_manager.registerCallback('robot_connected', new_robot)

    while True:
        time.sleep(1)


if __name__ == '__main__':
    run_hardware_manager()
