import threading

from cm4_core.interface.interface import WifiInterface
from cm4_core.interface.data_link import DataLink
from control_board.rc_board import RobotControl_Device


class TankRobot:
    interface: WifiInterface
    board: RobotControl_Device
    _thread: threading.Thread

    # === INIT =========================================================================================================
    def __init__(self):
        ...

        # TODO: This should done different and is only for KISS for David's defence
        self.motors = {
            'left': 0,
            'right': 0
        }

        self.interface.data['motors'] = {

            'left': DataLink(identifier='left',
                             description='Percentage of left motor speed',
                             limits=[-1, 1],
                             datatype=float,
                             obj=self.motors,
                             name='left'),

            'right': DataLink(identifier='right',
                              description='Percentage of right motor speed',
                              limits=[-1, 1],
                              datatype=float,
                              obj=self.motors,
                              name='right'),
        }

    # === METHODS ======================================================================================================
    def setSpeed(self, left, right):
        ...

    # === PRIVATE METHODS ==============================================================================================
    def _robot_thread(self):
        ...
