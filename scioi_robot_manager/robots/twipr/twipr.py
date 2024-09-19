import dataclasses

from core.devices.device import Device


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

    def setControlMode(self, mode, *args, **kwargs):
        print(f"Set control mode to {mode}")
        self.device.command(command='setControlMode', data={'mode': mode})

    def setInput(self, input, *args, **kwargs):
        # print(f"Input command to {self.device.information.device_id} as {input}")
        self.device.command('setControlInput', data={'input': input})

    def setLEDs(self, color):
        ...

    def setTestParameter(self, value):
        ...

    def setSpeed(self, v, psi_dot):
        ...

    def _onStreamCallback(self, stream, *args, **kwargs):

        ...

    def sendPosInfo(self, pos_dict: dict):
        self.device.command(command='getCurrentOrientation', data=pos_dict)

    def sendObstacleInfo(self, obs_dict: dict):
        self.device.command(command='getObstacles', data=obs_dict)