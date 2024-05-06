import dataclasses
import logging
import queue
import sys
import threading
import time
import cobs.cobs as cobs

from PySide6.QtNetwork import QHostAddress, QTcpServer, QTcpSocket
from PySide6.QtCore import QByteArray
from PyQt5.QtCore import QObject, pyqtSignal as Signal, QThread
from PySide6.QtWidgets import QApplication
from hardware_manager.utils.network import getIP

logger = logging.getLogger('tcp')
logger.setLevel('INFO')


########################################################################################################################
class TCP_Client:
    address: str  # IP address of the client

    rx_queue: queue.Queue  # Queue of incoming messages from the client
    tx_queue: queue.Queue  # Queue of outgoing messages to the client
    config: dict

    rx_callback: callable  # Callback function that is called as soon as a message is received
    rx_event: threading.Event

    _socket: QTcpSocket  # The socket in the server
    _thread: threading.Thread  # Thread handling the incoming and outgoing communication

    # === INIT =========================================================================================================
    def __init__(self, socket: QTcpSocket):
        self._socket = socket

        # connect readyRead-Signal to _rxReady function
        socket.readyRead.connect(self._rxReady)

        self.config = {
            'delimiter': b'\x00',
            'cobs': True
        }

        self.rx_queue = queue.Queue()
        self.tx_queue = queue.Queue()

        self._exit = False

        self.callbacks = {
            'rx': [],
            'disconnected': []
        }
        self.rx_event = threading.Event()

        # TODO: Should we do this? Or should the server itself send the stuff?
        self._thread = threading.Thread(target=self._thread_fun, daemon=True)
        self._thread.start()

    # === METHODS ======================================================================================================
    def registerCallback(self, callback_id, callback):
        if callback_id in self.callbacks.keys():
            self.callbacks[callback_id].append(callback)
        else:
            raise Exception(f"Device: No callback with id {callback_id} is known.")

    # ------------------------------------------------------------------------------------------------------------------
    def send(self, data):
        """

        :param data:
        :return:
        """
        data = self._prepareTxData(data)
        self.tx_queue.put_nowait(data)

    # ------------------------------------------------------------------------------------------------------------------
    def rxAvailable(self):
        """

        :return:
        """
        return self.rx_queue.qsize()

    # ------------------------------------------------------------------------------------------------------------------
    def close(self):
        """

        :return:
        """
        self._socket.close()
        self._exit = True
        logger.info(f"TCP socket {self.address} closed")

        for callback in self.callbacks['disconnected']:
            callback(self)

    # ------------------------------------------------------------------------------------------------------------------
    def setConfig(self, config):
        """
        Overrides the config with other values.
        :param config: New values for the config
        :return: None
        """
        self.config = {**self.config, **config}

    # === PRIVATE METHODS ==============================================================================================
    def _thread_fun(self):
        """

        :return:
        """
        while not self._exit:
            data = self.tx_queue.get(timeout=None)
            self._write(data)
            time.sleep(0.0001)

    # ------------------------------------------------------------------------------------------------------------------
    def _prepareTxData(self, data):
        if isinstance(data, list):
            data = bytes(data)

        # Encode the data and add a delimiter of those options are set
        if self.config['cobs']:
            data = cobs.encode(data)
        if self.config['delimiter'] is not None:
            data = data + self.config['delimiter']

        return data

    # ------------------------------------------------------------------------------------------------------------------
    def _write(self, data):
        self._socket.write(data)
        self._socket.flush()

    # ------------------------------------------------------------------------------------------------------------------
    def _rxReady(self):
        """

        :return:
        """
        num = self._socket.bytesAvailable()
        data = self._socket.read(num)  # Read the bytes from the incoming buffer
        data_packets = self._processRxData(data, separator=self.config['delimiter'], cobs_encoded=self.config[
            'cobs'])  # Get the data packets from the received byte stream

        for packet in data_packets:
            self.rx_queue.put_nowait(packet)

        self.rx_event.set()

        for callback in self.callbacks['rx']:
            callback(self)

    # ------------------------------------------------------------------------------------------------------------------
    @staticmethod
    def _processRxData(data, separator=b'\x00', cobs_encoded: bool = True):
        """
        - This functions takes the received byte stream and chops it into data packets. This makes the assumption that
        the separator is not used in the byte stream itself. This can be accomplished by only sending strings or
        cobs-encoded data
        :param data:
        :return:
        """

        # Split the data into data packets
        if isinstance(data, QByteArray):
            data = bytes(data)

        data_packets = data.split(separator)
        if not data_packets[-1] == b'':
            # TODO: I have a problem here because I have a datapacket that is not properly terminated
            logger.warning("Data packet corrupted")

        data_packets = data_packets[0:-1]

        if cobs_encoded:
            for i, packet in enumerate(data_packets):
                try:
                    data_packets[i] = cobs.decode(packet)
                except Exception:
                    logger.warning("Received incompatible message which cannot be COBS decoded")

        return data_packets


########################################################################################################################
class TCP_Host:
    """

    """
    address: str
    port: int
    clients: list[TCP_Client]  # List of the connected clients

    _thread: threading.Thread
    _server: '_QTcpServer_Wrapper'

    config: dict
    callbacks: dict

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self, address: str = None, hostname: bool = False, config: dict = None):
        """

        :param address:
        :param hostname:
        """
        super().__init__()

        default_config = {
            'max_clients': 100,
            'port': 6666,
        }

        if config is None:
            config = {}

        self.config = {**default_config, **config}

        self.clients = []

        if address is None and hostname is True:
            self.address = getIP()['hostname']
        elif address is not None:
            self.address = address
        else:
            raise Exception()

        self.port = self.config['port']
        self._server = None

        self.callbacks = {
            'client_connected': [],
            'client_disconnected': [],
            'server_error': []
        }

    # ------------------------------------------------------------------------------------------------------------------
    def start(self):
        self._thread = threading.Thread(target=self._thread_fun, daemon=True)
        self._thread.start()

    # ------------------------------------------------------------------------------------------------------------------
    def _thread_fun(self):
        self._server = _QTcpServer_Wrapper(address=self.address, port=self.port, clients=self.clients,
                                           config=self.config, callbacks=self.callbacks)
        self._server.start()

    # ------------------------------------------------------------------------------------------------------------------
    def close(self):
        logger.info(f"TCP host closed on {self.address}:{self.port}")
        self._server._exit = True
        self._thread.join()

    # ------------------------------------------------------------------------------------------------------------------
    def send(self):
        pass

    # ------------------------------------------------------------------------------------------------------------------
    def registerCallback(self, type, callback):
        if type in self.callbacks.keys():
            self.callbacks[type].append(callback)
        else:
            raise Exception("Callback not in list of valid callbacks.")


########################################################################################################################
class _QTcpServer_Wrapper(QObject):
    config: dict
    callbacks: dict
    new_client_signal = Signal(str, int)

    _host_address: QHostAddress
    _server: QTcpServer
    _thread: QThread
    _exit: bool

    def __init__(self, address, port, clients, config=None, callbacks: dict = None):
        super().__init__()

        default_config = {
            'max_clients': 100
        }

        if config is None:
            config = {}

        self.config = {**default_config, **config}

        self.address = address
        self.port = port
        self.clients = clients

        self._exit = False

        self._host_address = QHostAddress(self.address)
        self._thread = QThread()
        self._server = QTcpServer()
        self.app: QApplication = None

        if callbacks is not None:
            self.callbacks = callbacks
        else:
            self.callbacks = {}

    # ------------------------------------------------------------------------------------------------------------------
    def start(self):
        """
        start the Host Server:
        - listen for new connections
        - move the HostServer to a new thread where it is being executed
        - connect the start signal of the thread to the run method of HostServer
        - start the HostServer in the thread
        :return: nothing
        """
        self.app = QApplication(sys.argv)
        self._listen()
        self.moveToThread(self._thread)
        self._thread.started.connect(self._run)
        self._thread.start()
        self.app.exec_()
        time.sleep(1)

    # ------------------------------------------------------------------------------------------------------------------
    def _run(self):
        """

        :return:
        """
        while not self._exit:
            time.sleep(0.1)

        self._server.close()
        self._thread.terminate()
        self.app.quit()

    # ------------------------------------------------------------------------------------------------------------------
    def _listen(self):
        """
        - listen on the selected Ip for new connections
        - connect the accept_new_client-function to the Signal that is connected once there is a new Connection
        :return: nothing
        """
        self._server.setMaxPendingConnections(self.config['max_clients'])
        self._server.listen(self._host_address, self.port)
        logger.info(f"Starting TCP host on {self._server.serverAddress().toString()}:{self._server.serverPort()}")

        self._server.newConnection.connect(self._accept_new_client)

    # ------------------------------------------------------------------------------------------------------------------
    def _accept_new_client(self):
        """
         -handling of accepting a new client
         -create a new client object with the socket of the newly accepted client
         :return: nothing
         """
        socket = self._server.nextPendingConnection()
        client = TCP_Client(socket)

        self.clients.append(client)

        peer_address = socket.peerAddress().toString()
        peer_port = socket.peerPort()

        client.address = peer_address

        logger.debug(f"New client connected: {peer_address}:{peer_port}")
        # emit new connection signal with peer address and peer port to the interface
        self.new_client_signal.emit(peer_address, peer_port)
        # quick fix: the buffering number depends on the size of the biggest message
        socket.setReadBufferSize(10000)  # TODO: Magic number
        # connect error-Signal to close_socket function of new client to call after connection ended
        socket.error.connect(lambda: self._close_socket(client))

        for callback in self.callbacks['client_connected']:
            callback(client)

    # ------------------------------------------------------------------------------------------------------------------
    def _close_socket(self, client: TCP_Client):
        """
        close a socket once the client has disconnected
        :param client:
        :return: nothing
        """
        # handle client connection
        client.close()
        # remove client from list
        self.clients.remove(client)
        for cb in self.callbacks['client_disconnected']:
            cb(client)
        self._server.resumeAccepting()
