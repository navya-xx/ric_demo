import copy
import dataclasses

from core.devices.device import Device
from core.devices.robots.twipr.twipr_data import twipr_wifi_sample


@dataclasses.dataclass
class TWIPR_Data:
    ...


class TWIPR:
    device: Device
    callbacks: dict

    def __init__(self, device: Device, *args, **kwargs):
        self.device = device

        self.callbacks = {
            'stream': []
        }

        self.device.registerCallback('stream', self._onStreamCallback)

    # === CLASS METHODS =====================================================================

    # === METHODS ============================================================================

    # === PROPERTIES ============================================================================
    @property
    def id(self):
        return self.device.information.device_id

    # === COMMANDS ===========================================================================
    def testFunction(self, data):
        ...

    def balance(self, state):
        ...

    def setControlConfiguration(self, config):
        ...

    def loadControlConfiguration(self, name):
        ...

    def saveControlConfiguration(self, name):
        ...

    def beep(self, time):
        ...

    def stop(self):
        ...

    def setControlMode(self, mode):
        self.device.command(command='setControlMode', data={'mode': mode})

    def setInput(self, input):
        self.device.command('setControlInput', data={'input': input})

    def setLEDs(self, color):
        ...

    def setTestParameter(self, value):
        ...

    def setSpeed(self, v, psi_dot):
        ...

    def _onStreamCallback(self, *args, **kwargs):
        ...
