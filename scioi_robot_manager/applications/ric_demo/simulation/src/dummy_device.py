from core.communication.connection import Connection
from core.communication.protocols.protocol import Message
from core.communication.protocols.tcp.tcp_json_protocol import TCP_JSON_Message
from core.devices.device import Device, DeviceInformation


class DummyConnection(Connection):
    connected = True
    registered = True
    ...

    def send(self, message: Message):
        pass

    def registerCallback(self, callback_id, function, parameters: dict = None, lambdas: dict = None):
        pass


class DummyDevice(Device):

    # === INIT =========================================================================================================
    def __init__(self, id):

        if not id.startswith('v'):
            print(f"Cannot add virtual device with id {id}")
            return

        self.connection = DummyConnection()

        self.information = DeviceInformation()

        self.data = {}
        self.commands = {}

        self.callbacks = {
            'registered': [],
            'disconnected': [],
            'rx': [],
            'stream': [],
            'dummy_send': [],
        }

        self.information.device_class = 'robot'
        self.information.device_type = 'twipr'
        self.information.device_name = id
        self.information.device_id = id
        self.information.address = 'dummy'
        self.information.revision = 'v3'

    # === PROPERTIES ===================================================================================================
    @property
    def address(self):
        return "dummy"
        # if self.connection is not None:
        #     return self.connection.address
        # else:
        #     return None

    # ------------------------------------------------------------------------------------------------------------------
    # @property
    # def connection(self):
    #     return self._connection
    #
    # @connection.setter
    # def connection(self, connection):
    #     self._connection = connection
        # if self._connection is not None:
        #     self.connection.registerCallback('rx', self._rx_callback)
        #     self.connection.registerCallback('disconnected', self._disconnected_callback)

    # === METHODS ======================================================================================================
    def write(self, parameter, value):
        msg = TCP_JSON_Message()
        msg.type = 'write'
        msg.address = ''
        msg.source = ''

        if isinstance(parameter, str):
            params = parameter.split('/')

            if len(params) == 1:
                msg.data = {
                    parameter: value
                }
            elif len(params) == 2:
                msg.data = {
                    params[0]: {
                        params[1]: value
                    }
                }
            else:
                raise Exception("Levels >1 are not allowed for parameters")

        elif isinstance(parameter, dict):
            msg.data = parameter

        self.send(message=msg)

    # ------------------------------------------------------------------------------------------------------------------
    def read(self, parameter):
        msg = TCP_JSON_Message()
        msg.address = ''
        msg.source = ''
        msg.type = 'read'

        msg.data = {
            'parameter': parameter
        }

    # ------------------------------------------------------------------------------------------------------------------
    def command(self, command, data):
        msg = TCP_JSON_Message()
        msg.address = ''
        msg.source = ''
        msg.type = 'command'

        msg.data = {
            command: data
        }

        self.send(msg)

    # ------------------------------------------------------------------------------------------------------------------
    def send(self, message: Message):

        # Check if the message has the correct protocol

        for callback in self.callbacks['dummy_send']:
            callback(message)

        # Send the message via the connection
        # if self.connection.connected:
        #     try:
        #         self.connection.send(message)
        #     except OSError:
        #         logger.warning("Cannot send message")

    # ------------------------------------------------------------------------------------------------------------------
    def registerCallback(self, callback_id, callback):
        if callback_id in self.callbacks.keys():
            self.callbacks[callback_id].append(callback)
        else:
            raise Exception(f"Device: No callback with id {callback_id} is known.")

    # ------------------------------------------------------------------------------------------------------------------
    def dummyReceive(self, msg, *args, **kwargs):
        self._rx_callback(msg, *args, **kwargs)

    # ------------------------------------------------------------------------------------------------------------------
    def dummyStream(self, data):
        msg = TCP_JSON_Message()
        msg.type = 'stream'
        msg.address = ''
        msg.source = ''
        msg.data = data

        self.dummyReceive(msg)

    # === PRIVATE METHODS ==============================================================================================
    def _rx_callback(self, msg, *args, **kwargs):

        # Check if this message has the correct protocol
        ...

        # Handle the message based on the type of message
        if msg.type == 'answer':
            ...
        elif msg.type == 'event':
            self._handleEventMessage(msg)
        elif msg.type == 'stream':
            self._handleStreamMessage(msg)

    # ------------------------------------------------------------------------------------------------------------------
    def _handleEventMessage(self, message: TCP_JSON_Message):

        if message.event == 'device_identification':
            self._handleIdentificationEvent(message.data)

    # ------------------------------------------------------------------------------------------------------------------
    def _handleStreamMessage(self, message: TCP_JSON_Message):
        for callback in self.callbacks['stream']:
            callback(message, self)

    # ------------------------------------------------------------------------------------------------------------------
    def _handleAnswerMessage(self, message):
        ...

    # ------------------------------------------------------------------------------------------------------------------
    def _handleIdentificationEvent(self, data):
        print("IDENTIFICATION EVENT")

        # TODO
        # self.information.device_class = data['device_class']
        # self.information.device_type = data['device_type']
        # self.information.device_name = data['device_name']
        # self.information.device_id = data['device_id']
        # self.information.address = data['address']
        # self.information.revision = data['revision']

        # Set the commands
        self.connection.registered = True

        for callback in self.callbacks['registered']:
            callback(self)

    # ------------------------------------------------------------------------------------------------------------------
    def _disconnected_callback(self, connection: Connection):
        for callback in self.callbacks['disconnected']:
            callback(self)
