import logging
import time

from core.communication.core.tcp import TCP_Host, TCP_Client
from core.communication.core.udp import UDP_Server, UDP_Broadcast
import core.communication.protocols as protocols
from core.utils.network import getIP
import core.communication.addresses as addresses
from core.communication.tcp_connection import TCP_Connection
from utils.logging import Logger

logger = Logger('server')
logger.setLevel('INFO')


# ======================================================================================================================
class TCP_Server:
    connections: list[TCP_Connection]

    base_protocol = protocols.tcp.tcp_base_protocol.TCP_Base_Protocol
    handshake_protocol = protocols.tcp.tcp_handshake_protocol.TCP_Handshake_Protocol

    data_protocols = {
        'json': protocols.tcp.tcp_json_protocol.TCP_JSON_Protocol,
        'handshake': protocols.tcp.tcp_handshake_protocol.TCP_Handshake_Protocol
    }

    callbacks: dict
    address: str

    _unregistered_connections: list[TCP_Connection]
    _tcp_host: TCP_Host
    _udp_host: UDP_Server

    # === INIT =========================================================================================================
    def __init__(self, address=None):

        # If no specific address is specified, look for a local IP to host the server
        if address is None:
            addresses = getIP()
            if addresses is None:
                logger.error("No local network found. Cannot create server!")
                exit()
            address = addresses['local']
            if address is None:
                address = addresses['usb']
                if address is None:
                    logger.error("No local or USB IP found. Specify an address to start the server")
                    exit()

        self.address = address

        self._tcp_host = TCP_Host(address=self.address)
        self._udp_host = UDP_Server(address=self.address)

        self.connections = []
        self._unregistered_connections = []

        self._configureServer()

        self.callbacks = {
            'connected': [],
            'disconnected': []
        }

    # === METHODS ======================================================================================================
    def registerCallback(self, callback_id, callback):
        if callback_id in self.callbacks.keys():
            self.callbacks[callback_id].append(callback)
        else:
            raise Exception(f"No callback with id {callback_id} is known.")

    # ------------------------------------------------------------------------------------------------------------------
    def start(self):
        logger.info(f"Starting server on {self.address}")
        self._startServer()

    # ------------------------------------------------------------------------------------------------------------------
    def close(self):
        self._tcp_host.close()
        self._udp_host.close()
        logger.info("TCP Server closed")
        time.sleep(0.01)

    # ------------------------------------------------------------------------------------------------------------------
    def getDevice(self, name=None, address=None):
        """

        :param name:
        :param address:
        :return:
        """
        assert (name is None or address is None)
        if name is not None:
            device = next((device for device in self.connections if device.name == name), None)
            return device

        if address is not None:
            device = next((device for device in self.connections if device.address == address), None)
            return device

    # ------------------------------------------------------------------------------------------------------------------
    def send(self, message, address):
        self._send(message, address)

    # ------------------------------------------------------------------------------------------------------------------
    def broadcast(self, message):
        for device in self.connections:
            device.send(message, source=addresses.server)

    # === PRIVATE METHODS ==============================================================================================
    def _configureServer(self):
        self._tcp_host.registerCallback('client_connected', self._deviceConnected_callback)
        self._tcp_host.registerCallback('client_disconnected', self._deviceDisconnected_callback)

        udp_broadcast = UDP_Broadcast()
        udp_broadcast.data = f"{self.address}:{self._tcp_host.port}"
        udp_broadcast.time = 1
        self._udp_host.addBroadcast(udp_broadcast)

    # ------------------------------------------------------------------------------------------------------------------
    def _startServer(self):
        self._udp_host.start()
        self._tcp_host.start()

    # ------------------------------------------------------------------------------------------------------------------
    def _send(self, message, address):
        if isinstance(address, list) and all(isinstance(elem, int) for elem in address):
            address = bytes(address)

        if isinstance(address, bytes):

            # TODO: Also consider groups
            if address == addresses.broadcast:  # Send to all devices
                self.broadcast(message)
            else:
                device = self.getDevice(address=address)
                if device is not None:
                    device.send(message, source=addresses.server)

        elif isinstance(address, str):
            if address == 'broadcast':
                self.broadcast(message)
            else:
                device = self.getDevice(name=address)
                if device is not None:
                    device.send(message, source=addresses.server)

        elif isinstance(address, TCP_Connection):
            address.send(message, source=addresses.server)

    # ------------------------------------------------------------------------------------------------------------------
    def _deviceConnected_callback(self, socket: TCP_Client, *args, **kwargs):
        # put the client into the list of unregistered tcp devices
        unregistered_device = TCP_Connection(client=socket)
        self._unregistered_connections.append(unregistered_device)
        unregistered_device.registerCallback('handshake', self._deviceHandshake_callback)

    # ------------------------------------------------------------------------------------------------------------------
    def _deviceDisconnected_callback(self, socket: TCP_Client, *args, **kwargs):

        # Check if the socket belongs to one of the unregistered devices
        if any(device for device in self._unregistered_connections if device.client == socket):
            unregistered_device = next((device for device in self._unregistered_connections
                                        if device.client == socket), None)
            if unregistered_device is not None:
                self._unregistered_connections.remove(unregistered_device)
                logger.info(f"Unregistered TCP device with address {unregistered_device.address} disconnected")

        # Check if the client belongs to a registered device
        if any(device for device in self.connections if device.client == socket):
            registered_device = next((device for device in self.connections if device.client == socket), None)
            if registered_device is not None:
                logger.info(
                    f"TCP Connection closed. [Name: \"{registered_device.name}\", Adress: {registered_device.address}]")
                self.connections.remove(registered_device)
                for callback in self.callbacks['disconnected']:
                    callback(registered_device)

    # ------------------------------------------------------------------------------------------------------------------
    def _deviceHandshake_callback(self, device: TCP_Connection, handshake_msg):
        # Check all protocol ids that the device supports and check if they are in the supported
        # data protocols of the server
        for protocol_id in handshake_msg.protocols:
            if protocol_id not in [protocol.identifier for name, protocol in
                                   self.data_protocols.items()]:
                logger.warning(f"Device ({device.address}) supports unknown protocol with ID {protocol_id}")

        # Check if the device is in the list of unregistered devices
        if device not in self._unregistered_connections:
            # there might be a problem here. Better raise an Exception for now
            logger.error(f"Device ({device.address}) tried to register, even though it is not in the list "
                          f"of unregistered devices")
            return

        # Check if the device is already in the list of registered devices
        # if device in self.connections:
        #     logger.error(f"Connection with ({device.address}) tried to register, even though it is already registered")
        #     return

        # Check if there is already a device with the same address
        # for d in self.connections:
        #     if device.address == d.address:
        #         logger.error(
        #             f"Connection ({device.address}) tried to register but there is already a connection with IP address {device.address}")
        #         return

        # Put the device into the list of registered devices
        self.connections.append(device)
        self._unregistered_connections.remove(device)
        device.registered = True

        logger.info(f"New TCP connection. Name: \"{device.name}\", Address: {device.address}")

        for callback in self.callbacks['connected']:
            callback(device)

        # Send the handshake back
        server_handshake_msg = protocols.tcp.tcp_handshake_protocol.TCP_Handshake_Message()
        server_handshake_msg.name = 'server'
        server_handshake_msg.protocols = [protocol.identifier for name, protocol in self.data_protocols.items()]
        server_handshake_msg.address = addresses.server
        device.send(server_handshake_msg, source=addresses.server)
