import logging

from core.device_manager import DeviceManager
from core.devices.device import Device
from robots.twipr.twipr import TWIPR
from extensions.optitrack.optitrack import OptiTrack
from utils.logging import Logger
from applications.ric_demo.simulation.src.twipr_data import TWIPR_Control_Mode

logger = Logger('Robots')
logger.setLevel('INFO')


class TWIPR_Manager:
    deviceManager: DeviceManager
    optitrack: OptiTrack

    callbacks: dict
    robots: dict[str, TWIPR]

    def __init__(self, optitrack: bool = False):

        self.deviceManager = DeviceManager()

        if optitrack:
            self.optitrack = OptiTrack(settings.optitrack['server_address'],
                                       settings.optitrack['local_address'],
                                       settings.optitrack['multicast_address'])
        else:
            self.optitrack = None

        self.deviceManager.registerCallback('new_device', self._newDevice_callback)
        self.deviceManager.registerCallback('device_disconnected', self._deviceDisconnected_callback)
        self.deviceManager.registerCallback('stream', self._deviceStream_callback)

        if self.optitrack is not None:
            self.optitrack.registerCallback('new_frame', self._newOptiTrackFrame_callback)

        self.robots = {}

        self.callbacks = {
            'new_robot': [],
            'robot_disconnected': [],
            'stream': []
        }

    # === METHODS ======================================================================================================
    def registerCallback(self, callback_id, callback):
        if callback_id in self.callbacks.keys():
            self.callbacks[callback_id].append(callback)
        else:
            raise Exception(f"No callback with id {callback_id} is known.")

    # ------------------------------------------------------------------------------------------------------------------
    def init(self):
        self.deviceManager.init()

        if self.optitrack is not None:
            self.optitrack.init()

    # ------------------------------------------------------------------------------------------------------------------
    def start(self):
        self.deviceManager.start()

        if self.optitrack is not None:
            self.optitrack.start()
        # self._thread.start()

    # ------------------------------------------------------------------------------------------------------------------
    def emergencyStop(self):
        print("Emergency Stop!")
        for robot in self.robots.values():
            # self.setRobotControlMode(robot_id, "off")
            robot.setControlMode(TWIPR_Control_Mode.TWIPR_CONTROL_MODE_OFF)

    # ------------------------------------------------------------------------------------------------------------------
    def setRobotControlMode(self, robot, mode):
        if isinstance(robot, str):
            if robot in self.robots.keys():
                robot = self.robots[robot]
            else:
                return

        if isinstance(mode, str):
            control_mode_dict = {"off": 0, "direct": 1, "balancing": 2, "speed": 3}
            if mode in control_mode_dict.keys():
                mode = control_mode_dict[mode]
            else:
                return

        robot.setControlMode(mode)

    # === PRIVATE METHODS ==============================================================================================
    def _newDevice_callback(self, device: Device, *args, **kwargs):

        # Check if the device has the correct class and type
        if not (device.information.device_class == 'robot' and device.information.device_type == 'twipr'):
            return

        robot = TWIPR(device)

        # Check if the robot is in the list of known robot IDs, so that we can later assign the correct properties
        # if robot.device.information.device_id not in settings.agents.keys():
        #     logging.warning(
        #         f"New Robot ({robot.device.information.device_class}/{robot.device.information.device_type}) connected, but with "
        #         f"unknown id {robot.device.information.device_id}")
        #     return

        # Check if this robot ID is already used
        if robot.device.information.device_id in self.robots.keys():
            logging.warning(f"New Robot connected, but ID {robot.device.information.device_id} is already in use")

        self.robots[robot.device.information.device_id] = robot

        logger.info(f"New Robot connected with ID: \"{robot.device.information.device_id}\"")

        for callback in self.callbacks['new_robot']:
            callback(robot, *args, **kwargs)

    # ------------------------------------------------------------------------------------------------------------------
    def _deviceDisconnected_callback(self, device, *args, **kwargs):
        if device.information.device_id not in self.robots:
            return

        robot = self.robots[device.information.device_id]
        self.robots.pop(device.information.device_id)

        logger.info(f"Robot {device.information.device_id} disconnected")

        # Remove any joystick assignments
        for callback in self.callbacks['robot_disconnected']:
            callback(robot, *args, **kwargs)

    # ------------------------------------------------------------------------------------------------------------------
    def _newOptiTrackFrame_callback(self, rigidBodyId, position, orientation, *args, **kwargs):

        # Check if this OptiTrack RigidBodyID is in use
        for agent_id in self.robots:
            if rigidBodyId == settings.agents[agent_id]['optitrack_id']:
                ...

    def _deviceStream_callback(self, stream, device, *args, **kwargs):
        if device.information.device_id in self.robots.keys():
            for callback in self.callbacks['stream']:
                callback(stream, self.robots[device.information.device_id], *args, **kwargs)

    # ------------------------------------------------------------------------------------------------------------------
