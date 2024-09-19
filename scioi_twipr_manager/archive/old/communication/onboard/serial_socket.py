import queue
import dataclasses
import threading

import archive.cm4_core_old2.hardware.interfaces as interfaces


@dataclasses.dataclass
class SerialProtocol:
    """
    Byte    |   Description |   Default Value
    0       |   HEADER_0    |   0xAA
    1       |   HEADER_1    |   0xBB
    2       |   ID_0        |   -
    3       |   ID_1        |   -
    4       |   ID_2        |   -
    5       |   LEN         |   -
    6       |   CRC8        |   -
    7       |   DATA[0]     |   -
    8       |   DATA[1]     |   -
    ...     |   ...         |   ...
    N+6     |   DATA[N]     |   -
    N+7     |   FOOTER      |   0xCC
    """

    header: list = dataclasses.field(default_factory=lambda: [0xAA, 0xBB])
    footer: int = 0xCC
    footer_offset: int = 7
    id0_pos: int = 2
    id0_values: list = dataclasses.field(default_factory=lambda: [0x01, 0x02, 0x03, 0x04, 0x05, 0x06])
    id1_pos: int = 3
    id1_values: list = dataclasses.field(default_factory=lambda: [0x01, 0x02, 0x03, 0x04, 0x05])
    id2_pos: int = 4
    len_pos: int = 5
    crc8_pos: int = 6


class SerialSocket:
    UART: interfaces.UART
    protocol: SerialProtocol

    socket_type: str

    rx_thread: threading.Thread
    shutdown: bool

    rx_queue: queue.Queue
    tx_queue: queue.Queue

    def __init__(self, dev: str, baudrate: int, socket_type: str):

        self.socket_type = socket_type

        if self.socket_type == "bin":
            self.UART = interfaces.UART(dev=dev, baudrate=baudrate, cobs_encode_rx=True, cobs_encode_tx=False,
                                        timeout=None, delimiter=b'\x00')
        else:
            raise Exception("Not implemented yet")

        self.protocol = SerialProtocol()
        self.shutdown = False

    def start(self):
        self.UART.start()
        # self.rx_thread = threading.Thread(target=self.rx_thread_fun)

    def send(self, data):
        pass

    def sendMessage(self, msg):
        pass

    def close(self):
        self.UART.close()

    def rx_thread_fun(self):
        pass
