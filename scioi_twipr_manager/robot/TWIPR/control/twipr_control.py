import ctypes
import dataclasses
import enum
import logging
import threading
import time

from control_board.robot_control_board import RobotControl_Board
from robot.TWIPR.communication.twipr_communication import TWIPR_Communication
import robot.TWIPR.settings as settings
import robot.TWIPR.control.serial_communication_control as serial_communication_control

logger = logging.getLogger('control')
logger.setLevel('INFO')


@dataclasses.dataclass
class TWIPR_Balancing_Control_Config:
    available: bool = False
    K: list = dataclasses.field(default_factory=list)  # State Feedback Gain
    u_lim: list = dataclasses.field(default_factory=list)  # Input Limits
    external_input_gain: list = dataclasses.field(
        default_factory=list)  # When using balancing control without speed control, this can scale the external input


@dataclasses.dataclass
class TWIPR_PID_Control_Config:
    Kp: float = 0
    Kd: float = 0
    Ki: float = 0
    anti_windup: float = 0
    integrator_saturation: float = None


@dataclasses.dataclass
class TWIPR_Speed_Control_Config:
    available: bool = False
    v: TWIPR_PID_Control_Config = dataclasses.field(default_factory=TWIPR_PID_Control_Config)
    psidot: TWIPR_PID_Control_Config = dataclasses.field(default_factory=TWIPR_PID_Control_Config)
    external_input_gain: list = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class TWIPR_Control_Config:
    name: str = ''
    description: str = ''
    balancing_control: TWIPR_Balancing_Control_Config = dataclasses.field(
        default_factory=TWIPR_Balancing_Control_Config)
    speed_control: TWIPR_Speed_Control_Config = dataclasses.field(default_factory=TWIPR_Speed_Control_Config)


class TWIPR_Control_Mode(enum.IntEnum):
    TWIPR_CONTROL_MODE_OFF = 0,
    TWIPR_CONTROL_MODE_DIRECT = 1,
    TWIPR_CONTROL_MODE_BALANCING = 2,
    TWIPR_CONTROL_MODE_VELOCITY = 3,
    TWIPR_CONTROL_MODE_POS = 4


class TWIPR_Control_Status(enum.IntEnum):
    TWIPR_CONTROL_STATE_ERROR = 0
    TWIPR_CONTROL_STATE_NORMAL = 1


class TWIPR_Control_Status_LL(enum.IntEnum):
    TWIPR_CONTROL_STATE_LL_ERROR = 0
    TWIPR_CONTROL_STATE_LL_NORMAL = 1


class TWIPR_Control_Mode_LL(enum.IntEnum):
    TWIPR_CONTROL_MODE_LL_OFF = 0,
    TWIPR_CONTROL_MODE_LL_DIRECT = 1,
    TWIPR_CONTROL_MODE_LL_BALANCING = 2,
    TWIPR_CONTROL_MODE_LL_VELOCITY = 3


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


class TWIPR_Control:
    _comm: TWIPR_Communication

    status: TWIPR_Control_Status
    mode: TWIPR_Control_Mode
    mode_ll: TWIPR_Control_Mode_LL
    status_ll: TWIPR_Control_Status_LL

    input: TWIPR_Control_Input

    _thread: threading.Thread

    def __init__(self, comm: TWIPR_Communication):
        self._comm = comm

        self.status = TWIPR_Control_Status(TWIPR_Control_Status.TWIPR_CONTROL_STATE_ERROR)
        self.mode = TWIPR_Control_Mode(TWIPR_Control_Mode.TWIPR_CONTROL_MODE_OFF)
        self.status_ll = TWIPR_Control_Status_LL(TWIPR_Control_Status_LL.TWIPR_CONTROL_STATE_LL_ERROR)
        self.mode_ll = TWIPR_Control_Mode_LL(TWIPR_Control_Mode_LL.TWIPR_CONTROL_MODE_LL_OFF)
        self.input = TWIPR_Control_Input()

        self._comm.registerCallback('rx_sample', self._onSample)

        self._comm.wifi.addCommand(identifier='setControlMode', callback=self.setMode, arguments=['mode'],
                                   description='Sets the control mode')
        self._comm.wifi.addCommand(identifier='setControlInput', callback=self.setInput, arguments=['input'],
                                   description='Sets the Input')

        self._thread = threading.Thread(target=self._threadFunction)

    # ==================================================================================================================
    def init(self):
        ...

    def joystart(self):
        self._thread.start()

    def loadConfig(self, name):
        ...

    # ------------------------------------------------------------------------------------------------------------------
    def saveConfig(self, name, config=None):
        ...

    # ------------------------------------------------------------------------------------------------------------------
    def setMode(self, mode: (int, TWIPR_Control_Mode)):
        if isinstance(mode, int):
            try:
                mode = TWIPR_Control_Mode(mode)
            except ValueError:
                logger.warning(f"Value of {mode} is not a valid control mode")
                return

        if mode == TWIPR_Control_Mode.TWIPR_CONTROL_MODE_OFF:
            self._setControlMode_LL(TWIPR_Control_Mode_LL.TWIPR_CONTROL_MODE_LL_OFF)
        elif mode == TWIPR_Control_Mode.TWIPR_CONTROL_MODE_BALANCING:
            self._setControlMode_LL(TWIPR_Control_Mode_LL.TWIPR_CONTROL_MODE_LL_BALANCING)

    # ------------------------------------------------------------------------------------------------------------------
    def setInput(self, input):
        if not isinstance(input, list):
            logger.error("Wrong Input Datatype")
            return
        self._setControlInput_LL(input)

    # ------------------------------------------------------------------------------------------------------------------
    def setSpeed(self, v, psi_dot):
        ...

    # ------------------------------------------------------------------------------------------------------------------
    def setStateFeedbackGain(self, K):
        self._setStateFeedbackGain_LL(K)

    # ------------------------------------------------------------------------------------------------------------------
    def setVelocityController(self):
        ...

    # ------------------------------------------------------------------------------------------------------------------
    def getSample(self) -> TWIPR_Control_Sample:
        sample = TWIPR_Control_Sample()
        sample.status = self.status
        sample.mode = self.mode
        sample.configuration = ''
        sample.input = TWIPR_Control_Input()

        return sample

    # = PRIVATE METHODS ================================================================================================
    def _threadFunction(self):
        while True:
            self._update()
            time.sleep(0.01)

    def _update(self):
        # Check the LL state

        # TODO: This is a stupid idea
        if self.status_ll == TWIPR_Control_Status_LL.TWIPR_CONTROL_STATE_LL_ERROR:
            self.status = TWIPR_Control_Status.TWIPR_CONTROL_STATE_ERROR
        elif self.status_ll == TWIPR_Control_Status_LL.TWIPR_CONTROL_STATE_LL_NORMAL:
            self.status = TWIPR_Control_Status.TWIPR_CONTROL_STATE_NORMAL

        if self.mode_ll == TWIPR_Control_Mode_LL.TWIPR_CONTROL_MODE_LL_OFF:
            self.mode = TWIPR_Control_Mode.TWIPR_CONTROL_MODE_OFF
        elif self.mode_ll == TWIPR_Control_Mode_LL.TWIPR_CONTROL_MODE_LL_BALANCING:
            self.mode = TWIPR_Control_Mode.TWIPR_CONTROL_MODE_BALANCING

    # ------------------------------------------------------------------------------------------------------------------
    def _onSample(self, sample):
        self.status_ll = TWIPR_Control_Status_LL(sample['control']['status'])
        self.mode_ll = TWIPR_Control_Mode_LL(sample['control']['mode'])
        self.input.input = 0  # TODO
        self.input.input_ext = 0  # TODO
        self.input.v_cmd = 0  # TODO
        self.input.psi_dot_cmd = 0  # TODO

    # ------------------------------------------------------------------------------------------------------------------
    def _setControlMode_LL(self, mode):
        mode_data = 0
        if mode == TWIPR_Control_Mode.TWIPR_CONTROL_MODE_OFF:
            mode_data = 0
        elif mode == TWIPR_Control_Mode.TWIPR_CONTROL_MODE_BALANCING:
            mode_data = 2

        self._comm.serial.executeFunction(module=settings.REGISTER_TABLE_CONTROL,
                                          address=serial_communication_control.ADDRESS_CONTROL_MODE,
                                          data=mode_data,
                                          input_type=ctypes.c_uint8)

    # ------------------------------------------------------------------------------------------------------------------
    def _readControlMode_LL(self):
        ...

    # ------------------------------------------------------------------------------------------------------------------
    def _readControlState_LL(self):
        ...

    # ------------------------------------------------------------------------------------------------------------------
    def _setStateFeedbackGain_LL(self, K):
        assert (isinstance(K, list))
        assert (len(K) == 8)
        assert (all(isinstance(elem, (float, int)) for elem in K))

        self._comm.serial.executeFunction(module=settings.REGISTER_TABLE_CONTROL,
                                          address=serial_communication_control.ADDRESS_CONTROL_K,
                                          data=K,
                                          input_type=ctypes.c_float,
                                          output_type=None)

    # ------------------------------------------------------------------------------------------------------------------
    def _setVelocityControl_LL(self):
        ...

    # ------------------------------------------------------------------------------------------------------------------
    def _readControlConfig_LL(self):
        ...

    # ------------------------------------------------------------------------------------------------------------------
    def _setControlInput_LL(self, input):
        assert (isinstance(input, list))
        assert (len(input) == 2)
        assert (all(isinstance(elem, (float, int)) for elem in input))

        input_struct = serial_communication_control.twipr_control_input(u1=input[0], u2=input[1])

        self._comm.serial.executeFunction(module=settings.REGISTER_TABLE_CONTROL,
                                          address=serial_communication_control.ADDRESS_CONTROL_INPUT,
                                          data=input_struct,
                                          input_type=serial_communication_control.twipr_control_input)

    # ------------------------------------------------------------------------------------------------------------------
