import orjson

from archive.cm4_core_old2.communication.protocols import Protocol, RawMessage
from .tcp_protocol import TCP_Protocol


class TCP_JSONMessage(RawMessage):
    data: dict


class _TCP_JSONProtocol(Protocol):
    base_protocol = TCP_Protocol
    RawMessage = TCP_JSONMessage
    protocol_identifier = 0x02

    def decode(self, data: bytes):
        assert (isinstance(data, bytes))
        msg = self.RawMessage()
        msg.data = orjson.loads(data)
        return msg

    def encode(self, msg: TCP_JSONMessage, base_encode=False):
        """

        :param base_encode:
        :param msg:
        :return:
        """
        data = orjson.dumps(msg.data)

        return data

    def checkMessage(self, data):
        return 1


TCP_JSONProtocol = _TCP_JSONProtocol()
TCP_JSONMessage.protocol = TCP_JSONProtocol
