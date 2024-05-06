import time

from hardware_manager.manager import HardwareManager


def run_hardware_manager():
    hardware_manager = HardwareManager()
    hardware_manager.start()

    while True:
        time.sleep(1)


if __name__ == '__main__':
    run_hardware_manager()
