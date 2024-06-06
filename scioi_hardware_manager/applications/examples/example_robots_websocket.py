import asyncio
import json
import threading
import time

import numpy as np

from applications.robot_manager import RobotManager
from device_manager.devices.robots.twipr.twipr import TWIPR
from extensions.joystick.joystick_manager import Joystick
from extensions.websockets.websocket_server import WebsocketClass

ws_stream = None
ws_messages = None


def stream_callback(stream, device, *args, **kwargs):
    if ws_stream is not None:
        ws_stream.send(stream.data)


def new_robot(robot, *args, **kwargs):
    global ws_messages
    print(f"New Robot connected ({robot.device.information.device_name})")
    message = {"event": "robot_connected", "device_id": robot.device.information.device_id}
    ws_messages.send(message)


def robot_disconnected(robot, *args, **kwargs):
    global ws_messages
    print(f"Robot disconnected ({robot.device.information.device_name})")
    message = {"event": "robot_disconnected", "device_id": robot.device.information.device_id}
    ws_messages.send(message)


def ws_callback(message):
    global stop_streaming
    data = json.loads(message)
    message_type = data.get('type')

    if message_type == 'command' and data.get('command') == 'emergency':
        stop_streaming = False
        timestamp = data.get('timestamp')
        print(f"Emergency command received at {timestamp}")

    elif message_type == 'assignController':
        bot_id = data.get('botId')
        controller_id = data.get('controllerId')
        timestamp = data.get('timestamp')
        print(f"Assigning controller {controller_id} to bot {bot_id} at {timestamp}")

    elif message_type == 'set':
        bot_id = data.get('botId')
        key = data.get('key')
        value = data.get('value')
        timestamp = data.get('timestamp')
        print(f"Setting {key} to {value} for bot {bot_id} at {timestamp}")
        # Set the control mode for the bot
        set_control_mode(bot_id, key, value)

    else:
        print(f"Unknown message type: {message_type}")

def set_initial_values():
    joysticks = [{
                "id": "3240234234324324",
                "name": "controller1",
                "assignedBot": "twipr1",
            },
            {
                "id": "32402334234324324",
                "name": "controller2",
                "assignedBot": "twipr2",
            },
            {
                "id": "32402234234324324",
                "name": "controller3",
                "assignedBot": "twipr3",
            },
            {
                "id": "3240112334234324324",
                "name": "controller4",
                "assignedBot": "twipr4",
            }
            ]
    message = { "timestamp" : time.time(), "type" : "joysticksChanged", "payload": {"joysticks" : joysticks}  }
    ws_messages.send(message)


def main():
    global ws_stream
    global ws_messages

    manager = RobotManager()
    manager.init()
    manager.start()

    ws_stream = WebsocketClass('localhost', 8765, start=True)
    ws_messages = WebsocketClass('localhost', 8766, start=True)
    ws_messages.set_message_callback(ws_callback)
    manager.registerCallback('stream', stream_callback)
    manager.registerCallback('new_robot', new_robot)

    set_initial_values()

    while True:
        time.sleep(0.1)


if __name__ == '__main__':
    main()
