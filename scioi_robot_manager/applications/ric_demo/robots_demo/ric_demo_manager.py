import logging
import threading
import time

from applications.ric_demo import settings
from applications.ideenexpo.src.ideenexpo_gui import IdeenExpoGUI
from robots.twipr.twipr_manager import TWIPR_Manager
from extensions.joystick.joystick_manager import Joystick, JoystickManager

logger = logging.getLogger('RIC')
logger.setLevel('INFO')

torque_turn_max_cmd = 0.04  #0.06
torque_forward_max_cmd = 0.04  #0.06


class RIC_Demo_RobotManager:
    robotManager: TWIPR_Manager
    gui: IdeenExpoGUI

    joystick_manager: JoystickManager
    callbacks: dict
    _connected_joysticks: dict
    _manual_torque_limits: dict

    joystick_assignments: dict

    _thread: threading.Thread

    def __init__(self):

        self.robotManager = TWIPR_Manager()
        self.joystick_manager = JoystickManager()

        self.joystick_manager.registerCallback('new_joystick', self._joystickConnected_callback)
        self.joystick_manager.registerCallback('joystick_disconnected', self._joystickDisconnected_callback)

        self.robotManager.registerCallback('stream', self._robotStream_callback)
        self.robotManager.registerCallback('new_robot', self._newRobot_callback)
        self.robotManager.registerCallback('robot_disconnected', self._robotDisconnected_callback)

        self.gui = IdeenExpoGUI()
        self.gui.registerCallback('rx_message', self._guiRxMessage_callback)

        self._manual_torque_limits = {
            'forward': 0.2,
            'turn': 0.2,
        }

        self.callbacks = {
            'new_robot': [],
            'robot_disconnected': [],
            'stream': [],
        }

        self.joystick_assignments = {}
        self._connected_joysticks = {}

        self._thread = threading.Thread(target=self._threadFunction)

    # ------------------------------------------------------------------------------------------------------------------
    def init(self):
        self.robotManager.init()
        self.joystick_manager.init()
        self.gui.init()

    # ------------------------------------------------------------------------------------------------------------------
    def start(self):
        self.gui.start()
        self.joystick_manager.start()
        self.robotManager.start()
        self._thread.start()

    # ------------------------------------------------------------------------------------------------------------------
    def registerCallback(self, callback_id, callback):
        if callback_id in self.callbacks.keys():
            self.callbacks[callback_id].append(callback)
        else:
            raise Exception(f"No callback with id {callback_id} is known.")

    # === PRIVATE METHODS ==============================================================================================
    def _threadFunction(self):

        while True:

            for assignment in self.joystick_assignments.values():
                input = self._calculateInputValues(assignment['joystick'])
                assignment['robot'].setInput(input)
            time.sleep(0.1)

    # ------------------------------------------------------------------------------------------------------------------
    def _assignJoystick(self, robot, joystick):
        if isinstance(robot, str):
            if robot in self.robotManager.robots.keys():
                robot = self.robotManager.robots[robot]
            else:
                return

        if isinstance(joystick, str):
            if joystick in self.joystick_manager.joysticks.keys():
                joystick = self.joystick_manager.joysticks[joystick]
            else:
                return

        for key, assignment in self.joystick_assignments.items():
            if robot == assignment['robot']:
                self._unassignJoystick(assignment['joystick'])

        self.joystick_assignments[joystick.uuid] = {
            'robot': robot,
            'joystick': joystick
        }

        logger.info(
            f"Added Joystick assignment ({joystick.uuid} -> {self.joystick_assignments[joystick.uuid]['robot'].id})")
        self.gui.print(
            f"Added Joystick assignment ({joystick.uuid} -> {self.joystick_assignments[joystick.uuid]['robot'].id})")

        joystick.setButtonCallback(button=1, event='down', function=robot.setControlMode, parameters={'mode': 2})
        joystick.setButtonCallback(button=0, event='down', function=robot.setControlMode, parameters={'mode': 0})
        joystick.setButtonCallback(button=2, event='down', function=self.robotManager.emergencyStop)

    # ------------------------------------------------------------------------------------------------------------------
    def _unassignJoystick(self, joystick):

        if isinstance(joystick, str) and joystick in self.joystick_manager.joysticks.keys():
            joystick = self.joystick_manager.joysticks[joystick]
        else:
            return

        # Check if there is a joystick assignment, if not, return
        if joystick.uuid not in self.joystick_assignments.keys():
            return

        logger.info(
            f"Remove Joystick assignment ({joystick.uuid} -> {self.joystick_assignments[joystick.uuid]['robot'].id})")
        self.gui.print(
            f"Remove Joystick assignment ({joystick.uuid} -> {self.joystick_assignments[joystick.uuid]['robot'].id})")
        self.joystick_assignments.pop(joystick.uuid)

        joystick.clearAllButtonCallbacks()

    # ------------------------------------------------------------------------------------------------------------------
    def _joystickConnected_callback(self, joystick: Joystick, *args, **kwargs):

        # Check if the joystick is in the list of known joysticks:
        if joystick.uuid not in settings.joysticks:
            logger.info(f"Joystick ({joystick.uuid}) connected, but not in list of known joysticks")
            return

        # Check if the joystick uuid is already given to another connected joystick
        if joystick.uuid in self._connected_joysticks.keys():
            logger.info(f"Joystick ({joystick.uuid}) connected, but it is already in list of connected joysticks")
            return

        self._connected_joysticks[joystick.uuid] = joystick

        # Add the joystick to the gui
        self.gui.addJoystick(joystick)

    # ------------------------------------------------------------------------------------------------------------------
    def _joystickDisconnected_callback(self, joystick, *args, **kwargs):
        if joystick.uuid not in self._connected_joysticks.keys():
            return

        # Remove the joystick from the list of connected joysticks
        self._connected_joysticks.pop(joystick.uuid)
        logger.info(f"Joystick disconnected. UUID: {joystick.uuid})")
        self.gui.print(f"Joystick disconnected. UUID: {joystick.uuid})")

        if joystick.uuid in self.joystick_assignments.keys():
            self._unassignJoystick(joystick)

        # Notify the GUI
        self.gui.removeJoystick(joystick)

    # ------------------------------------------------------------------------------------------------------------------
    def _setControlModeAll(self, mode):
        for robot in self.robotManager.robots.values():
            robot.setControlMode(mode)


    # ------------------------------------------------------------------------------------------------------------------
    def _robotStream_callback(self, stream, robot, *args, **kwargs):
        sample = self.gui.convertTwiprSample(stream)
        self.gui.sendStream(sample)

        for callback in self.callbacks['stream']:
            callback(stream, robot)

    # ------------------------------------------------------------------------------------------------------------------
    def _newRobot_callback(self, robot, *args, **kwargs):
        self.gui.addRobot(robot)
        self.gui.print(f"Robot connected: {robot.id}")

        for callback in self.callbacks['new_robot']:
            callback(robot, *args, **kwargs)

    # ------------------------------------------------------------------------------------------------------------------
    def _robotDisconnected_callback(self, robot, *args, **kwargs):

        self.gui.removeRobot(robot)
        self.gui.print(f"Robot disconnected: {robot.id}")

        # Check if there were any joystick assignments
        for joystick_id, assignment in self.joystick_assignments.items():
            if assignment['robot'] == robot:
                self._unassignJoystick(joystick_id)

        for callback in self.callbacks['robot_disconnected']:
            callback(robot, *args, **kwargs)

    # ------------------------------------------------------------------------------------------------------------------
    def _guiRxMessage_callback(self, message):
        message_type = message.get('type')

        if message_type == 'command':

            if message['data']['command'] == 'emergency':
                self.robotManager.emergencyStop()

        elif message_type == 'joysticksChanged':

            joysticks = message['data']['joysticks']

            for joystick in joysticks:
                joystick_id = joystick['id']
                robot_id = joystick['assignedBot']

                # No Robot assigned to Joystick
                if robot_id == '':
                    # Check if it is currently assigned to a robot
                    if joystick_id in self.joystick_assignments.keys():
                        self._unassignJoystick(joystick_id)
                else:

                    # Check if it is assigned to another robot in the list of ric_robots
                    if joystick_id in self.joystick_assignments.keys():
                        connected_robot_id = self.joystick_assignments[joystick_id][
                            'robot'].device.information.device_id

                        if connected_robot_id == robot_id:
                            # Do nothing, we have already assigned this robot
                            pass
                        else:
                            self._assignJoystick(robot=robot_id, joystick=joystick_id)

                    # it is not connected to a robot yet:
                    else:
                        self._assignJoystick(robot=robot_id, joystick=joystick_id)

        elif message_type == 'set':
            robot_id = message['botId']
            data_key = message['data']['key']
            data_value = message['data']['value']
            timestamp = message['timestamp']

            self.robotManager.setRobotControlMode(robot_id, data_value)

        else:
            # Unknown Message
            pass

    # ------------------------------------------------------------------------------------------------------------------

    def _calculateInputValues(self, joystick) -> list:
        forward = joystick.axis[1] * torque_forward_max_cmd
        turn = joystick.axis[2] * torque_turn_max_cmd
        return [forward + turn, forward - turn]
        # forward = 0
        # turn = 0
        # master_boost = 0
        #
        # if self._masterJoystick is not None:
        #     master_boost = (self._masterJoystick.axis[5] + 1) * 0.25
        #
        # torque_forward_max_cmd = self._manual_torque_limits['forward'] + master_boost * (
        #         ideenexpo_settings.manual_control_settings['forward']['max'] - self._manual_torque_limits['forward'])
        #
        # if self._masterJoystick is not None and (
        #         self._masterJoystickActive or (abs(self._masterJoystick.axis[1]) > 0.05)):
        #     forward = self._masterJoystick.axis[1] * torque_forward_max_cmd
        # else:
        #     forward = joystick.axis[1] * torque_forward_max_cmd
        #
        # if self._masterJoystick is not None and (
        #         self._masterJoystickActive or (abs(self._masterJoystick.axis[2]) > 0.05)):
        #     turn = self._masterJoystick.axis[2] * self._manual_torque_limits['turn']
        # else:
        #     turn = joystick.axis[2] * self._manual_torque_limits['turn']
        # return [forward + turn, forward - turn]
