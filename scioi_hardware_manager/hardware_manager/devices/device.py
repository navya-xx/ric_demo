import dataclasses
import logging

from hardware_manager.communication.connection import Connection
from hardware_manager.communication.protocols.protocol import Protocol, Message
from hardware_manager.communication.protocols.tcp.tcp_json_protocol import TCP_JSON_Message, TCP_JSON_Protocol

logger = logging.getLogger('device')
logger.setLevel('INFO')


@dataclasses.dataclass
class DataValue:
    identifier: str
    description: str
    datatype: (tuple, type)
    limits: list
    writable: bool
    value: object


@dataclasses.dataclass
class DeviceInformation:
    device_class: str = ''
    device_type: str = ''
    name: str = ''
    device_id: str = ''
    address: str = ''
    revision: int = 0


class Device:
    information: DeviceInformation

    data: dict
    commands: dict

    connection: Connection

    # === INIT =========================================================================================================
    def __init__(self, connection: Connection = None):
        self.connection = connection

        self.information = DeviceInformation()

        self.data = {}
        self.commands = {}

        self.callbacks = {
            'registered': [],
            'disconnected': [],
            'rx': [],
            'stream': []
        }

    # === PROPERTIES ===================================================================================================
    @property
    def address(self):
        if self.connection is not None:
            return self.connection.address
        else:
            return None

    # ------------------------------------------------------------------------------------------------------------------
    @property
    def connection(self):
        return self._connection

    @connection.setter
    def connection(self, connection):
        self._connection = connection
        if self._connection is not None:
            self.connection.registerCallback('rx', self._rx_callback)
            self.connection.registerCallback('disconnected', self._disconnected_callback)

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

        self.send(msg)

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
        assert (message._protocol in self.connection.protocols)

        # Send the message via the connection
        self.connection.send(message)

    # ------------------------------------------------------------------------------------------------------------------
    def registerCallback(self, callback_id, callback):
        if callback_id in self.callbacks.keys():
            self.callbacks[callback_id].append(callback)
        else:
            raise Exception(f"Device: No callback with id {callback_id} is known.")

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
        self.information.device_class = data['device_class']
        self.information.device_type = data['device_type']
        self.information.device_name = data['device_name']
        self.information.device_id = data['device_id']
        self.information.address = data['address']
        self.information.remote_address = data['revision']

        # Set the data
        for name, item in data['data'].items():
            if isinstance(item, dict) and all(isinstance(sub_item, dict) for sub_item in item.values()):
                self.data[name] = {}
                for sub_item_name, sub_item in item.items():
                    self.data[name][sub_item_name] = DataValue(identifier=sub_item['identifier'],
                                                               description=sub_item['description'],
                                                               limits=sub_item['limits'],
                                                               writable=sub_item['writable'],
                                                               datatype=sub_item['datatype'],
                                                               value=sub_item['value'])
            else:
                self.data[name] = DataValue(identifier=item['identifier'],
                                            description=item['description'],
                                            limits=item['limits'],
                                            writable=item['writable'],
                                            datatype=item['datatype'],
                                            value=item['value'])

        # Set the commands
        ...

        self.connection.registered = True

        for callback in self.callbacks['registered']:
            callback(self)

    # ------------------------------------------------------------------------------------------------------------------
    def _disconnected_callback(self, connection: Connection):
        logger.info(f'Device disconnected. Name: {self.name} ({self.device_class}/{self.device_type})')
        for callback in self.callbacks['disconnected']:
            callback(self)
    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
