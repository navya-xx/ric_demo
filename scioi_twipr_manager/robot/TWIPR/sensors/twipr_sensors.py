import dataclasses

from robot.TWIPR.communication.twipr_communication import TWIPR_Communication


@dataclasses.dataclass
class TWIPR_Sensors_IMU:
    gyr: dict = dataclasses.field(default_factory=dict)
    acc: dict = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class TWIPR_Sensors_Power:
    bat_voltage: float = 0
    bat_current: float = 0


@dataclasses.dataclass
class TWIPR_Sensors_Drive_Data:
    speed: float = 0
    torque: float = 0
    slip: bool = False


@dataclasses.dataclass
class TWIPR_Sensors_Drive:
    left: TWIPR_Sensors_Drive_Data = dataclasses.field(default_factory=TWIPR_Sensors_Drive_Data)
    right: TWIPR_Sensors_Drive_Data = dataclasses.field(default_factory=TWIPR_Sensors_Drive_Data)


@dataclasses.dataclass
class TWIPR_Sensors_Distance:
    front: float = 0
    back: float = 0


@dataclasses.dataclass
class TWIPR_Sensors_Sample:
    imu: TWIPR_Sensors_IMU = dataclasses.field(default_factory=TWIPR_Sensors_IMU)
    power: TWIPR_Sensors_Power = dataclasses.field(default_factory=TWIPR_Sensors_Power)
    drive: TWIPR_Sensors_Drive = dataclasses.field(default_factory=TWIPR_Sensors_Drive)
    distance: TWIPR_Sensors_Distance = dataclasses.field(default_factory=TWIPR_Sensors_Distance)


class TWIPR_Sensors:
    _comm: TWIPR_Communication

    imu: TWIPR_Sensors_IMU
    power: TWIPR_Sensors_Power
    drive: TWIPR_Sensors_Drive
    distance: TWIPR_Sensors_Distance

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self, comm: TWIPR_Communication):
        self._comm = comm
        self._comm.registerCallback('rx_sample', self._onSample)

        self.imu = TWIPR_Sensors_IMU(gyr={'x':0, 'y': 0, 'z': 0}, acc={'x':0, 'y': 0, 'z': 0})
        self.power = TWIPR_Sensors_Power(bat_voltage=0, bat_current=0)
        self.drive = TWIPR_Sensors_Drive()
        self.distance = TWIPR_Sensors_Distance()

    # ------------------------------------------------------------------------------------------------------------------
    def getSample(self):
        sample = TWIPR_Sensors_Sample()
        sample.imu = self.imu
        sample.drive = self.drive
        sample.power.bat_voltage = 14.57
        return sample

    # ------------------------------------------------------------------------------------------------------------------
    def _onSample(self, sample, *args, **kwargs):
        self.imu.gyr = sample['sensors']['gyr']
        self.imu.acc = sample['sensors']['acc']
        self.drive.left = sample['sensors']['speed_left']
        self.drive.right = sample['sensors']['speed_right']
        self.power.bat_voltage = sample['sensors']['battery_voltage']
        self.power.bat_current = 0
        self.distance.front = 0
        self.distance.back = 0

    # ------------------------------------------------------------------------------------------------------------------
    def _readImu(self):
        ...

    # ------------------------------------------------------------------------------------------------------------------
    def _readPower(self):
        ...

    # ------------------------------------------------------------------------------------------------------------------
    def _readDrive(self):
        ...
