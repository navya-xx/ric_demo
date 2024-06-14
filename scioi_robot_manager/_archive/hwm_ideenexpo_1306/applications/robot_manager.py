import logging
import threading
import time

from numpy import sign

from device_manager.device_manager import DeviceManager
from device_manager.devices.device import Device
from device_manager.devices.robots.twipr.twipr import TWIPR
from extensions.joystick.joystick_manager import JoystickManager, Joystick
from extensions.optitrack.optitrack import OptiTrack
import applications.ideenexpo.settings as settings

logger = logging.getLogger('robot manager')
logger.setLevel('INFO')

# TODO: should be somewhere else

max_forward_torque_cmd = 0.01
max_turning_torque_cmd = 0.03
state = 1

MAX_TORQUE_FORWARD = 0.1

MAX_TORQUE_TURN = 0.15


def increaseForwardTorqueValues(forward, *args, **kwargs):
    global max_turning_torque_cmd, max_forward_torque_cmd
    max_forward_torque_cmd = max_forward_torque_cmd + forward

    if max_forward_torque_cmd > MAX_TORQUE_FORWARD:
        max_forward_torque_cmd = MAX_TORQUE_FORWARD

    print(f"Set Torque values to Turning: {max_turning_torque_cmd}, Forwards: {max_forward_torque_cmd}")


def lowerForwardTorqueValues(forward, *args, **kwargs):
    global max_turning_torque_cmd, max_forward_torque_cmd
    max_forward_torque_cmd = max_forward_torque_cmd - forward

    if max_forward_torque_cmd < 0.01:
        max_forward_torque_cmd = 0.01

    print(f"Set Torque values to Turning: {max_turning_torque_cmd}, Forwards: {max_forward_torque_cmd}")


def increaseTurningTorqueValues(turning, *args, **kwargs):
    global max_turning_torque_cmd
    max_turning_torque_cmd = max_turning_torque_cmd + turning

    if max_turning_torque_cmd > MAX_TORQUE_TURN:
        max_turning_torque_cmd = MAX_TORQUE_TURN
    print(f"Set Torque values to Turning: {max_turning_torque_cmd}, Forwards: {max_forward_torque_cmd}")


def lowerTurningTorqueValues(turning, *args, **kwargs):
    global max_turning_torque_cmd
    max_turning_torque_cmd = max_turning_torque_cmd - turning

    if max_turning_torque_cmd < 0.03:
        max_turning_torque_cmd = 0.03
    print(f"Set Torque values to Turning: {max_turning_torque_cmd}, Forwards: {max_forward_torque_cmd}")


def resetTorqueValues():
    global max_turning_torque_cmd, max_forward_torque_cmd
    max_forward_torque_cmd = 0.02
    max_turning_torque_cmd = 0.04

    print(f"Set Torque values to Turning: {max_turning_torque_cmd}, Forwards: {max_forward_torque_cmd}")


class RobotManager:
    deviceManager: DeviceManager
    joysticks: JoystickManager
    optitrack: OptiTrack

    callbacks: dict

    robots: dict[str, TWIPR]

    joystick_assignments: dict
    connected_joysticks: dict

    masterJoystick: Joystick

    _thread: threading.Thread

    _masterJoystickActive: bool

    def __init__(self, optitrack: bool = False):

        self.deviceManager = DeviceManager()
        self.joysticks = JoystickManager()
        self.masterJoystick = None
        self._masterJoystickActive = False

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

        resetTorqueValues()

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

        for key, assignment in self.joystick_assignments.items():
            if robot == assignment['robot']:
                self.unassignJoystick(assignment['joystick'])

        self.joystick_assignments[joystick.uuid] = {
            'robot': robot,
            'joystick': joystick
        }
        joystick.setButtonCallback(button=1, event='down', function=robot.setControlMode, parameters={'mode': 2})
        joystick.setButtonCallback(button=0, event='down', function=robot.setControlMode, parameters={'mode': 0})
        print("CALLBACKS ASSIGN")
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

        if joystick == self.masterJoystick:
            self._assignMasterCallbacks()

        for callback in self.callbacks['joystick_assignment_removed']:
            callback(joystick)
        # TODO remove button callbacks and update function for axes

    # ------------------------------------------------------------------------------------------------------------------
    def emergencyStop(self):
        print("Emergency Stop")
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
                val1 = 0
                val2 = 0

                master_torque_factor = 0

                if self.masterJoystick is not None:
                    master_torque_factor = (self.masterJoystick.axis[5] + 1) * 0.25

                max_forward_torque_cmd_local = max_forward_torque_cmd + master_torque_factor * (
                        MAX_TORQUE_FORWARD - max_forward_torque_cmd)

                # if self.masterJoystick is not None and (self._masterJoystickActive or (abs(self.masterJoystick.axis[1])>0.05 or abs(self.masterJoystick.axis[2]) > 0.05)):
                #     val1 = self.masterJoystick.axis[1] * max_forward_torque_cmd
                #     val2 = self.masterJoystick.axis[2] * max_turning_torque_cmd
                # else:
                #     val1 = assignment['joystick'].axis[1] * max_forward_torque_cmd
                #     val2 = assignment['joystick'].axis[2] * max_turning_torque_cmd

                if self.masterJoystick is not None and (
                        self._masterJoystickActive or (abs(self.masterJoystick.axis[1]) > 0.05)):
                    val1 = self.masterJoystick.axis[1] * max_forward_torque_cmd_local
                else:
                    val1 = assignment['joystick'].axis[1] * max_forward_torque_cmd_local

                if self.masterJoystick is not None and (
                        self._masterJoystickActive or (abs(self.masterJoystick.axis[2]) > 0.05)):
                    val2 = self.masterJoystick.axis[2] * max_turning_torque_cmd
                else:
                    val2 = assignment['joystick'].axis[2] * max_turning_torque_cmd

                # if self.masterJoystick is not None and self._masterJoystickActive:
                #     val1 = self.masterJoystick.axis[1] * max_forward_torque_cmd
                #     val2 = self.masterJoystick.axis[2] * max_turning_torque_cmd
                # else:
                #     val1 = assignment['joystick'].axis[1] * max_forward_torque_cmd
                #     val2 = assignment['joystick'].axis[2] * max_turning_torque_cmd

                forward_command = val1
                turn_command = val2

                # if abs(forward_command) > 0.01:
                #     forward_command = float(sign(forward_command) * (abs(forward_command) * (1 - master_torque_factor) + master_torque_factor * MAX_TORQUE_FORWARD))

                # print(forward_command)
                assignment['robot'].setInput([forward_command + turn_command, forward_command - turn_command])

            time.sleep(0.1)

    # ------------------------------------------------------------------------------------------------------------------
    def _newJoystick_callback(self, joystick, *args, **kwargs):
        # Check if the joystick is in the list of known joysticks
        if joystick.uuid not in settings.joysticks:
            print(joystick.uuid)
            return
        logger.info(f"New Joystick connected (ID: {settings.joysticks[joystick.uuid]['id']}, UUID: {joystick.uuid})")
        joystick.name = settings.joysticks[joystick.uuid]['id']

        if settings.joysticks[joystick.uuid]['master']:
            logger.info("Master Joystick connected!")
            self.masterJoystick = joystick
            self._assignMasterCallbacks()

            # self.masterJoystick.setButtonCallback(button=2, event='down', function=self._masterTakeOver)
            # self.masterJoystick.setButtonCallback(button=3, event='down', function=resetTorqueValues)
            # self.masterJoystick.setButtonCallback(button=4, event='down', function=self.emergencyStop)

        self.connected_joysticks[joystick.uuid] = joystick

        for callback in self.callbacks['new_joystick']:
            callback(joystick, *args, **kwargs)

    # ------------------------------------------------------------------------------------------------------------------
    def _joystickDisconnected_callback(self, joystick, *args, **kwargs):
        if joystick.uuid not in self.connected_joysticks.keys():
            return

        # Remove the Joystick from our internal list
        self.connected_joysticks.pop(joystick.uuid)
        logger.info(f"Joystick disconnected (ID: {settings.joysticks[joystick.uuid]['id']}, UUID: {joystick.uuid})")

        if settings.joysticks[joystick.uuid]['master']:
            self.masterJoystick = None
            logger.info("Master Joystick disconnected!")

        # Check if there have been any assignments, if so, delete them
        if joystick.uuid in self.joystick_assignments:
            logging.info(
                f"Removed Joystick assignment ({settings.joysticks[joystick.uuid]['id']} -> {self.joystick_assignments[joystick.uuid]['robot'].device.information.device_id})")
            self.unassignJoystick(joystick.uuid)

        # TODO: Notify the GUI. Should not be done here but on an overlaying task. But we need a callback here

        for callback in self.callbacks['joystick_disconnected']:
            callback(joystick)

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
            try:
                if self.robots[device.information.device_id] == assignment['robot']:
                    print("Unassign Joystick because of disconnect")
                    self.unassignJoystick(joystick_id)
            except Exception:
                print("I have to fix this")

        logger.info(f"Robot {device.information.device_id} disconnected")

        # Remove any joystick assignments

    # ------------------------------------------------------------------------------------------------------------------
    def _newOptiTrackFrame_callback(self, rigidBodyId, position, orientation, *args, **kwargs):

        # Check if this OptiTrack RigidBodyID is in use
        for agent_id in self.robots:
            if rigidBodyId == settings.agents[agent_id]['optitrack_id']:
                pass

    def _deviceStream_callback(self, stream, device, *args, **kwargs):
        if device.information.device_id in self.robots.keys():
            robot = self.robots[device.information.device_id]
            new_sample = robot.convertSample(stream)

            for callback in self.callbacks['stream']:
                callback(new_sample, device, *args, **kwargs)

    # ------------------------------------------------------------------------------------------------------------------
    def _assignMasterCallbacks(self):
        if self.masterJoystick is not None:
            self.masterJoystick.clearAllButtonCallbacks()
            self.masterJoystick.setJoyHatCallback(direction='up', function=increaseForwardTorqueValues,
                                                  parameters={'forward': 0.01})
            self.masterJoystick.setJoyHatCallback(direction='down', function=lowerForwardTorqueValues,
                                                  parameters={'forward': 0.01})

            self.masterJoystick.setJoyHatCallback(direction='right', function=increaseTurningTorqueValues,
                                                  parameters={'turning': 0.01})
            self.masterJoystick.setJoyHatCallback(direction='left', function=lowerTurningTorqueValues,
                                                  parameters={'turning': 0.01})

            self.masterJoystick.setButtonCallback(button=1, event='down', function=self._masterSetControlMode,
                                                  parameters={'mode': 2})
            self.masterJoystick.setButtonCallback(button=0, event='down', function=self._masterSetControlMode,
                                                  parameters={'mode': 0})
            self.masterJoystick.setButtonCallback(button=2, event='down', function=self._masterJoystickToggle)
            self.masterJoystick.setButtonCallback(button=3, event='down', function=resetTorqueValues)
            self.masterJoystick.setButtonCallback(button=4, event='down', function=self.emergencyStop)

    # ------------------------------------------------------------------------------------------------------------------
    def _masterSetControlMode(self, mode):
        for robot in self.robots.values():
            robot.setControlMode(mode)

    def _masterJoystickToggle(self):
        print("Master Joystick Toggle")
        self._masterJoystickActive = not self._masterJoystickActive

        if self._masterJoystickActive:
            self.masterJoystick.rumble(1, 750)
        else:
            self.masterJoystick.rumble(0.25, 250)

    # ------------------------------------------------------------------------------------------------------------------
    def _masterTakeOver(self):
        # if self.masterJoystick is None:
        #     return
        #
        # if len(self.robots) > 1:
        #     self.emergencyStop()
        #     return
        #
        # robot = None
        # for key, assignment in self.joystick_assignments.items():
        #     robot = assignment['robot']
        #     self.unassignJoystick(key)
        #     break
        #
        # if robot is not None:
        #     self.assignJoystick(robot=robot, joystick=self.masterJoystick)

        print("Master Takeover")
