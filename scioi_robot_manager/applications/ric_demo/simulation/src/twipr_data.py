import dataclasses
import enum
import math
import time

import numpy as np
import orjson


@dataclasses.dataclass
class TWIPR_Sample_General:
    id: str = ''
    status: str = ''
    configuration: str = ''
    time: int = 0
    tick: int = 0
    sample_time: float = 0


class TWIPR_Control_Status(enum.IntEnum):
    TWIPR_CONTROL_STATE_ERROR = 0
    TWIPR_CONTROL_STATE_NORMAL = 1


class TWIPR_Control_Mode(enum.IntEnum):
    TWIPR_CONTROL_MODE_OFF = 0,
    TWIPR_CONTROL_MODE_DIRECT = 1,
    TWIPR_CONTROL_MODE_BALANCING = 2,
    TWIPR_CONTROL_MODE_VELOCITY = 3,
    TWIPR_CONTROL_MODE_POS = 4


@dataclasses.dataclass
class TWIPR_Control_Input:
    input_ext: list = dataclasses.field(default_factory=list)
    input: list = dataclasses.field(default_factory=list)
    v_cmd: float = 0
    psi_dot_cmd: float = 0


@dataclasses.dataclass
class TWIPR_Control_Sample:
    status: TWIPR_Control_Status = dataclasses.field(
        default=TWIPR_Control_Status(TWIPR_Control_Status.TWIPR_CONTROL_STATE_ERROR))
    mode: TWIPR_Control_Mode = dataclasses.field(default=TWIPR_Control_Mode(TWIPR_Control_Mode.TWIPR_CONTROL_MODE_OFF))
    configuration: str = ''
    input: TWIPR_Control_Input = dataclasses.field(default_factory=TWIPR_Control_Input)


@dataclasses.dataclass
class TWIPR_Estimation_State:
    x: float = 0
    y: float = 0
    v: float = 0
    theta: float = 0
    theta_dot: float = 0
    psi: float = 0
    psi_dot: float = 0


class TWIPR_Estimation_Status(enum.Enum):
    TWIPR_ESTIMATION_STATUS_ERROR = 0,
    TWIPR_ESTIMATION_STATUS_NORMAL = 1,


class TWIPR_Estimation_Mode(enum.Enum):
    TWIPR_ESTIMATION_MODE_VEL = 0,
    TWIPR_ESTIMATION_MODE_POS = 1


@dataclasses.dataclass
class TWIPR_Estimation_Sample:
    status: TWIPR_Estimation_Status = TWIPR_Estimation_Status.TWIPR_ESTIMATION_STATUS_ERROR
    state: TWIPR_Estimation_State = dataclasses.field(default_factory=TWIPR_Estimation_State)
    mode: TWIPR_Estimation_Mode = TWIPR_Estimation_Mode.TWIPR_ESTIMATION_MODE_VEL


class TWIPR_Drive_Status(enum.Enum):
    TWIPR_DRIVE_STATUS_OFF = 1,
    TWIPR_DRIVE_STATUS_ERROR = 0.
    TWIPR_DRIVE_STATUS_NORMAL = 2


@dataclasses.dataclass
class TWIPR_Drive_Data:
    status: TWIPR_Drive_Status = TWIPR_Drive_Status.TWIPR_DRIVE_STATUS_OFF
    torque: float = 0
    speed: float = 0
    input: float = 0


@dataclasses.dataclass
class TWIPR_Drive_Sample:
    left: TWIPR_Drive_Data = dataclasses.field(default_factory=TWIPR_Drive_Data)
    right: TWIPR_Drive_Data = dataclasses.field(default_factory=TWIPR_Drive_Data)


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


@dataclasses.dataclass
class TWIPR_Sample:
    general: TWIPR_Sample_General = dataclasses.field(default_factory=TWIPR_Sample_General)
    control: TWIPR_Control_Sample = dataclasses.field(default_factory=TWIPR_Control_Sample)
    estimation: TWIPR_Estimation_Sample = dataclasses.field(default_factory=TWIPR_Estimation_Sample)
    drive: TWIPR_Drive_Sample = dataclasses.field(default_factory=TWIPR_Drive_Sample)
    sensors: TWIPR_Sensors_Sample = dataclasses.field(default_factory=TWIPR_Sensors_Sample)


def buildSample():
    sample = TWIPR_Sample()

    sample.general.id = 'twipr6'
    sample.general.status = 0
    sample.general.configuration = ''
    sample.general.time = time.time()
    sample.general.tick = 0
    sample.general.sample_time = 0.1

    # sample.control = self.control.getSample()
    sample.estimation = TWIPR_Estimation_Sample()
    sample.estimation.status = 0
    sample.estimation.mode = 0
    sample.estimation.state = TWIPR_Estimation_State()
    sample.estimation.state.x = 1.5
    sample.estimation.state.y = 2
    sample.estimation.state.v = 1
    sample.estimation.state.theta = -1.2
    sample.estimation.state.theta_dot = 0
    sample.estimation.state.psi = float(np.rad2deg(math.pi/4))
    sample.estimation.state.psi_dot = 0

    sample.sensors.imu.acc = {
        'x': 0,
        'y': 0,
        'z': 0,
    }

    sample.sensors.imu.gyr = {
        'x': 0,
        'y': 0,
        'z': 0,
    }

    json_string = orjson.dumps(sample)
    sample = orjson.loads(json_string)


    return sample
