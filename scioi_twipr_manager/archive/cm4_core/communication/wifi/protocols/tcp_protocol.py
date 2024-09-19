from typing import Union
import logging

from archive.cm4_core_old2.communication.protocols import Protocol, RawMessage
from archive.cm4_core_old2.utils.bytes import bytearray_to_string


class TCP_Message(RawMessage):
    data_protocol_id: int
    src: list
    add: list
    data: list


class _TCP_Protocol(Protocol):
    """
    |   BYTE    |   NAME            |   DESCRIPTION                 |   VALUE
    |   0       |   HEADER[0]       |   first header byte           |   0x55
    |   1       |   HEADER[1]       |   second header byte          |   0x55
    |   2       |   SRC[0]          |   Source ID                   |
    |   3       |   SRC[1]          |   Source ID                   |
    |   4       |   ADD[0]          |   Address                     |
    |   5       |   ADD[1]          |   Address                     |
    |   6       |   PROTOCOL        |   Protocol ID                 |
    |   7       |   LEN[0]          |   Length of the payload       |
    |   8       |   LEN[1]          |   Length of the payload       |
    |   9       |   PAYLOAD[0]      |   Payload                     |
    |   9+N-1   |   PAYLOAD[N-1]    |   Payload                     |
    |   9+N     |   CRC8            |   CRC8 of the Payload         |
    |   10+N     |   FOOTER          |   Footer                      |   0x5D
    """
    base_protocol = None
    protocol_identifier = 0
    RawMessage = TCP_Message

    idx_protocol = 6
    idx_src = slice(2, 4)
    idx_add = slice(4, 6)
    idx_len = slice(7, 9)
    idx_payload = 9
    offset_crc = 9
    offset_footer = 10

    header_0 = 0x55
    header_1 = 0x55
    footer = 0x5D

    protocol_overhead = 11

    def __init__(self):
        super().__init__()

    def decode(self, data: Union[list, bytes, bytearray]):
        check = self.checkMessage(data)

        if not check:
            logging.debug(f"Corrupted TCP message received")
            return

        msg = TCP_Message()
        msg.data_protocol_id = data[self.idx_protocol]
        msg.src = data[self.idx_src]
        msg.add = list(data[self.idx_add])
        payload_len = int.from_bytes(data[self.idx_len], byteorder="little")
        msg.data = data[self.idx_payload:self.idx_payload + payload_len]
        logging.debug(
            f"TCP Message:[PROTOCOL: [{bytearray_to_string(msg.data_protocol_id)}], SRC: [{bytearray_to_string(msg.src)}], ADD: "
            f"[{bytearray_to_string(msg.add)}], DATA: [{bytearray_to_string(msg.data)}]]")
        return msg

    def encode(self, msg: TCP_Message, base_encode=False):
        """
        - Encode a TCP message from a given TCP_Message
        :param msg: TCP_Message object
        :param base_encode: Since the TCP_Protocol has no base protocol, this is not used
        :return: byte buffer of the message
        """
        assert (isinstance(msg, TCP_Message))
        buffer = [0] * (len(msg.data) + self.protocol_overhead)
        buffer[0] = self.header_0
        buffer[1] = self.header_1
        buffer[self.idx_src] = msg.src
        buffer[self.idx_add] = msg.add
        buffer[self.idx_protocol] = msg.data_protocol_id
        buffer[self.idx_len] = len(msg.data).to_bytes(length=2, byteorder="little")
        buffer[self.idx_payload: self.idx_payload + len(msg.data)] = msg.data
        buffer[self.offset_crc + len(msg.data)] = 0x00  # TODO
        buffer[self.offset_footer + len(msg.data)] = self.footer
        buffer = bytes(buffer)
        return buffer

    def checkMessage(self, data):
        if not data[0] == self.header_0:
            return 0
        if not data[1] == self.header_1:
            return 0

        payload_len = int.from_bytes(data[self.idx_len], byteorder="little")
        if not len(data) == payload_len + self.protocol_overhead:
            return 0

        if not data[payload_len + self.offset_footer] == self.footer:
            return 0

        return 1


TCP_Protocol = _TCP_Protocol()
TCP_Message.protocol = TCP_Protocol
