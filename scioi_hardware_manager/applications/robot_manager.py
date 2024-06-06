import logging
import threading
import time

from device_manager.device_manager import DeviceManager
from device_manager.devices.device import Device
from device_manager.devices.robots.twipr.twipr import TWIPR
from extensions.joystick.joystick_manager import JoystickManager
from extensions.optitrack.optitrack import OptiTrack
import applications.ideenexpo.settings as settings

logger = logging.getLogger('robot manager')
logger.setLevel('INFO')

# TODO: should be somewhere else
max_forward_torque_cmd = 0.10
max_turning_torque_cmd = 0.10


class RobotManager:
    deviceManager: DeviceManager
    joysticks: JoystickManager
    optitrack: OptiTrack

    callbacks: dict

    robots: dict[str, TWIPR]

    joystick_assignments: dict
    connected_joysticks: dict

    _thread: threading.Thread

    def __init__(self, optitrack: bool = False):

        self.deviceManager = DeviceManager()
        self.joysticks = JoystickManager()

        if optitrack:
            self.optitrack = OptiTrack(settings.optitrack['server_address'],
                                       settings.optitrack['local_address'],
                                       settings.optitrack['multicast_address'])
        else:
            self.optitrack = None

        self.joysticks.registerCallback('new_joystick', self._newJoystick_callback)
        self.joysticks.registerCallback('joystick_disconnected', self._joystickDisconnected_callback)

        self.deviceManager.registerCallback('new_device', self._newDevice_callback)
        self.deviceManager.registerCallback('device_disconnected', self._deviceDisconnected_callback)
        self.deviceManager.registerCallback('stream', self._deviceStream_callback)

        if self.optitrack is not None:
            self.optitrack.registerCallback('new_frame', self._newOptiTrackFrame_callback)

        self.robots = {}
        self.connected_joysticks = {}
        self.joystick_assignments = {}

        self.callbacks = {
            'new_robot': [],
            'robot_disconnected': [],
            'new_joystick': [],
            'joystick_disconnected': [],
            'new_joystick_assignment': [],
            'joystick_assignment_removed': [],
            'stream': []
        }

        self._thread = threading.Thread(target=self._threadFunction)

    # === METHODS ======================================================================================================
    def registerCallback(self, callback_id, callback):
        if callback_id in self.callbacks.keys():
            self.callbacks[callback_id].append(callback)
        else:
            raise Exception(f"No callback with id {callback_id} is known.")

    # ------------------------------------------------------------------------------------------------------------------
    def init(self):
        self.deviceManager.init()
        self.joysticks.init()

        if self.optitrack is not None:
            self.optitrack.init()

    # ------------------------------------------------------------------------------------------------------------------
    def start(self):
        self.deviceManager.start()
        self.joysticks.start()

        if self.optitrack is not None:
            self.optitrack.start()
        self._thread.start()

    # ------------------------------------------------------------------------------------------------------------------
    def assignJoystick(self, robot, joystick):

        print("ASSIGN")
        if isinstance(robot, str):
            if robot in self.robots.keys():
                robot = self.robots[robot]
            else:
                return

        if isinstance(joystick, str):
            if joystick in self.joysticks.joysticks.keys():
                joystick = self.joysticks.joysticks[joystick]
            else:
                return

        self.joystick_assignments[joystick.uuid] = {
            'robot': robot,
            'joystick': joystick
        }
        joystick.setButtonCallback(button=1, event='down', function=robot.setControlMode, parameters={'mode': 2})
        joystick.setButtonCallback(button=0, event='down', function=robot.setControlMode, parameters={'mode': 0})

        for callback in self.callbacks['new_joystick_assignment']:
            callback(robot, joystick)
        # TODO add button callbacks and update function for axes. Maybe add a function of the Joystick to the robot
        #  class? Or just handle it in the update function here? Probably the best to just do it here

    # ------------------------------------------------------------------------------------------------------------------
    def unassignJoystick(self, joystick):
        if isinstance(joystick, str) and joystick in self.joysticks.joysticks.keys():
            joystick = self.joysticks.joysticks[joystick]
        else:
            return

        self.joystick_assignments.pop(joystick.uuid)

        joystick.clearAllButtonCallbacks()

        for callback in self.callbacks['joystick_assignment_removed']:
            callback(joystick)
        # TODO remove button callbacks and update function for axes

    # ------------------------------------------------------------------------------------------------------------------
    def emergencyStop(self):
        for robot in self.robots.values():
            robot.setControlMode(0)

    # ------------------------------------------------------------------------------------------------------------------
    def setRobotControlMode(self, robot, mode):
        if isinstance(robot, str):
            if robot in self.robots.keys():
                robot = self.robots[robot]
            else:
                return

        robot.setControlMode(mode)

    # === PRIVATE METHODS ==============================================================================================
    def _threadFunction(self):
        while True:
            # Write the input to all the robots
            for assignment in self.joystick_assignments.values():
                val1 = assignment['joystick'].axis[1] * max_forward_torque_cmd
                val2 = assignment['joystick'].axis[2] * max_turning_torque_cmd
                assignment['robot'].setInput([val1 + val2, val1 - val2])

            time.sleep(0.1)

    # ------------------------------------------------------------------------------------------------------------------
    def _newJoystick_callback(self, joystick, *args, **kwargs):
        # Check if the joystick is in the list of known joysticks
        if joystick.uuid not in settings.joysticks:
            print(joystick.uuid)
            return
        logger.info(f"New Joystick connected (ID: {settings.joysticks[joystick.uuid]['id']}, UUID: {joystick.uuid})")

        if settings.joysticks[joystick.uuid]['master']:
            logger.info("Master Joystick connected!")

        self.connected_joysticks[joystick.uuid] = joystick

        for callback in self.callbacks['new_joystick']:
            callback(joystick, *args, **kwargs)

        ...

    # ------------------------------------------------------------------------------------------------------------------
    def _joystickDisconnected_callback(self, joystick, *args, **kwargs):
        if joystick.uuid not in self.connected_joysticks.keys():
            return

        # Remove the Joystick from our internal list
        self.connected_joysticks.pop(joystick.uuid)
        logger.info(f"Joystick disconnected (ID: {settings.joysticks[joystick.uuid]['id']}, UUID: {joystick.uuid})")

        if settings.joysticks[joystick.uuid]['master']:
            logger.info("Master Joystick disconnected!")

        # Check if there have been any assignments, if so, delete them
        if joystick.uuid in self.joystick_assignments:
            logging.info(
                f"Removed Joystick assignment ({settings.joysticks[joystick.uuid]['id']} -> {self.joystick_assignments[joystick.uuid]['robot'].device.information.device_id})")
            self.unassignJoystick(joystick.uuid)

        # TODO: Notify the GUI. Should not be done here but on an overlaying task. But we need a callback here

    # ------------------------------------------------------------------------------------------------------------------
    def _newDevice_callback(self, device: Device, *args, **kwargs):

        # Check if the device has the correct class and type
        if not (device.information.device_class == 'robot' and device.information.device_type == 'twipr'):
            return

        robot = TWIPR(device)

        # Check if the robot is in the list of known robot IDs, so that we can later assign the correct properties
        if robot.device.information.device_id not in settings.agents.keys():
            logging.warning(
                f"New Robot ({robot.device.information.device_class}/{robot.device.information.device_type}) connected, but with "
                f"unknown id {robot.device.information.device_id}")
            return

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

        self.robots.pop(device.information.device_id)

        for joystick_id, assignment in self.joystick_assignments.items():
            if self.robots[device.information.device_id] == assignment['robot']:
                self.unassignJoystick(joystick_id)

        logger.info(f"Robot {device.information.device_id} disconnected")

        # Remove any joystick assignments

    # ------------------------------------------------------------------------------------------------------------------
    def _newOptiTrackFrame_callback(self, rigidBodyId, position, orientation, *args, **kwargs):

        # Check if this OptiTrack RigidBodyID is in use
        for agent_id in self.robots:
            if rigidBodyId == settings.agents[agent_id]['optitrack_id']:
                ...

    def _deviceStream_callback(self, stream, device, *args, **kwargs):
        ...
        if device.information.device_id in self.robots.keys():
            robot = self.robots[device.information.device_id]
            new_sample = robot.convertSample(stream)

            for callback in self.callbacks['stream']:
                callback(new_sample, device, *args, **kwargs)
