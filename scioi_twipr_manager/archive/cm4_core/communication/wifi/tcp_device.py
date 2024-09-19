import dataclasses
import logging
import queue
import threading
import time
from _socket import socket

from .core.tcp_socket import TCP_Socket, getHostIP
from .protocols.tcp_handshake import TCP_DeviceHandshakeProtocol
from .protocols.tcp_protocol import TCP_Protocol
from ..protocols import Protocol, RawMessage


@dataclasses.dataclass
class TCP_ServerData:
    uid: list
    name: str
    address: int


class TCP_Device:
    """

    """
    _socket: TCP_Socket
    server: TCP_ServerData
    uid: list
    name: str
    protocols: dict[str, Protocol]
    registered: bool
    connected: bool

    base_protocol = TCP_Protocol
    handshake_protocol = TCP_DeviceHandshakeProtocol

    rx_queue: queue.Queue
    tx_queue: queue.Queue
    callbacks: dict[str, list]
    events: dict[str, threading.Event]

    _exit: bool  # Exit the thread

    config: dict

    _thread: threading.Thread

    # === INIT =========================================================================================================
    def __init__(self, protocols: dict = None, uid: list = None, name: str = None, config: dict = None):

        default_config = {
            'rx': 'poll',  # Could also be 'callback'
        }

        if protocols is None:
            protocols = {}

        if config is None:
            config = {}

        if uid is None:
            uid = [0, 0, 0, 0]

        if name is None:
            name = "noname"

        self.config = {**default_config, **config}

        self.protocols = protocols
        self.uid = uid
        self.name = name

        self.registered = False
        self.connected = False

        # Prepare the RX and TX queue
        self.rx_queue = queue.Queue()
        self.tx_queue = queue.Queue()

        # Prepare the callbacks and events
        self.callbacks = {
            'rx': [],
            'connected': [],
            'disconnected': [],
            'error': [],
            'registered': [],
        }

        self.events = {
            'rx': threading.Event(),
            'connected': threading.Event(),
            'disconnected': threading.Event(),
            'error': threading.Event(),
            'registered': threading.Event()
        }

        # Prepare the data structure for the server
        self.server = TCP_ServerData(address=None, uid=None, name=None)

        # Configure the Socket
        socket_config = {
            'delimiter': b'\x00',
            'cobs': True
        }

        # Initialize the TCP Socket and register the callbacks
        self._socket = TCP_Socket(config=socket_config)
        self._socket.registerCallback('connected', self._socket_connect_callback)
        self._socket.registerCallback('disconnected', self._socket_disconnect_callback)

        self._exit = False

    # === PROPERTIES ===================================================================================================
    # === METHODS ======================================================================================================
    def start(self):
        # Listen to the Host IP on UDP. If the timeout is reached, an Exception will be thrown
        ip = getHostIP(timeout=5)
        if ip is None:
            raise Exception("Cannot find server IP")

        # If a valid ip has been received, set the corresponding server ip in the socket
        self.server.address = ip
        self._socket.server_address = ip

        # Start the socket
        self._socket.start()

        # Start the Thread
        self._thread = threading.Thread(target=self._thread_fun, daemon=True)
        self._thread.start()

    # ------------------------------------------------------------------------------------------------------------------
    def send(self, msg: RawMessage):
        """
        - send a message over the TCP socket. The message has to have a known protocol
        :param msg:
        :return:
        """
        ret = 0
        buffer = self._encode_message(msg)

        if buffer is not None:
            ret = self._socket.send(buffer)  # TODO: include a return value

        return ret

    # ------------------------------------------------------------------------------------------------------------------
    def sendRaw(self, buffer):
        ret = self._socket.send(buffer)
        return ret

    # ------------------------------------------------------------------------------------------------------------------
    def registerCallback(self, type, callback):
        """
        - register a callback function for one of the given callbacks in self.callbacks
        :param type: str -> string identifier of the callback
        :param callback: callable -> function to be called when the callback is invoked
        :return: None
        """
        if type in self.callbacks.keys():
            self.callbacks[type].append(callback)
        else:
            raise Exception("Callback not in list of supported callbacks")

    # ------------------------------------------------------------------------------------------------------------------
    def close(self):
        self._exit = True

    # === PRIVATE METHODS ==============================================================================================
    def _thread_fun(self):
        """
        - this functions runs in a thread and manages the TCP Client
        :return:
        """

        # Wait for the socket to be connected
        # connected = self._socket.events['connected'].wait(timeout=5)
        #
        # if not connected:
        #     logging.warning(f"Cannot connect to server with address {self.server.address}")
        #
        # logging.info(f"TCP Device: Successfully connected to server with address {self.server.address}")

        # Send the handshake to the server


        # Wait for the handshake to come back
        # ret = self.events['registered'].wait(timeout=2)
        # if not ret:
        #     raise Exception("Server is not responding to handshake")

        # Start the reception of data
        while not self._exit:

            if not self.connected:
                connected = self._socket.events['connected'].wait(timeout=1)
                if connected:
                    self.connected = True
                    self._send_handshake()
                    logging.info(f"TCP Device: Successfully connected to server with address {self.server.address}")

            try:
                data = self._socket.rx_queue.get(timeout=2)
            except queue.Empty:
                continue
            self._rx_function(data)

        # Exit
        self._socket.close()
        logging.info("Close TCP Client")

    # ------------------------------------------------------------------------------------------------------------------
    def _encode_message(self, msg: RawMessage):
        """

        :param msg:
        :return:
        """
        # Check if the message has a supported protocol
        if msg.protocol is not self.handshake_protocol and next(
                (protocol for name, protocol in self.protocols.items() if protocol == msg.protocol), None) is None:
            logging.warning("Protocol not supported")
            return

        # Generate the payload data
        payload = msg.encode()

        # Generate the base message
        basemsg = self.base_protocol.RawMessage()
        basemsg.data_protocol_id = msg.protocol.protocol_identifier
        basemsg.source = [0, 0]  # TODO
        basemsg.address = [0, 0]  # TODO
        basemsg.data = payload
        buffer = basemsg.encode()

        return buffer

    # ------------------------------------------------------------------------------------------------------------------
    def _decode_message(self, buffer: bytes):
        """
        - decode a given buffer into a known protocol and return the RawMessage
        :param buffer:
        :return:
        """
        # Decode the base protocol
        msg: TCP_Device.base_protocol.RawMessage = self.base_protocol.decode(buffer)
        msg_out = msg
        if msg is None:
            logging.warning(f"TCP Device: Incompatible message received")
            return None

        # Base protocol
        if msg.data_protocol_id == self.base_protocol.protocol_identifier:
            pass  # TODO

        # Handshake
        if msg.data_protocol_id == self.handshake_protocol.protocol_identifier:
            msg_out = self.handshake_protocol.decode(msg.data)

        # Data protocols
        if msg.data_protocol_id != self.base_protocol.protocol_identifier \
                and msg.data_protocol_id != self.handshake_protocol.protocol_identifier:

            protocol = next(
                (protocol for name, protocol in self.protocols.items() if
                 protocol.protocol_identifier == msg.data_protocol_id),
                None)

            if protocol is not None:
                msg_out = protocol.decode(msg.data)
            else:
                logging.warning(f"TCP Device {self.uid}: Unknown protocol with id {msg._protocol}")

        return msg_out

    # ------------------------------------------------------------------------------------------------------------------
    def _receive_handshake(self, handshake_msg: handshake_protocol.RawMessage):
        """
        - function is called if a handshake message has been received.
        :param handshake_msg:
        :return:
        """
        # Set the server info from the received handshake data
        self.server.uid = handshake_msg.address
        self.server.name = handshake_msg.name

        self.registered = True

        logging.info(f"Registered device with server \"{self.server.name}\"")
        for cb in self.callbacks['registered']:
            cb(self, self.server)

        self.events['registered'].set()

    # ------------------------------------------------------------------------------------------------------------------
    def _send_handshake(self):
        """
        - sends a handshake message to the TCP server
        :return:
        """
        msg = self.handshake_protocol.RawMessage()

        msg.address = self.uid
        msg.name = self.name
        msg.protocols = [protocol.protocol_identifier for _, protocol in self.protocols.items()]
        self.send(msg)

    # ------------------------------------------------------------------------------------------------------------------
    def _rx_function(self, data):  # TODO: Rename
        """

        :param data:
        :return:
        """
        # Decode the data into a message
        message = self._decode_message(data)

        if message is None:
            return  # TODO

        if message.protocol == self.base_protocol:
            return  # TODO

        # Handshake
        elif message.protocol == self.handshake_protocol:
            self._receive_handshake(message)

        # Data protocol
        else:
            self.rx_queue.put_nowait(message)

            for cb in self.callbacks['rx']:
                cb(device=self, message=message)

            self.events['rx'].set()

    # logging.debug(f"TCP Device [\"{self.name}\"] RX: Protocol: [{msg.data_protocol_id}]  data: {msg.data}")

    # ------------------------------------------------------------------------------------------------------------------
    def _socket_connect_callback(self, *args, **kwargs):
        pass

    # ------------------------------------------------------------------------------------------------------------------
    def _socket_disconnect_callback(self, *args, **kwargs):
        self.connected = False
        logging.warning("Lost connection to server")
