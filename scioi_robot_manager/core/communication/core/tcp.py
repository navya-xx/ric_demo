import dataclasses
import logging
import queue
import sys
import threading
import time
import socket

import cobs.cobs as cobs

from core.utils.network import getIP

logger = logging.getLogger('tcp')
logger.setLevel('INFO')

PACKAGE_TIMEOUT_TIME = 5
FAULTY_PACKAGES_MAX_NUMBER = 10


@dataclasses.dataclass
class FaultyPackage:
    timestamp: float


########################################################################################################################
class TCP_Client:
    address: str  # IP address of the client

    rx_queue: queue.Queue  # Queue of incoming messages from the client
    tx_queue: queue.Queue  # Queue of outgoing messages to the client
    config: dict

    rx_callback: callable  # Callback function that is called as soon as a message is received
    rx_event: threading.Event

    _connection: socket.socket

    _rxThread: threading.Thread

    _faultyPackages: list

    # === INIT =========================================================================================================
    def __init__(self, connection: socket, address: str):
        self._connection = connection
        self.address = address

        # connect readyRead-Signal to _rxReady function
        # socket.readyRead.connect(self._rxReady)

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

        self._faultyPackages = []

        self._rxThread = threading.Thread(target=self._rx_thread_fun, daemon=True)
        self._rxThread.start()

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
        self._write(data)
        # self.tx_queue.put_nowait(data)

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
        self._connection.close()
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
    # def _thread_fun(self):
    #     """
    #
    #     :return:
    #     """
    #     while not self._exit:
    #         data = self.tx_queue.get(timeout=None)
    #         self._write(data)
    #         time.sleep(0.0001)

    # ------------------------------------------------------------------------------------------------------------------
    def _rx_thread_fun(self):

        while not self._exit:
            try:
                data = self._connection.recv(8092)
            except Exception as e:
                logging.warning("Error in TCP connection. Close connection")
                self.close()
                return

            if data == b'':
                self.close()
            elif data is not None:
                try:
                    self._processRxData(data)
                except Exception:
                    ...  # TODO: Not good and hacky

            else:  # data is empty -> Device has disconnected
                self.close()

            # Remove the faulty packages older than PACKAGE_TIMEOUT_TIME
            self._faultyPackages = [package for package in self._faultyPackages if time.time() < (package.timestamp + PACKAGE_TIMEOUT_TIME)]


            # Send a warning if more than FAULTY_PACKAGES_MAX_NUMBER faulty packages have been received
            # in the last PACKAGE_TIMEOUT_TIME seconds
            if len(self._faultyPackages) > FAULTY_PACKAGES_MAX_NUMBER:
                logger.warning(
                    f"Received {FAULTY_PACKAGES_MAX_NUMBER} of faulty TCP packages in the last {PACKAGE_TIMEOUT_TIME} seconds")

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
        self._connection.sendall(data)

    # ------------------------------------------------------------------------------------------------------------------

    def _processRxData(self, data):
        """
        - This functions takes the received byte stream and chops it into data packets. This makes the assumption that
        the separator is not used in the byte stream itself. This can be accomplished by only sending strings or
        cobs-encoded data
        cobs-encoded data
        :param data:
        :return:
        """
        data_packets = data.split(self.config['delimiter'])
        if not data_packets[-1] == b'':
            self._faultyPackages.append(FaultyPackage(timestamp=time.time()))
            return

        data_packets = data_packets[0:-1]

        if self.config['cobs']:
            for i, packet in enumerate(data_packets):
                try:
                    data_packets[i] = cobs.decode(packet)
                except Exception:
                    self._faultyPackages.append(FaultyPackage(timestamp=time.time()))
                    return
                    # logger.warning("Received incompatible message which cannot be COBS decoded")

        for packet in data_packets:
            self.rx_queue.put_nowait(packet)

        self.rx_event.set()

        for callback in self.callbacks['rx']:
            callback(self)


########################################################################################################################
class TCP_Host:
    """

    """
    address: str
    port: int
    clients: list[TCP_Client]  # List of the connected clients

    _thread: threading.Thread

    _server: socket.socket
    config: dict
    callbacks: dict

    _exit: bool

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

        self.callbacks = {
            'client_connected': [],
            'client_disconnected': [],
            'server_error': []
        }

        self._exit = False

        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # ------------------------------------------------------------------------------------------------------------------
    def start(self):
        self._thread = threading.Thread(target=self._threadFunction, daemon=True)
        self._thread.start()

    # ------------------------------------------------------------------------------------------------------------------
    def close(self):
        logger.info(f"TCP host closed on {self.address}:{self.port}")
        self._exit = True
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

    # ------------------------------------------------------------------------------------------------------------------
    def _threadFunction(self):
        server_address = (self.address, self.port)
        self._server.bind(server_address)
        self._server.listen(self.config['max_clients'])
        logger.info(f"Starting TCP host on {self.address}:{self.port}")

        while not self._exit:
            connection, client_address = self._server.accept()
            self._acceptNewClient(connection, client_address)

    # ------------------------------------------------------------------------------------------------------------------
    def _acceptNewClient(self, connection, address):
        """
         -handling of accepting a new client
         -create a new client object with the socket of the newly accepted client
         :return: nothing
         """
        client = TCP_Client(connection, address)

        self.clients.append(client)

        logger.info(f"New client connected: {client.address}")
        # emit new connection signal with peer address and peer port to the interface

        client.registerCallback('disconnected', self._clientClosed_callback)

        for callback in self.callbacks['client_connected']:
            callback(client)

    # ------------------------------------------------------------------------------------------------------------------
    def _clientClosed_callback(self, client: TCP_Client):
        """
        close a socket once the client has disconnected
        :param client:
        :return: nothing
        """
        # remove client from list
        self.clients.remove(client)
        for cb in self.callbacks['client_disconnected']:
            cb(client)
