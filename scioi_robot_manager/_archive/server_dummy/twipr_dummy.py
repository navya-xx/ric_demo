import copy
import threading
import time
import random

from device_manager.communication.connection import Connection
from device_manager.communication.protocols.protocol import Message
from device_manager.communication.protocols.tcp.tcp_json_protocol import TCP_JSON_Message
from device_manager.devices.robots.twipr.twipr import TWIPR
from device_manager.devices.robots.twipr.twipr_data import twipr_wifi_sample


class ConnectionDummy(Connection):
    registered: bool

    def send(self, message: Message):
        pass

    def registerCallback(self, callback_id, function, parameters: dict = None, lambdas: dict = None):
        pass

    def __init__(self):
        super().__init__()
        self.registered = False


class TWIPR_Dummy(TWIPR):
    _thread: threading.Thread

    def __init__(self):
        super().__init__(connection=ConnectionDummy())
        self._thread = threading.Thread(target=self._dummy_thread_function, daemon=True)
        self._thread.start()

    def _generateStreamMessage(self):
        msg = TCP_JSON_Message()

        data = copy.deepcopy(twipr_wifi_sample)
        msg.data = data
        msg.type = 'stream'

        self._rx_callback(msg)

    def _dummy_thread_function(self):
        time.sleep(random.uniform(0.01, 0.1))
        while True:
            if self.connection.registered:
                self._generateStreamMessage()
            time.sleep(1)
