import logging

from hardware_manager.devices.device_manager import DeviceManager

logger = logging.getLogger('manager')
logger.setLevel('INFO')


class HardwareManager:
    device_manager: DeviceManager

    def __init__(self):
        self.device_manager = DeviceManager()

    def init(self):
        self.device_manager.init()

    def start(self):
        logger.info("Starting Hardware Manager")
        self.device_manager.start()
