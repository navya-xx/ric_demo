import threading
import queue
import time
import logging

from hardware_manager.communication import addresses
from hardware_manager.communication.connection import Connection
from hardware_manager.communication.protocols.tcp.tcp_base_protocol import TCP_Base_Protocol, TCP_Base_Message
from hardware_manager.communication.protocols.tcp.tcp_handshake_protocol import TCP_Handshake_Protocol, \
    TCP_Handshake_Message
from hardware_manager.communication.protocols.tcp.tcp_json_protocol import TCP_JSON_Protocol
from hardware_manager.communication.protocols.protocol import Message
import hardware_manager.utils.utils as utils
from hardware_manager.communication.core.tcp import TCP_Client

logger = logging.getLogger('tcp_c')
logger.setLevel('INFO')


########################################################################################################################
class TCP_Connection(Connection):
    rx_queue: queue.Queue
    client: TCP_Client
    config: dict

    protocols = {'base': TCP_Base_Protocol, 'handshake': TCP_Handshake_Protocol}

    _callbacks: dict[str, list]
    _events: dict[str, threading.Event]
    _thread: threading.Thread

    # === INIT =========================================================================================================
    def __init__(self, client: TCP_Client = None, config: dict = None):
        super().__init__()

        # Config for the TCP Device
        default_config = {
            'rx_queue': False,
        }
        if config is None:
            config = {}

        self.config = {**default_config, **config}

        self.client = client
        self.rx_queue = queue.Queue()

        self.callbacks = {
            'disconnected': [],
            'handshake': [],
            'rx': []
        }

        self.events = {
            'handshake': threading.Event(),
            'rx': threading.Event()
        }

    # === PROPERTIES ===================================================================================================
    @property
    def client(self):
        return self._client

    @client.setter
    def client(self, client: TCP_Client):
        self._client = client
        if client is not None:
            self.connected = True
            self.client.registerCallback('rx', self._clientRx_callback)
            self.client.registerCallback('disconnected', self._clientDisconnect_callback)

    @property
    def ip(self):
        return self.client.address

    # === METHODS ======================================================================================================
    def send(self, msg, source=None):

        # Encode the message
        data = self._encodeMessage(msg, source)

        self.client.send(data)
        self.sent += 1

    # ------------------------------------------------------------------------------------------------------------------
    def sendRaw(self, buffer):
        """
        - sends raw data over the TCP Client. For debug purposes only
        :param buffer: Byte array to be sent
        :return:
        """
        self.client.send(buffer)
        self.sent += 1

    # ------------------------------------------------------------------------------------------------------------------
    def registerCallback(self, callback_id, function, parameters: dict = None, lambdas: dict = None):
        """

        :param callback_id:
        :param function:
        :param parameters:
        :param lambdas:
        """
        callback = utils.Callback(function, parameters, lambdas)
        if callback_id in self.callbacks:
            self.callbacks[callback_id].append(callback)
        else:
            raise Exception("Invalid Callback type")

    # === PRIVATE METHODS ==============================================================================================
    def _encodeMessage(self, msg: Message, source=None):
        """

        :param msg:
        :param source:
        :return:
        """
        # Check if the message has a supported protocol
        if next((protocol for name, protocol in self.protocols.items() if protocol == msg._protocol), None) is None:
            logger.warning("Protocol not supported")
            return

        # Generate the payload
        payload = msg.encode()

        if msg._protocol is not self.protocols['base']:
            # Generate the overall message
            basemsg = self.protocols['base'].Message()
            basemsg.data_protocol_id = msg._protocol.identifier

            if source is None:
                source = addresses.server

            basemsg.src = bytes(source)
            basemsg.add = bytes(self.address)
            basemsg.data = payload
            buffer = basemsg.encode()
        else:
            buffer = payload

        return buffer

    # ------------------------------------------------------------------------------------------------------------------
    def _processIncomingHandshake(self, handshake_msg: TCP_Handshake_Message):
        """

        :param handshake_msg:
        """
        self.address = handshake_msg.address
        self.name = handshake_msg.name
        if TCP_JSON_Protocol.identifier in handshake_msg.protocols:  # TODO: This should be in a file somewhere
            self.protocols['json'] = TCP_JSON_Protocol

        for callback in self.callbacks['handshake']:
            callback(self, handshake_msg)

    # ------------------------------------------------------------------------------------------------------------------
    def _processDataPacket(self, data):
        """

        :param data:
        :return:
        """
        # Decode the data into a message
        base_msg: TCP_Base_Message = self.protocols['base'].decode(data)

        if base_msg is None:
            # the received data package is not a valid TCP message
            self.error_packets += 1
            return None

        # The received message is valid
        self.received += 1
        self.last_contact = time.time()

        # Check if the protocol ID uses a protocol known to the device
        # Protocol 0 is the base protocol
        if base_msg.data_protocol_id == self.protocols['base'].identifier:
            logger.warning(f"")
            return

        # Protocol 1 is the handshake protocol
        if base_msg.data_protocol_id == self.protocols['handshake'].identifier:
            msg = self.protocols['handshake'].decode(base_msg.data)
            self._processIncomingHandshake(msg)
            return

        # Another protocol is used
        protocol = next(
            (protocol for name, protocol in self.protocols.items() if
             protocol.identifier == base_msg.data_protocol_id),
            None)

        if protocol is not None:
            msg = protocol.decode(base_msg.data)
        else:
            logger.warning(f"TCP Device {self.address}: Unknown protocol with id {base_msg.data_protocol_id}")
            return

        logger.debug(
            f" (TCP RX) Device: \"{self.name}\", Protocol: {base_msg.data_protocol_id}, data: {base_msg.data}")

        if self.config['rx_queue']:
            self.rx_queue.put_nowait(msg)

        for callback in self.callbacks['rx']:
            callback(msg)

        self.events['rx'].set()

    # ------------------------------------------------------------------------------------------------------------------
    # def _thread_fun(self):
    #     pass

    # ------------------------------------------------------------------------------------------------------------------
    def _clientRx_callback(self, *args, **kwargs):
        """
        - callback called when the socket receives data
        :param args:
        :param kwargs:
        :return:
        """
        # TODO: this is bad and blocks all other receiving things. This
        #  should be in a separate thread
        while self.client.rx_queue.qsize() > 0:
            buffer = self.client.rx_queue.get_nowait()
            self._processDataPacket(buffer)

    # ------------------------------------------------------------------------------------------------------------------
    def _clientDisconnect_callback(self, client):

        for callback in self.callbacks['disconnected']:
            callback(self)
