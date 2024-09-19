import typing

from ...protocols import Protocol, RawMessage


# noinspection PyTypeChecker
class UART_Message(RawMessage):
    cmd: int
    msg: int
    add: list
    data: typing.Union[list, bytes]


class _UART_Protocol(Protocol):
    """
       |   BYTE    |   NAME            |   DESCRIPTION                 |   VALUE
       |   0       |   HEADER[0]       |   first header byte           |   0x55
       |   1       |   ADD[0]          |   Address                     |
       |   2       |   ADD[1]          |   Address                     |
       |   3       |   CMD             |   Address                     |
       |   4       |   MSG             |   Address                     |
       |   5       |   LEN             |   Length of the payload       |
       |   6       |   PAYLOAD[0]      |   Payload                     |
       |   6+N-1   |   PAYLOAD[N-1]    |   Payload                     |
       |   6+N     |   CRC8            |   CRC8 of the Payload         |
       |   7+N    |   FOOTER          |   Footer                      |   0x5D
       """

    base_protocol = None
    protocol_identifier = 0
    RawMessage = UART_Message

    idx_header = 0
    header = 0x55
    footer = 0x5D
    idx_cmd = 3
    idx_add = slice(1, 3)
    idx_len = 5
    idx_msg = 4
    idx_payload = 6
    offset_crc8 = 6
    offset_footer = 7

    protocol_overhead = 8

    def decode(self, data):
        """

        :param data:
        :return:
        """
        msg = self.RawMessage()

        payload_len = data[self.idx_len]

        msg.cmd = data[self.idx_cmd]
        msg.msg = data[self.idx_msg]
        msg.add = list(data[self.idx_add])
        msg.data = data[self.idx_payload:self.idx_payload + payload_len]

        return msg

    def encode(self, msg: RawMessage):
        """

        :param msg:
        :return:
        """
        buffer = [0] * (self.protocol_overhead + len(msg.data))
        buffer[self.idx_header] = self.header
        buffer[self.idx_cmd] = msg.cmd
        buffer[self.idx_add] = msg.add
        buffer[self.idx_msg] = msg.msg
        buffer[self.idx_len] = len(msg.data)
        buffer[self.idx_payload:self.idx_payload + len(msg.data)] = msg.data
        buffer[self.offset_crc8 + len(msg.data)] = 0
        buffer[self.offset_footer + len(msg.data)] = self.footer
        buffer = bytes(buffer)
        return buffer

    def checkMessage(self, data):
        """

        :param data:
        :return:
        """
        payload_len = data[self.idx_len]

        if not data[self.idx_header] == self.header:
            return 0

        if not data[self.offset_footer + payload_len] == self.footer:
            return 0

        if not len(data) == (payload_len + self.protocol_overhead):
            return 0


UART_Protocol = _UART_Protocol()
UART_Message.protocol = UART_Protocol
