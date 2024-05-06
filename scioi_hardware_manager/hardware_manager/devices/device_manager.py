import logging

from hardware_manager.communication.tcp_server import TCP_Server
from hardware_manager.devices.device import Device
from hardware_manager.utils.utils import Callback

logger = logging.getLogger('device')
logger.setLevel('INFO')


class DeviceManager:
    server: TCP_Server

    devices: dict[str, Device]

    callbacks: dict[str, list[Callback]]

    # === INIT =========================================================================================================
    def __init__(self):

        self.devices = {}

        self.callbacks = {
            'new_device': [],
            'device_disconnected': [],
        }

        self.server = TCP_Server()
        self.server.registerCallback('connected', self._newConnection_callback)

        self._unregistered_devices = []

    # === METHODS ======================================================================================================
    def registerCallback(self, callback_id, callback):
        if callback_id in self.callbacks.keys():
            self.callbacks[callback_id].append(callback)
        else:
            raise Exception(f"TCP Device: No callback with id {callback_id} is known.")

    # ------------------------------------------------------------------------------------------------------------------
    def init(self):
        ...
    
    # ------------------------------------------------------------------------------------------------------------------
    def start(self):
        logger.info(f"Starting Device Manager")
        self.server.start()

    # === PRIVATE METHODS ==============================================================================================
    def _newConnection_callback(self, connection):

        # Make a new generic device with the connection
        device = Device()
        device.connection = connection

        # Append this device to the unregistered devices, since it has not yet sent an identification message
        self._unregistered_devices.append(device)

        device.registerCallback('registered', self._deviceRegistered_callback)
        device.registerCallback('disconnected', self._deviceDisconnected_callback)
        logger.debug(f"New device connected. Address: {device.connection.address}, IP: {device.connection.ip}")

    # ------------------------------------------------------------------------------------------------------------------
    def _deviceRegistered_callback(self, device):

        logger.info(f'New device registered. Name: {device.name} ({device.device_class}/{device.device_type})')
        for callback in self.callbacks['new_device']:
            callback(device=device)

    # ------------------------------------------------------------------------------------------------------------------
    def _deviceDisconnected_callback(self, device):
        ...

    # ------------------------------------------------------------------------------------------------------------------

    # ------------------------------------------------------------------------------------------------------------------
