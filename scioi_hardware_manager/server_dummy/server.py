import logging
import threading

from device_manager.devices.device import Device
from device_manager.utils.utils import Callback


class HardwareManagerDummy:
    _thread: threading.Thread

    devices: dict[str, Device]
    callbacks: dict[str, list[Callback]]

    def __init__(self):

        self.devices = {}

        self.callbacks = {
            'new_device': [],
            'device_disconnected': [],
        }

    # === METHODS ======================================================================================================

    def registerCallback(self, callback_id, callback):
        if callback_id in self.callbacks.keys():
            self.callbacks[callback_id].append(callback)
        else:
            raise Exception(f"TCP Device: No callback with id {callback_id} is known.")

    # ------------------------------------------------------------------------------------------------------------------
    def start(self):
        ...

    # ------------------------------------------------------------------------------------------------------------------
    def addNewDevice(self, device: Device):

        self.devices[device.information.device_id] = device
        device.connection.registered = True

        print(f"Add new device: {device.information.device_id}. Info:{device.information}")

        for callback in self.callbacks['new_device']:
            callback(device=device)

    # ------------------------------------------------------------------------------------------------------------------
    def removeDevice(self, device_id):
        device = self.devices[device_id]
        device.connection.registered = False
        self.devices.pop(device_id)

        for callback in self.callbacks['device_disconnected']:
            callback(device=device)

    # ------------------------------------------------------------------------------------------------------------------
    def _threadFunction(self):
        ...
