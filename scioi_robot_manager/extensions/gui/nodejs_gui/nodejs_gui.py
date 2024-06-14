import json
import os
import subprocess
import threading
import time
import signal

from core.utils.callbacks import Callback
from extensions.websockets.websocket_server import WebsocketClass

frontend_dir = f"{os.path.dirname(__file__)}/frontend/"


class NodeJSGui:
    websocket_stream: WebsocketClass
    websocket_messages: WebsocketClass

    _frontend_thread: threading.Thread
    client_connected: bool

    callbacks: dict

    def __init__(self):
        self.websocket_stream = WebsocketClass('localhost', 8765, start=True)
        self.websocket_messages = WebsocketClass('localhost', 8766, start=True)

        self.websocket_messages.set_message_callback(self._rxMessage_callback)
        self.websocket_messages.set_connection_callback(self._websocketClientConnected_callback)

        self.frontend_process = None

        signal.signal(signal.SIGINT, self.close)

        self.client_connected = False

        self.callbacks = {
            'websocket_client_connected': [],
            'rx_message': [],
        }

    # ------------------------------------------------------------------------------------------------------------------
    def init(self):
        ...

    # ------------------------------------------------------------------------------------------------------------------
    def start(self):
        self._run_frontend()

    # ------------------------------------------------------------------------------------------------------------------
    def close(self, *args, **kwargs):
        self.frontend_process.terminate()

    # ------------------------------------------------------------------------------------------------------------------
    def registerCallback(self, callback_id, function, parameters: dict = None, lambdas: dict = None):
        """

        :param callback_id:
        :param function:
        :param parameters:
        :param lambdas:
        """
        callback = Callback(function, parameters, lambdas)
        if callback_id in self.callbacks:
            self.callbacks[callback_id].append(callback)
        else:
            raise Exception("Invalid Callback type")

    # ------------------------------------------------------------------------------------------------------------------
    def sendMessage(self, message_type, data):
        message = {"timestamp": time.time(), "type": message_type, "data": data}
        self.websocket_messages.send(message)

    # ------------------------------------------------------------------------------------------------------------------
    def sendEvent(self, event, device_id):
        message = {"timestamp": time.time(), "event": event, device_id: device_id}
        self.websocket_messages.send(message)

    # ------------------------------------------------------------------------------------------------------------------
    def print(self, message):
        self.sendMessage(message_type="message", data=message)
    # ------------------------------------------------------------------------------------------------------------------

    def sendStream(self, data):
        self.websocket_stream.send(data)

    # ------------------------------------------------------------------------------------------------------------------
    def install(self):
        os.chdir(frontend_dir)
        os.system("npm install")

    # === PRIVATE METHODS ==============================================================================================
    def _rxMessage_callback(self, message, *args, **kwargs):
        print("fdhsfhdj")
        message = json.loads(message)
        for callback in self.callbacks['rx_message']:
            callback(message, *args, **kwargs)

    # ------------------------------------------------------------------------------------------------------------------
    def _websocketClientConnected_callback(self, *args, **kwargs):
        self.client_connected = True
        for callback in self.callbacks['websocket_client_connected']:
            callback(*args, **kwargs)

    # ------------------------------------------------------------------------------------------------------------------
    def _run_frontend(self):
        os.chdir(frontend_dir)
        # os.system("npm run dev -- --open")
        # os.system("npm install")
        # print(frontend_dir)
        # subprocess.run("npm run dev -- --open", shell=True, cwd=frontend_dir)
        self.frontend_process = subprocess.Popen("npm run dev -- --open", shell=True)
        # self.frontend_process = subprocess.run(["npm", "run", "dev", "--", "--open"], cwd=frontend_dir)
