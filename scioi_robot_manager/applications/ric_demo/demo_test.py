import time

from applications.ric_demo.simulation.src.dummy_device import DummyDevice
from applications.ric_demo.simulation.src.twipr_data import buildSample
from applications.ric_demo.robots_demo.ric_demo_manager import RIC_Demo_RobotManager
from utils.logging import Logger

logger = Logger('RIC')

dummy_twipr_device = DummyDevice()
dummy_robot = None


def printSend(msg, *args, **kwargs):
    ...


def main():
    global dummy_robot
    dummy_twipr_device.registerCallback('dummy_send', printSend)

    logger.info("Starting RIC Demo")
    manager = RIC_Demo_RobotManager()
    manager.init()
    manager.start()

    time.sleep(5)
    manager.robotManager.deviceManager._deviceRegistered_callback(dummy_twipr_device)

    while True:

        if 'twipr6' in manager.robotManager.robots.keys():
            if dummy_robot is None:
                dummy_robot = manager.robotManager.robots['twipr6']

            manager.robotManager.robots['twipr6'].setInput([1, 1])
            sample = buildSample()
            dummy_robot.device.dummyStream(sample)
        time.sleep(1)


if __name__ == '__main__':
    main()
