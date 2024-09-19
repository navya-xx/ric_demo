import dataclasses
import enum

from robot.TWIPR.communication.twipr_communication import TWIPR_Communication


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


class TWIPR_Estimation:
    _comm: TWIPR_Communication

    state: TWIPR_Estimation_State
    status: TWIPR_Estimation_Status
    mode: TWIPR_Estimation_Mode

    def __init__(self, comm: TWIPR_Communication):
        self._comm = comm

        self.state = TWIPR_Estimation_State()

        self._comm.registerCallback('rx_sample', self._onSample)

    # ==================================================================================================================

    # ------------------------------------------------------------------------------------------------------------------
    def getSample(self) -> TWIPR_Estimation_Sample:
        sample = TWIPR_Estimation_Sample()
        sample.mode = None
        sample.status = None
        sample.state = self.state

        return sample

    # ==================================================================================================================
    def _update(self):
        ...

    def _onSample(self, sample, *args, **kwargs):
        self.state.v = sample['estimation']['state']['v']
        self.state.theta = sample['estimation']['state']['theta']
        self.state.theta_dot = sample['estimation']['state']['theta_dot']
        self.state.psi = sample['estimation']['state']['psi']
        self.state.psi_dot = sample['estimation']['state']['psi_dot']

    # ------------------------------------------------------------------------------------------------------------------
    def _readState_LL(self):
        ...

    # ------------------------------------------------------------------------------------------------------------------
