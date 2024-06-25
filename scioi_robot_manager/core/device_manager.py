import logging
import time

from core.communication.protocols.tcp.tcp_json_protocol import TCP_JSON_Message
from core.communication.tcp_server import TCP_Server
from core.devices.device import Device
from robots.twipr.twipr import TWIPR
from core.utils.callbacks import Callback

logger = logging.getLogger('device')
logger.setLevel('INFO')

known_devices = {
    'robot': {
        'twipr': TWIPR
    }
}


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
            'stream': [],
        }

        self.server = TCP_Server()
        self.server.registerCallback('connected', self._newConnection_callback)

        self._unregistered_devices = []

    # === METHODS ======================================================================================================
    def registerCallback(self, callback_id, callback):
        if callback_id in self.callbacks.keys():
            self.callbacks[callback_id].append(callback)
        else:
            raise Exception(f"No callback with id {callback_id} is known.")

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

        # TODO: If the device is in the list of known devices, then it shuld be converted to one of these
        if device.information.device_class in known_devices.keys():
            if device.information.device_type in known_devices[device.information.device_class].keys():
                ...

        logger.info(
            f'New device registered. Name: {device.information.device_name} ({device.information.device_class}/{device.information.device_type})')

        self._sendSyncMessage(device)

        device.registerCallback('stream', self._deviceStreamCallback)

        for callback in self.callbacks['new_device']:
            callback(device=device)

    # ------------------------------------------------------------------------------------------------------------------
    def _deviceDisconnected_callback(self, device):
        logger.info(
            f'Device disconnected. Name: {device.information.device_name} ({device.information.device_class}/{device.information.device_type})')
        for callback in self.callbacks['device_disconnected']:
            callback(device=device)

    # ------------------------------------------------------------------------------------------------------------------
    def _deviceStreamCallback(self, stream, device, *args, **kwargs):
        for callback in self.callbacks['stream']:
            callback(stream, device, *args, **kwargs)

    # ------------------------------------------------------------------------------------------------------------------
    def _sendSyncMessage(self, device: Device):
        message = TCP_JSON_Message()

        message.type = 'event'
        message.event = 'sync'
        message.data = {
            'time': time.time()
        }

        device.send(message)

