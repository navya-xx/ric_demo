import ctypes
import enum
import threading

from cm4_core_old.communication.serial.protocols.uart_protocol import UART_Message
from cm4_core_old.communication.serial.serial_connection import SerialConnection
from cm4_core_old import utils
import control_board.settings as board_parameters


class UART_CMD(enum.IntEnum):
    UART_CMD_WRITE = 0x01
    UART_CMD_READ = 0x02
    UART_CMD_ANSWER = 0x03
    UART_CMD_STREAM = 0x04
    UART_CMD_EVENT = 0x05
    UART_CMD_MSG = 0x06
    UART_CMD_FCT = 0x07
    UART_CMD_ECHO = 0x08


FLOAT = ctypes.c_float
DOUBLE = ctypes.c_double
UINT8 = ctypes.c_uint8
UINT16 = ctypes.c_uint16
INT8 = ctypes.c_int8
INT16 = ctypes.c_int16
UINT32 = ctypes.c_uint32
INT32 = ctypes.c_int32


class ReadRequest:
    event: threading.Event
    module: int = 0
    address: bytes = b'\x00\x00'
    msg: UART_Message = None
    timeout: bool = True
    flag: int = 0

    def __init__(self):
        self.event = threading.Event()


class Serial_Interface:
    device: SerialConnection
    callbacks: dict
    _thread: threading.Thread
    _exit: bool = False
    _readRequest = list[ReadRequest]

    def __init__(self, port: str, baudrate: int = 115200):
        self.device = SerialConnection(device=port, baudrate=baudrate)

        self.device.registerCallback('rx', self._uart_rx_callback)

        self.callbacks = {
            'rx': [],
            'error': []
        }

        self._readRequests = []

    # ------------------------------------------------------------------------------------------------------------------
    def init(self):
        ...

    # ------------------------------------------------------------------------------------------------------------------
    def start(self):
        self.device.start()
        self._thread = threading.Thread(target=self._thread_function, daemon=True)
        self._thread.start()

    # ------------------------------------------------------------------------------------------------------------------
    def stop(self):
        self.device.close()

    # ------------------------------------------------------------------------------------------------------------------
    def write(self, module: int = 0, address: (int, list) = None, value=None, type=ctypes.c_uint8):
        if not isinstance(value, type):
            value = type(value)
        data_bytes = bytes(value)

        self._send(cmd=UART_CMD.UART_CMD_WRITE, module=module, address=address, flag=0, data=data_bytes)

    # ------------------------------------------------------------------------------------------------------------------
    def echo(self, module: int = 0, address: (int, list) = None, value=None, type=ctypes.c_uint8, flag: int = 0):
        if not isinstance(value, type):
            value = type(value)
        data_bytes = bytes(value)

        self._send(cmd=UART_CMD.UART_CMD_ECHO, module=module, address=address, flag=flag, data=data_bytes)

    # ------------------------------------------------------------------------------------------------------------------

    def read(self, address, module: int = 0, type=ctypes.c_uint8):

        # Send the message for reading
        self._send(cmd=UART_CMD.UART_CMD_READ, module=module, address=address, flag=0, data=[])
        request = self._registerRead(module=module, address=address)

        event_success = request.event.wait(timeout=1)

        if event_success and request.msg.flag == 1:

            # Check if the data length matches the data type
            if not ctypes.sizeof(type) == len(request.msg.data):
                return None
            else:
                return type.from_buffer_copy(request.msg.data)
        else:
            return None

    # ------------------------------------------------------------------------------------------------------------------

    def function(self, address, module: int = 0, data=None, input_type=None, output_type=None, timeout=1):

        if isinstance(data, list) and input_type is not None:

            data_bytes = bytearray()
            for entry in data:
                data_bytes += bytes(input_type(entry))

            data = bytes(data_bytes)

        elif input_type is not None and not isinstance(data, input_type):
            data = input_type(data)
            data = bytes(data)

        elif input_type is not None and isinstance(data, input_type):
            data = bytes(data)
        else:
            raise Exception()

        self._send(cmd=UART_CMD.UART_CMD_FCT, module=module, address=address, flag=0, data=data)

        # Register for reading if type is not None
        if output_type is not None:
            req = self._registerRead(module=module, address=address)

            event_success = req.event.wait(timeout=timeout)
            if event_success and req.msg.flag == 1:

                # Check if the data length matches the data type
                if not ctypes.sizeof(output_type) == len(req.msg.data):
                    return None
                else:
                    return output_type.from_buffer_copy(req.msg.data)
            else:
                return None
        else:
            return None

    # ------------------------------------------------------------------------------------------------------------------

    def registerCallback(self, type, callback):
        """

        :param type:
        :param callback:
        :return:
        """
        if type in self.callbacks.keys():
            self.callbacks[type].append(callback)
        else:
            raise Exception("Callback not in list of callbacks")

    # === PRIVATE METHOD ===============================================================================================

    def _thread_function(self):
        while not self._exit:
            # Wait until there is a message in the rx queue of the device
            msg = self.device.rx_queue.get(timeout=None)

            # Handle the rx message and then go back to waiting
            self._handleIncomingMessage(msg)

        # ------------------------------------------------------------------------------------------------------------------

    def _handleIncomingMessage(self, message: UART_Message):

        if message.cmd == UART_CMD.UART_CMD_WRITE:
            # ERROR. Should not happen
            pass
        elif message.cmd == UART_CMD.UART_CMD_READ:
            # ERROR. Should not happen
            pass
        elif message.cmd == UART_CMD.UART_CMD_ANSWER:
            self._handleMessage_answer(message)
        elif message.cmd == UART_CMD.UART_CMD_FCT:
            # ERROR. Should not happen
            pass
        elif message.cmd == UART_CMD.UART_CMD_STREAM:
            pass
        elif message.cmd == UART_CMD.UART_CMD_EVENT:
            pass

        # ------------------------------------------------------------------------------------------------------------------

    def _handleMessage_answer(self, msg):

        # Go through all the read requests and check if anyone waits for this
        for req in self._readRequests:
            if req.module == msg.add[0] and req.address == bytes([msg.add[1], msg.add[2]]):
                req.msg = msg
                req.event.set()

        # ------------------------------------------------------------------------------------------------------------------

    def _registerRead(self, module, address):
        request = ReadRequest()

        if isinstance(address, list):
            address = bytes(address)
        elif isinstance(address, int):
            address = utils.bytes.intToByte(address, 2)

        request.address = address
        request.module = module

        self._readRequests.append(request)
        return request

    # ------------------------------------------------------------------------------------------------------------------
    def _send(self, cmd: int = 0, module: int = 0, address: (bytes, bytearray, list, int) = None, flag: int = 0,
              data=None):

        if isinstance(address, int):
            address = list(utils.bytes.intToByte(address, 2))
        elif isinstance(address, bytes):
            address = list(address)
        elif isinstance(address, bytearray):
            address = list(address)

        msg = UART_Message()
        msg.cmd = cmd
        msg.add = [module] + address
        msg.flag = flag

        if data is None:
            data = []

        msg.data = data
        self._sendMessage(msg)

    # ------------------------------------------------------------------------------------------------------------------
    def _sendMessage(self, msg: UART_Message):
        # Check the Message
        assert (msg.data is not None)
        assert (len(msg.add) == 3)
        assert (msg.cmd in iter(UART_CMD))
        self.device.send(msg)

    # ------------------------------------------------------------------------------------------------------------------
    def _sendRaw(self, buffer):
        self.device.sendRaw(buffer)

    # ------------------------------------------------------------------------------------------------------------------
    def _uart_rx_callback(self, message, **kwargs):
        for callback in self.callbacks['rx']:
            callback(message)
