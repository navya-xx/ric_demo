#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Created By  : David Stoll
# Supervisor  : Dustin Lehmann
# Created Date: date/month/time ..etc
# version ='1.0'
# ---------------------------------------------------------------------------
""" This Module is responsible for receiving the Host-Server Ip via UDP """
# ---------------------------------------------------------------------------
# Module Imports
import errno
import logging
import queue
import select
import socket
import threading
import time
from enum import Enum
import cobs.cobs as cobs

from archive.cm4_core_old2.utils.time import time_ms

MAX_SOCKET_READ = 8192


# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

def getHostIP(timeout=None):
    logging.info("Listening for host IP on UDP...")
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
    client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    client.bind(("", 37020))
    client.settimeout(timeout)
    try:
        data, addr = client.recvfrom(1024)
    except socket.timeout:
        logging.warning(f"Timeout: No host IP received")
        return None
    # decode received data to string
    data = (data.decode('utf-8'))
    # set host address of event to received data
    logging.info(f"Received host ip: {data}")
    return data


class SocketState(Enum):
    """
    class to describe the current state of socket
    """
    NOT_CONNECTED = 0
    CONNECTED = 1


class TCP_Socket:
    """

    """
    server_address: str
    server_port: int
    _socket: socket.socket

    rx_queue: queue.Queue
    tx_queue: queue.Queue

    config: dict

    _input_connections: list
    _output_connections: list

    _exit: bool
    _thread: threading.Thread
    _tx_thread: threading.Thread

    _close_check_time: int
    _close_check_interval_ms = 1000

    delimiter: bytes

    callbacks: dict[str, list]
    events: dict[str, threading.Event]

    # === INIT =========================================================================================================
    def __init__(self, server_address: str = None, server_port: int = 6666, config: dict = None):
        """

        :param server_address:
        :param server_port:
        """
        self.server_address = server_address
        self.server_port = server_port

        self.state = SocketState(SocketState.NOT_CONNECTED)

        self.rx_queue = queue.Queue()
        self.tx_queue = queue.Queue()

        self._socket = None

        self._exit = False

        self._input_connections = []
        self._output_connections = []

        if config is None:
            config = {}

        default_config = {
            'delimiter': b'\x00',
            'cobs': True
        }
        self.config = {**default_config, **config}

        self.callbacks = {
            'connected': [],
            'disconnected': [],
            'error': [],
            'rx': [],
        }

        self.events = {
            'connected': threading.Event(),
            'disconnected': threading.Event(),
            'error': threading.Event(),
            'rx': threading.Event()
        }

        self._close_check_time = 0

    # === METHODS ======================================================================================================
    def start(self):
        """

        :return:
        """
        if self.server_address is None or self.server_port is None:
            raise Exception("Cannot start socket without address")

        logging.info(f"Starting Socket")
        self._thread = threading.Thread(target=self._thread_fun)
        self._thread.start()

        self._tx_thread = threading.Thread(target=self._tx_thread_fun, daemon=True)
        self._tx_thread.start()

    # ------------------------------------------------------------------------------------------------------------------
    def close(self):
        """

        :return:
        """
        self._exit = True

    # ------------------------------------------------------------------------------------------------------------------
    def send(self, data, force=False):
        """

        :param force:
        :param data:
        :return:
        """

        if self.state == SocketState.CONNECTED or force:
            self.tx_queue.put_nowait(data)
            return 1
        else:
            return 0

    # ------------------------------------------------------------------------------------------------------------------
    def registerCallback(self, type, callback):
        if type in self.callbacks.keys():
            self.callbacks[type].append(callback)
        else:
            raise Exception("Callback not in list of known callbacks")

    # === PRIVATE METHODS ==============================================================================================
    def _thread_fun(self):
        """

        :return:
        """
        while not self._exit:
            self._step()
            time.sleep(0.001)

        self._socket.close()
        logging.info("Close TCP Socket")

    def _step(self):
        """

        :return:
        """

        if self.state == SocketState.NOT_CONNECTED:
            self._connect(self.server_address, self.server_port)

        readable, writable, exceptional = select.select(self._input_connections, self._output_connections,
                                                        self._input_connections, 0)

        # Check if the connection was closed:
        if time_ms() > (self._close_check_time + self._close_check_interval_ms):
            closed = self._remote_connection_closed()
            self._close_check_time = time_ms()

            if closed:
                logging.warning(f"Socket: Lost connection to server on {self.server_address}")
                self.state = SocketState.NOT_CONNECTED
                self.events['connected'].clear()
                for cb in self.callbacks['disconnected']:
                    cb(self)

        # rx data
        for connection in readable:
            try:
                # save received data
                data = connection.recv(MAX_SOCKET_READ)
                if len(data) > 0:
                    self._rx_handling(data)

            except (ConnectionResetError, ConnectionAbortedError, InterruptedError):
                logging.warning(f"Lost connection with TCP server {self.server_address}")
                self._output_connections.remove(connection)
                self._input_connections.remove(connection)
                connection.close()
                self.state = SocketState.NOT_CONNECTED
                self.events['connected'].clear()
                for cb in self.callbacks['disconnected']:
                    cb(self)
                return

        # for connection in writable:
        #     # TODO
        #     pass

        for connection in exceptional:
            logging.error(f"Server exception with {connection.getpeername()}")
            self._input_connections.remove(connection)
            if connection in self._output_connections:
                self._output_connections.remove(connection)
            connection.close()

            for cb in self.callbacks['error']:
                cb(self)

    # ------------------------------------------------------------------------------------------------------------------
    def _tx_thread_fun(self):
        """
        - this thread handles the sending of the data over the TCP socket
        - it polls the tx_queue and if data is available it encodes the data, adds the delimiter and sends it over the
        TCP socket
        """
        while not self._exit:
            # Get the latest data from the queue:
            try:
                data = self.tx_queue.get(block=True, timeout=1)
            except queue.Empty:
                continue

            # Encode the data to utf-8 if it's a string
            if isinstance(data, str):
                data = data.encode('utf-8')
            elif isinstance(data, list):
                data = bytes(data)

            assert (isinstance(data, (bytes, bytearray)))

            # Encode the data and add a delimiter of those options are set
            if self.config['cobs']:
                data = cobs.encode(data)
            if self.config['delimiter'] is not None:
                data = data + self.config['delimiter']

            logging.debug(f"Sending: {data}")

            # Check if the output connection is writable
            writable = False
            while not writable:
                readable, writable, exceptional = select.select(self._input_connections, self._output_connections,
                                                                self._input_connections, 0)

            self._socket.send(data)  # Send the data over the socket

    # ------------------------------------------------------------------------------------------------------------------
    def _connect(self, server_address, server_port):
        """
        connect to client if server_address AND server Port are defined
        :param server_address: address of Host-Server
        :param server_port: port of Host-Server
        :return: nothing
        """
        self.server_address = server_address
        self.server_port = server_port

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        logging.info(f"Client: Connect to server {self.server_address}:{server_port}...")
        self._socket.connect((server_address, server_port))
        logging.info(f"Client: Connected to server {server_address}:{server_port}!")
        self._socket.setblocking(False)
        self._output_connections.append(self._socket)
        self._input_connections.append(self._socket)
        self.state = SocketState.CONNECTED

        for cb in self.callbacks['connected']:
            cb(self, server_address)

        self.events['connected'].set()

    # ------------------------------------------------------------------------------------------------------------------
    def _rx_handling(self, data: bytes):

        # Split the data by the delimiter
        data_packets = data.split(self.config["delimiter"])

        if not data_packets[-1] == b'':
            pass  # TODO: here i need some handling of incomplete packets

        data_packets = data_packets[0:-1]

        if self.config["cobs"]:
            for i, packet in enumerate(data_packets):
                try:
                    data_packets[i] = cobs.decode(packet)
                except:
                    pass  # TODO: This means we have cut a package in the middle

        for packet in data_packets:
            self.rx_queue.put_nowait(packet)
            # TODO: Should the callback be here?

        for cb in self.callbacks['rx']:
            cb()

        self.events['rx'].set()

        # --------------------------------------------------------------------------------------------------------------

    def _remote_connection_closed(self) -> bool:
        """
        Returns True if the remote side did close the connection

        """
        try:
            buf = self._socket.recv(1, socket.MSG_PEEK | socket.MSG_DONTWAIT)
            if buf == b'':
                return True
        except BlockingIOError as exc:
            if exc.errno != errno.EAGAIN:
                # Raise on unknown exception
                raise
        return False
