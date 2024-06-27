import asyncio
import json
import logging
import os
import threading
import time

import qmt
import queue
import sys

# ======================================================================================================================
babylon_path = f"{os.path.dirname(__file__)}/babylon_lib/"


# ======================================================================================================================
class BabylonVisualization:
    webapp_path: str

    _webapp: qmt.Webapp
    _webappProcess: None

    _last_sample: dict

    _config: dict
    _run: bool
    _show: str
    Ts = 0.05  # 0.04

    loaded: bool

    _tx_queue: queue.Queue
    _thread: threading.Thread

    # === INIT =========================================================================================================
    def __init__(self, webapp: str = babylon_path + '/pysim_env.html', webapp_config=None,
                 world_config=None, object_mappings = babylon_path + 'object_config.json', show: str = 'chromium'):

        self._config = {
            'objects': {},
            'world': {},
            'object_mappings': {},
            'webapp': {}
        }

        # Load the object configuration, which stores the information which Babylon Object needs to be created for a
        # certain class
        if isinstance(object_mappings, str):
            with open(object_mappings) as f:
                object_mappings = json.load(f)

        assert (isinstance(object_mappings, dict))
        self._config['object_mappings'] = object_mappings

        # World config: Describes the world and all the objects within the world
        if world_config is None:
            world_config = {}
        self._config['world'] = world_config

        # General config
        if webapp_config is None:
            webapp_config = {}
        self._config['webapp'] = webapp_config

        if webapp is not None:
            self.webapp_path = webapp

        assert (hasattr(self, 'webapp_path') and self.webapp_path is not None)

        self._last_sample = {}
        self._run = False
        self._tx_queue = queue.Queue()
        self._webapp = None
        self._show = show
        self.loaded = False

    # ------------------------------------------------------------------------------------------------------------------
    def init(self):
        ...

    # ------------------------------------------------------------------------------------------------------------------
    def start(self):
        logging.info("Starting Babylon visualization")
        self._thread = threading.Thread(target=self._threadFunction, daemon=False)
        self._thread.start()

    # ------------------------------------------------------------------------------------------------------------------
    def addObject(self, object_id: str, object_class: str, object_config: dict):
        data = {
            'type': 'addObject',
            'data': {
                'id': object_id,
                'class': object_class,
                'config': object_config
            }
        }
        self.sendData(data)

    # ------------------------------------------------------------------------------------------------------------------
    def removeObject(self, object_id):
        data = {
            'type': 'removeObject',
            'data': {
                'id': object_id,
            }
        }
        self.sendData(data)

    # ------------------------------------------------------------------------------------------------------------------
    def updateObject(self, object_id, data: dict):
        data = {
            'type': 'update',
            'data': {
                'id': object_id,
                'data': data
            }
        }
        self.sendData(data)

    # ------------------------------------------------------------------------------------------------------------------
    def set(self, object_id, parameter, value):
        data = {
            'type': 'set',
            'data': {
                'id': object_id,
                'parameter': parameter,
                'value': value
            }
        }
        self.sendData(data)

    # ------------------------------------------------------------------------------------------------------------------
    def get(self, object_id, parameter):
        ...

    # ------------------------------------------------------------------------------------------------------------------
    def function(self, object_id, function_name, arguments: list):
        data = {
            'type': 'function',
            'data': {
                'id': object_id,
                'function': function_name,
                'arguments': arguments
            }
        }
        self.sendData(data)

    # ------------------------------------------------------------------------------------------------------------------
    def sendSample(self, sample_dict: dict):
        data = {
            'type': 'sample',
            'data': sample_dict
        }
        self.sendData(data)

    # ------------------------------------------------------------------------------------------------------------------
    def sendData(self, data):
        self._tx_queue.put(data)

    # ------------------------------------------------------------------------------------------------------------------
    def setWorldConfig(self, world_config):
        self._config['world'] = world_config

    # === PRIVATE METHODS ==============================================================================================
    def _sendTxQueue(self):
        if not self.loaded:
            return
        len_tx_queue = self._tx_queue.qsize()
        for i in range(len_tx_queue):
            data = self._tx_queue.get()
            self._sendData(data)

    # ------------------------------------------------------------------------------------------------------------------

    def _sendData(self, data):
        if self._webappProcess is not None:
            try:
                self._webappProcess.sendSample(data)
            except Exception as e:
                print("Webapp not reachable")
                exit()

    # ------------------------------------------------------------------------------------------------------------------
    def _pollEvents(self):
        try:
            params = self._webappProcess.getParams(clear=True)
        except Exception as e:
            return

        if len(params) > 0:
            self._checkEvents(params)

    # ------------------------------------------------------------------------------------------------------------------
    def _checkEvents(self, params: dict = None):
        if 'loaded' in params.keys():
            print("Webapp loaded")
            self.loaded = True

    # ------------------------------------------------------------------------------------------------------------------
    def _threadFunction(self):
        # Define a new event loop, otherwise it's not working
        asyncio.set_event_loop(asyncio.new_event_loop())
        self._webapp = qmt.Webapp(self.webapp_path, config=self._config, show=self._show)
        self._webappProcess = self._webapp.runInProcess()

        while True:
            self._sendTxQueue()
            self._pollEvents()
            time.sleep(0.01)
