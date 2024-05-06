import dataclasses
import logging
import queue
import socket
import threading
import time
from cobs import cobs

logger = logging.getLogger('udp')
logger.setLevel('INFO')


########################################################################################################################
@dataclasses.dataclass
class UDP_Message:
    data: bytes = None
    address: str = None
    port: int = None


########################################################################################################################
@dataclasses.dataclass
class UDP_Broadcast:
    data: bytes = ''
    address: str = '<broadcast>'
    port: int = 37020
    time: float = 1
    _last_sent: float = 0


########################################################################################################################
class UDP_Server:
    """

    """
    server: socket.socket
    address: str
    port: int
    _thread: threading.Thread

    config: dict
    _exit: bool

    broadcasts: list[UDP_Broadcast]

    _rx_queue: queue.Queue
    _tx_queue: queue.Queue

    _thread_timeout = 0.001

    # === INIT =========================================================================================================
    def __init__(self, address, port: int = 44444, config: dict = None):
        """
        """

        self.address = address
        self.port = port

        if config is None:
            config = {}

        default_config = {
            'cobs': False
        }

        self.config = {**default_config, **config}

        self._tx_queue = queue.Queue()
        self.broadcasts = []

        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # Set a timeout so the socket does not block
        # indefinitely when trying to receive data.
        self.server.settimeout(0)

        # set ip and port
        self.server.bind((str(self.address), self.port))

        self._exit = False

    # === METHODS ======================================================================================================
    def start(self):
        logger.info(f"Starting UDP host on {self.address}:{self.port}")
        self._thread = threading.Thread(target=self._thread_fun)
        self._thread.start()

    # ------------------------------------------------------------------------------------------------------------------
    def addBroadcast(self, broadcast: UDP_Broadcast):
        self.broadcasts.append(broadcast)
        logger.debug(f"Added UDP Broadcast to {broadcast.address}:{broadcast.port}. Time={broadcast.time}s")

    # ------------------------------------------------------------------------------------------------------------------
    def send(self, data, address: str = '<broadcast>', port: int = 37020):

        msg = UDP_Message()

        if isinstance(data, list):
            data = bytes(data)
        if isinstance(data, str):
            data = data.encode('utf-8')

        if self.config['cobs']:
            data = cobs.encode(data)
            data = data + b'\x00'

        msg.data = data
        msg.address = address
        msg.port = port

        self._tx_queue.put_nowait(msg)

    # ------------------------------------------------------------------------------------------------------------------
    def close(self):
        """

        :return:
        """
        self._exit = True
        self._thread.join()

    # ------------------------------------------------------------------------------------------------------------------
    def _thread_fun(self):
        while not self._exit:

            # Check if there is something in the tx_queue. If so, send it
            while self._tx_queue.qsize() > 0:
                msg = self._tx_queue.get_nowait()
                self.server.sendto(msg.data, (msg.address, msg.port))

            # Go through the active broadcasts and see if one of them has to be sent
            for broadcast in self.broadcasts:
                if time.time() > broadcast._last_sent + broadcast.time:
                    broadcast._last_sent = time.time()
                    self.send(broadcast.data, broadcast.address, broadcast.port)

            # Check if there is something in RX

            try:
                data, addr = self.server.recvfrom(1028)
                if len(data) > 0:
                    logger.info(f"UDP: Received {data} from {addr}")
            except BlockingIOError:
                pass

            time.sleep(self._thread_timeout)

        logger.info(f"Closing UDP Server on {self.address}: {self.port}")
