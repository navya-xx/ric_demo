from .tcp_protocol import TCP_Protocol
from archive.cm4_core_old2.communication.protocols import Protocol, RawMessage


class TCP_DeviceHandshakeMessage(RawMessage):
    uid: list
    protocols: list
    name: str


class _TCP_DeviceHandshakeProtocol(Protocol):
    """
    |   BYTE    |   NAME            |   DESCRIPTION                     |   VALUE
    |   0       |   HEADER          |   Header Byte                     |   0x7F
    |   1       |   UID[0]          |   UID                             |
    |   2       |   UID[1]          |   UID                             |
    |   3       |   UID[2]          |   UID                             |
    |   4       |   UID[3]          |   UID                             |
    |   5       |   NUM_PROTOCOLS   |   number of protocols N           |
    |   6       |   PROTOCOL[0]     |   first protocol                  |
    |   7       |   PROTOCOL[1]     |   second protocol                 |
    |   6+N-1   |   PROTOCOL[N]     |   last protocol                   |
    |   6+N     |   LEN_NAME        |   number of bytes M in the name   |
    |   7+N     |   NAME[0]         |   name                            |
    |   8+N     |   NAME[1]         |   name                            |
    |   7+M+N   |   NAME[M]         |   name                            |

    """
    RawMessage = TCP_DeviceHandshakeMessage

    idx_header = 0
    header = 0x7F
    idx_uid = 1
    idx_num_protocols = 5
    idx_protocols = 6

    offset_len_name = 6
    offset_name = 7
    protocol_overhead = 7

    protocol_identifier = 0x01

    base_protocol = TCP_Protocol

    def __init__(self):
        super().__init__()

    def decode(self, data):
        check = self.checkMessage(data)

        if not check:
            return None

        msg = self.RawMessage()
        msg.uid = list(data[self.idx_uid:self.idx_uid+4])
        num_protocols = data[self.idx_num_protocols]
        msg.protocols = list(data[self.idx_protocols:self.idx_protocols+num_protocols])
        len_name = data[self.offset_len_name+num_protocols]
        msg.name = (data[self.offset_name+num_protocols:self.offset_name+num_protocols+len_name]).decode("utf-8")
        return msg

    def encode(self, msg: RawMessage):
        buffer = [0] * (self.protocol_overhead + len(msg.protocols))
        buffer[self.idx_header] = self.header
        buffer[self.idx_uid] = msg.uid[0]
        buffer[self.idx_uid + 1] = msg.uid[1]
        buffer[self.idx_uid + 2] = msg.uid[2]
        buffer[self.idx_uid + 3] = msg.uid[3]
        buffer[self.idx_num_protocols] = len(msg.protocols)
        buffer[self.idx_protocols:self.idx_protocols + len(msg.protocols)] = msg.protocols
        buffer[self.offset_len_name + len(msg.protocols)] = len(msg.name)
        buffer[self.offset_name + len(msg.protocols):self.offset_len_name + len(msg.protocols) + len(msg.name)] = list(
            msg.name.encode("utf-8"))
        return buffer

    def checkMessage(self, data):
        if not data[self.idx_header] == self.header:
            return 0

        num_protocols = data[self.idx_num_protocols]
        len_name = data[self.offset_len_name + num_protocols]

        if not len(data) == num_protocols + len_name + self.protocol_overhead:
            return 0

        return 1


TCP_DeviceHandshakeProtocol = _TCP_DeviceHandshakeProtocol()
TCP_DeviceHandshakeMessage.protocol = TCP_DeviceHandshakeProtocol

