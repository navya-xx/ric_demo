import typing

import dataclasses
from abc import ABC, abstractmethod
from typing import Union


class RawMessage:
    protocol: 'Protocol' = None

    def __init__(self, **kwargs):
        hints = typing.get_type_hints(self)
        for key, value in kwargs.items():
            if key in hints:
                setattr(self, key, value)

    def encode(self):
        return self.protocol.encode(self)


# TODO
class BaseProtocol(ABC):
    RawMessage: type


class Protocol(ABC):
    RawMessage: type
    base_protocol: 'Protocol'
    protocol_identifier: int

    def __init__(self):
        pass

    @abstractmethod
    def decode(self, data):
        pass

    @abstractmethod
    def encode(self, msg: RawMessage):
        pass

    @abstractmethod
    def checkMessage(self, data):
        pass
