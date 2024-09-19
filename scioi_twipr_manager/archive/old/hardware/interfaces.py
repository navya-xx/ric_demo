from queue import Queue
import serial
import os
# import cobs.cobs as cobs
import threading

from archive import cm4_core_old2 as utils


class UART:
    dev: str
    baudrate: int
    timeout: int
    device: serial.Serial

    rx_buffer: list

    # Consistent Overhead Byte Stuffing (# https://en.wikipedia.org/wiki/Consistent_Overhead_Byte_Stuffing)
    cobs_encode_rx: bool
    cobs_encode_tx: bool

    delimiter: bytes
    data: str  # 'bin' or 'ascii'

    rx_buffer_queue: Queue
    tx_buffer_queue: Queue

    rx_callback: utils.Callback

    _thread: threading.Thread
    shutdown: bool

    def __init__(self, dev: str, baudrate: int, timeout=0, cobs_encode_rx: bool = True,
                 cobs_encode_tx: bool = False, delimiter: bytes = b'\x00', data: str = 'bin'):
        self.dev = dev
        self.baudrate = baudrate
        self.timeout = timeout

        self.cobs_encode_rx = cobs_encode_rx
        self.cobs_encode_tx = cobs_encode_tx
        self.delimiter = delimiter
        self.data = data

        self.rx_buffer_queue = Queue()
        self.tx_buffer_queue = Queue()

        try:
            os.stat(dev)
        except OSError:
            raise Exception("UART Device does not exist!")

        self.device = serial.Serial(dev, baudrate=baudrate, timeout=timeout)

        self.shutdown = False
        self.rx_callback = None

    def start(self):
        try:
            self.device.open()
        except serial.SerialException:
            self.device.close()
            self.device.open()

        self._thread = threading.Thread(target=self.thread)
        self._thread.start()

    def registerCallback(self, callback_type, fun, **params):
        if callback_type == 'rx':
            self.rx_callback = utils.Callback(fun=fun, **params)

    def send(self, data):
        if self.device.writable():
            if self.cobs_encode_tx:
                # data = cobs.encode(data)
                pass
            self.device.write(data)  # TODO: Change this so that it will be written into a buffer

    def available(self):
        return self.device.inWaiting()

    def read(self, size: int = 1):
        return self.device.read(size)

    def close(self):
        self.shutdown = True
        self._thread.join()
        self.device.close()

    def thread(self):

        while not self.shutdown:
            if self.cobs_encode_rx and self.timeout is None:  # TODO: This is blocking, so the shutdown thing never really works!
                data = self.device.read_until(expected=self.delimiter)
                if len(data) > 0:  # TODO: Remove this magic number here
                    # data = cobs.decode(data[:-1])
                    self.rx_buffer_queue.put_nowait(data)
                    if self.rx_callback is not None:
                        self.rx_callback(data=data)


class SPI:
    def __init__(self):
        pass


class I2C:
    def __init__(self):
        pass
