import dataclasses
import enum
import logging
import time

import boards
import hardware_manager.devices.boards.utils as board_utils
from hardware_manager.communication.core.tcp import TCP_CommunicationDevice
from hardware_manager.communication.protocols.tcp.tcp_json_protocol import TCP_JSON_Protocol, TCP_JSON_Message
from hardware_manager.communication.protocols.tcp.tcp_base_protocol import TCP_Base_Message
import hardware_manager.utils.utils as utils


@dataclasses.dataclass
class RobotControlCommunication(boards.BoardCommunication):

    def __init__(self):
        self.dev = {
            'tcp': TCP_CommunicationDevice(),
            'udp': None,
            'usb': None
        }


# ======================================================================================================================
class RobotControl_IMU:
    gyr: list
    acc: list
    orientation: list
    state: str
    timestamp: float


# ======================================================================================================================
@dataclasses.dataclass
class RobotControl_BoardSensors:
    temp1: float = -1
    temp2: float = -1
    battery: float = -1
    usb: float = -1
    timestamp: float = -1


# ======================================================================================================================
class RobotControlSensors:
    imu: RobotControl_IMU
    board: RobotControl_BoardSensors

    def __init__(self):
        self.imu = RobotControl_IMU()
        self.board = RobotControl_BoardSensors()


# ======================================================================================================================
class RobotControl_DiscreteLED(board_utils.led.DiscreteLED):
    identifier: str

    def __init__(self, identifier: str):
        super().__init__()
        self.identifier = identifier


# ======================================================================================================================
class RobotControl_RGB_LED(board_utils.led.RGB_LED):
    ...


# ======================================================================================================================
class RobotControl_RGB_Strand(board_utils.led.RGB_LED_Strand):
    ...


# ======================================================================================================================
class RobotControl_LEDs:
    led1: RobotControl_DiscreteLED
    led2: RobotControl_DiscreteLED
    rgb_status: RobotControl_RGB_LED
    rgb_strand: RobotControl_RGB_Strand

    def __init__(self):
        self.led1 = RobotControl_DiscreteLED('led1')
        self.led2 = RobotControl_DiscreteLED('led2')
        self.rgb_status = RobotControl_RGB_LED()
        self.rgb_strand = RobotControl_RGB_Strand(16)


# ======================================================================================================================
class RobotControlStatus:
    ...


# ======================================================================================================================
class RobotControlHardwareRevision(enum.Enum):
    REV1 = 1,
    REV2 = 2,
    REV2_1 = 3,
    REV3 = 4,
    REV4 = 5


# ======================================================================================================================
@dataclasses.dataclass
class RobotControlHardware(boards.BoardHardware):
    rev: RobotControlHardwareRevision = None


# ======================================================================================================================
@dataclasses.dataclass
class RobotControlSoftware(boards.BoardSoftware):
    rev_h7: str = None
    firmware_h7: str = None
    hash_h7: str = None

    rev_cm4: str = None
    firmware_cm4: str = None
    hash_cm4: str = None

    rev_board: str = None
    firmware_board: str = None
    hash_board: str = None

    firmware: str = None
    rev: str = None


# ======================================================================================================================
class RobotControl(boards.Board):
    com: RobotControlCommunication
    sensors: RobotControlSensors
    hardware: RobotControlHardware
    software: RobotControlSoftware
    leds: RobotControl_LEDs
    data: dict

    callbacks: dict[str, list[utils.Callback]]
    message_callbacks: list[board_utils.tcp.TCPMessageCallback]

    # === INIT =========================================================================================================
    def __init__(self):
        super().__init__()

        self.com = RobotControlCommunication()
        self.sensors = RobotControlSensors()
        self.hardware = RobotControlHardware()
        self.software = RobotControlSoftware()

        self.message_callbacks = []

        self.callbacks = {
            'rx': [],
            'tx': [],
            'error': []
        }

    # === PROPERTIES ===================================================================================================
    # === METHODS ======================================================================================================
    def addMessageCallback(self, message_filter, function, parameters: dict = None, lambdas: dict = None):
        callback = utils.Callback(function, parameters, lambdas)
        message_callback = board_utils.tcp.TCPMessageCallback(callback, message_filter)
        self.message_callbacks.append(message_callback)

    # ------------------------------------------------------------------------------------------------------------------
    def sendTCPMessage(self, msg):
        if isinstance(msg, TCP_JSON_Message):
            self._sendTCPMessage(msg)
        elif isinstance(msg, dict):
            json_msg = TCP_JSON_Message()
            json_msg.data = msg
            self._sendTCPMessage(json_msg)

    # ------------------------------------------------------------------------------------------------------------------
    def setParameter(self, parameter: str, value):
        data = {
            parameter: value
        }

    # ------------------------------------------------------------------------------------------------------------------
    def readParameter(self, parameter: str):
        ...

    # ------------------------------------------------------------------------------------------------------------------
    def setValue(self, name, value):
        data = {
            name: value
        }

    # ------------------------------------------------------------------------------------------------------------------
    def readValue(self, name: str):
        ...

    # ------------------------------------------------------------------------------------------------------------------
    def setStreamingConfig(self, config: dict):
        ...

    # ------------------------------------------------------------------------------------------------------------------
    def setPinConfig(self, config: dict):
        ...

    # ------------------------------------------------------------------------------------------------------------------
    def setPin(self, pin_name: str, value: int):
        ...

    # ------------------------------------------------------------------------------------------------------------------
    def setPWM(self, pin_name: str, value: float):
        ...

    # ------------------------------------------------------------------------------------------------------------------
    def reboot(self):
        """
        - reboots the CM4
        :return:
        """
        ...

    # ------------------------------------------------------------------------------------------------------------------
    def shutdown(self):
        """
        - shuts down the CM4 and disables the MCU
        :return:
        """
        ...

    # ------------------------------------------------------------------------------------------------------------------
    def stop(self):
        """
        - shuts down the MCU and resets all outputs
        :return:
        """
        ...

    # ------------------------------------------------------------------------------------------------------------------
    def updateMCUFirmware(self):
        ...

    # ------------------------------------------------------------------------------------------------------------------
    def run(self, statement: str):
        """
        - run a statement on the CM4
        :param statement:
        :return:
        """
        pass

    # ------------------------------------------------------------------------------------------------------------------
    def restartFirmware(self):
        """
        - restarts the firmware on the CM4
        :return:
        """
        pass

    # ------------------------------------------------------------------------------------------------------------------
    def resetMCU(self):
        """
        - resets the program on the MCU
        :return:
        """
        pass

    # --- MORE SPECIAL METHODS -----------------------------------------------------------------------------------------
    def setLED(self, led: str, value: int):
        """
        - set one of the on-board LEDs to a certain value or toggle the LED
        :param value: int -> 0 (off), 1 (on), -1 (toggle)
        :param led: str -> 'led1' or 'led2'
        :return:
        """
        ...

    def setStatusLED(self, color: list):
        """
        :param color: [RED, GREEN, BLUE]
        """
        ...

    def setRGB(self, number: int, color: list):
        """

        :param number: can be either an integer for one LED, a list of integers, or a -1 for all LEDs
        :param color: [R,G,B] for a single LED or all LEDs and a list of lists for multiple LEDs [[R1,G1,B1],[R2,G2,B2]]
        """
        ...

    # === PRIVATE METHODS ==============================================================================================
    def _sendTCPMessage(self, message: TCP_JSON_Message):
        # Check if the tcp device is connected and working
        if not (self.com.dev['tcp'].connected and self.com.dev['tcp'].registered):
            logging.error(f"Cannot send message to {self.name}")
            return

        # Create a TCP Base Message to send to the device
        tcp_msg = TCP_Base_Message()
        tcp_msg.src = [0, 0]
        tcp_msg.add = [0, 0]
        tcp_msg.data_protocol_id = TCP_JSON_Protocol.identifier
        tcp_msg.data = message.encode()
        self.com.dev['tcp'].send(tcp_msg)

    # ------------------------------------------------------------------------------------------------------------------
    def _sendTCPRaw(self, data):
        # Check if the tcp device is connected and working
        if not (self.com.dev['tcp'].connected and self.com.dev['tcp'].registered):
            logging.error(f"Cannot send message to {self.name}")
            return

        self.com.dev['tcp'].sendRaw(data)

    # ------------------------------------------------------------------------------------------------------------------
    def _sendUSBMessage(self):
        logging.error(f"USB Messages or not implemented yet.")

    # ------------------------------------------------------------------------------------------------------------------
    def _rxMessageHandler(self, message: TCP_JSON_Message):
        assert (isinstance(message, TCP_JSON_Message) and hasattr(message.data, 'data'))

        # check for certain tags inside the message and evoke the individual message handlers
        if hasattr(message.data, 'sensors'):
            if hasattr(message.data['sensors'], 'imu'):
                self._rxMessageHandler(message.data['sensors']['imu'])

            if hasattr(message.data['sensors'], 'board'):
                self._rxMessageHandler_BoardSensors(message.data['sensors']['board'])

        if hasattr(message.data, 'hardware'):
            self._rxMessageHandler_HardwareConfig(message.data['hardware'])

        if hasattr(message.data, 'software'):
            self._rxMessageHandler_SoftwareConfig(message.data['software'])

        if hasattr(message.data, 'data'):
            self._rxMessageHandler_Data(message.data['data'])

    # ------------------------------------------------------------------------------------------------------------------

    # TODO: I probably need also some callbacks for certain messages. Also the general handling should be more modular

    # TODO: Make a general message that just writes stuff into a "data" dict

    # --- INDIVIDUAL MESSAGE HANDLERS ----------------------------------------------------------------------------------
    def _rxMessageHandler_IMU(self, imu_data):
        # TODO: I need a data extraction method that does not yields an error if the field is not there, but rather a
        #  soft error
        self.sensors.imu.gyr = utils.getFromDict(imu_data, 'gyr')
        self.sensors.imu.acc = utils.getFromDict(imu_data, 'acc')
        self.sensors.imu.orientation = utils.getFromDict(imu_data, 'orientation')
        self.sensors.imu.state = utils.getFromDict(imu_data, 'state')
        self.sensors.imu.timestamp = time.time()

    # ------------------------------------------------------------------------------------------------------------------
    def _rxMessageHandler_BoardSensors(self, board_sensors):
        self.sensors.board.temp1 = board_sensors['temp1']
        self.sensors.board.temp2 = board_sensors['temp2']
        self.sensors.board.battery = board_sensors['battery']
        self.sensors.board.usb = board_sensors['usb_voltage']
        self.sensors.board.timestamp = time.time()

    # ------------------------------------------------------------------------------------------------------------------
    def _rxMessageHandler_Data(self, data):
        assert (isinstance(data, dict))

        for key, value in data.items():
            self.data[key] = value

    # ------------------------------------------------------------------------------------------------------------------
    def _rxMessageHandler_HardwareConfig(self, config):
        self.hardware.rev = config['rev']

    # ------------------------------------------------------------------------------------------------------------------
    def _rxMessageHandler_SoftwareConfig(self, config):
        self.software.rev_h7 = config['rev_h7']
        self.software.rev_cm4 = config['rev_cm4']
        self.software.rev_board = config['rev_board']
        self.software.hash_h7 = config['hash_h7']
        self.software.hash_board = config['hash_board']
        self.software.hash_cm4 = config['hash_cm4']
        self.software.firmware_board = config['firmware_board']
        self.software.firmware_h7 = config['firmware_h7']
        self.software.firmware_cm4 = config['firmware_cm4']
