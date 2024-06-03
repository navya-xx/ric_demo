import dataclasses
from abc import ABC, abstractmethod

from device_manager.communication.protocols.protocol import Protocol, Message


class Connection(ABC):
    address: list
    ip: str
    name: str
    connected: bool  # True if the device is connected to the host
    registered: bool  # True if the device is connected and has identified itself

    protocols: dict = {}  # List of communication protocols supported by the device
    last_contact: float  # Time in s when the last message was received
    timeout: bool  # True if timeout event occurred for device
    sent: int  # Number of messages sent to that device
    received: int  # Number of messages received from that device
    error_packets: int  # Number of packets with errors

    _uid_mask: list

    def __init__(self):
        self.address = None
        self.name = None
        self.connected = False
        self.registered = False
        self.last_contact = None
        self.timeout = None
        self.sent = 0
        self.received = 0
        self.error_packets = 0

    @abstractmethod
    def send(self, message: Message):
        ...

    @abstractmethod
    def registerCallback(self, callback_id, function, parameters: dict = None, lambdas: dict = None):
        ...