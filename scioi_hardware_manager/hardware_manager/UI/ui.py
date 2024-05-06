from hardware_manager.devices.device import Device
from hardware_manager.devices.device_manager import DeviceManager
from hardware_manager.utils.utils import Callback


class UI:
    qt_ui: type
    device_manager: DeviceManager

    callbacks: dict[str, list[Callback]]

    def __init__(self):

        self.device_manager.registerCallback('new_device', self._newDevice_callback)
        self.device_manager.registerCallback('device_disconnected', self._deviceDisconnected_callback)


        self.callbacks = {
            'test': [],
        }

    # === METHODS ======================================================================================================
    def registerCallback(self, callback_id, callback):
        if callback_id in self.callbacks.keys():
            self.callbacks[callback_id].append(callback)
        else:
            raise Exception(f"TCP Device: No callback with id {callback_id} is known.")
    # === PRIVATE METHODS ==============================================================================================
    def _newDevice_callback(self, device: Device, *args, **kwargs):
        ...
        for callback in self.callbacks['test']:
            callback(device)

    def _deviceDisconnected_callback(self, device: Device):
        ...