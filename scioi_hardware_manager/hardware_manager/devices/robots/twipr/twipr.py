import dataclasses

from hardware_manager.devices.device import Device


@dataclasses.dataclass
class TWIPR_Data:
    ...


class TWIPR(Device):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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

    # === PARAMETERS =========================================================================
    def setControlMode(self, mode):
        ...

    def setInput(self, input):
        ...

    def setLEDs(self, color):
        ...

    def setTestParameter(self, value):
        ...

    def setSpeed(self, v, psi_dot):
        ...




