import copy
import threading
import time
import random
import sys
import os

from device_manager.devices.device import Device

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from device_manager.communication.connection import Connection
from device_manager.communication.protocols.protocol import Message
from device_manager.communication.protocols.tcp.tcp_json_protocol import TCP_JSON_Message
from device_manager.devices.robots.twipr.twipr import TWIPR
# from hardware_manager.devices.robots.twipr.twipr_data import twipr_wifi_sample
from device_manager.devices.robots.twipr.twipr_data import twipr_wifi_sample, get_twipr_wifi_sample
import numpy as np

mapsize = [3, 3]


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
        super().__init__(device=Device(connection=ConnectionDummy()))
        self._thread = threading.Thread(target=self._dummy_thread_function, daemon=True)
        self._thread.start()

    def _generateStreamMessage(self, i=0, positional_offset=[0, 0], radius=0.5):
        msg = TCP_JSON_Message()
        # data = copy.deepcopy(twipr_wifi_sample)
        name = self.device.information.device_id
        id = self.device.information.device_id
        data = get_twipr_wifi_sample(i, name, id, 0.005, radius)
        data['estimation']['state']['x'] += positional_offset[0]
        data['estimation']['state']['y'] += positional_offset[1]
        # cap the x and y values to 0 and mapsize[0] and mapsize[1]
        data['estimation']['state']['x'] = max(0, min(data['estimation']['state']['x'], mapsize[0]))
        data['estimation']['state']['y'] = max(0, min(data['estimation']['state']['y'], mapsize[1]))
        msg.data = data
        msg.type = 'stream'

        self.device._rx_callback(msg)

    def _dummy_thread_function(self):
        time.sleep(random.uniform(0.01, 0.1))
        i = 0
        positional_offset = np.random.uniform(low=0, high=min(mapsize), size=(2,)).tolist()
        radius = random.uniform(0.2, 1)
        while True:
            if self.device.connection.registered:
                self._generateStreamMessage(i, positional_offset, radius)
                i += 1
            else:
                i = 0
                positional_offset = np.random.uniform(low=-5, high=5, size=(2,)).tolist()
                radius = random.uniform(0.75, 3)
            time.sleep(0.1)
