import time
import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from device_manager.devices.robots.twipr.twipr import TWIPR
from extensions.websockets.websocket_server import WebsocketClass
from server_dummy.server import HardwareManagerDummy
from server_dummy.twipr_dummy import TWIPR_Dummy
import threading
import random

ws_stream = None
ws_messages = None
stop_streaming = False


def callback_stream(message, device: TWIPR_Dummy):
    global ws_stream, stop_streaming
    # print(f"STREAM from {device.information.device_id}")
    # Convert message to JSON and send to the websocket
    if not stop_streaming:
        id = message.data["general"]["id"]

        message = message.data
        ws_stream.send(message)


def device_connected_callback(device: TWIPR_Dummy):
    global ws_messages
    print(f"Device Connected: {device.information.device_id}")
    message = {"event": "robot_connected", "device_id": device.information.device_id}
    ws_messages.send(message)
    # ws.send(msg)


def device_disconnected_callback(device: TWIPR_Dummy):
    global ws_messages
    print(f"Device disconnected: {device.information.device_id}")
    message = {"event": "robot_disconnected", "device_id": device.information.device_id}
    ws_messages.send(message)


"""
async def websocket_server():
    async with websockets.serve(register, "localhost", 8765):
        await asyncio.Future()  # Run forever
"""


def create_robots(max_number_of_robots=10):
    robots = []
    for i in range(max_number_of_robots):
        robot = TWIPR_Dummy()
        robot.device.information.device_id = f"twipr{i + 1}"
        robot.device.registerCallback('stream', callback_stream)
        robots.append(robot)
    return robots


def create_random_robot_connections(min_number_of_robots=1, max_number_of_robots=10):
    # create a list with either 0 or 1 randomly (lenght of list = max_number_of_robots)
    random_robot_connections = [random.choice([0, 1]) for i in range(max_number_of_robots)]
    while sum(random_robot_connections) < min_number_of_robots:
        random_robot_connections[random_robot_connections.index(0)] = 1
    return random_robot_connections


def connect_disconnect_robots(robots, old_robot_connections, new_robot_connections, server):
    for i in range(len(robots)):
        if old_robot_connections[i] == 0 and new_robot_connections[i] == 1:
            server.addNewDevice(robots[i].device)
        elif old_robot_connections[i] == 1 and new_robot_connections[i] == 0:
            server.removeDevice(robots[i].information.device_id)


def print_connected_robots(robots_connections):
    for i, con in enumerate(robots_connections):
        if con == 1:
            print("Robot {} is connected".format(i))


def run_robot_loop(server):
    max_number_of_robots = 10
    robots = create_robots(max_number_of_robots)
    old_robot_connections = [0] * max_number_of_robots
    new_robot_connections = create_random_robot_connections()
    time_to_change_robots = 30
    while True:
        connect_disconnect_robots(robots, old_robot_connections, new_robot_connections, server)
        old_robot_connections = new_robot_connections
        new_robot_connections = create_random_robot_connections()
        print(f"change robot connections:")
        print_connected_robots(new_robot_connections)
        print("--------------------")
        time.sleep(time_to_change_robots)


def ws_callback(message):
    global stop_streaming
    data = json.loads(message)
    message_type = data.get('type')

    if message_type == 'command' and data.get('command') == 'emergency':
        stop_streaming = True
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


def set_control_mode(bot_id, key, value):
    # Dummy function to set control mode, replace with actual implementation
    print(f"Control mode for {bot_id} set to {value}")


def main():
    global ws_stream
    global ws_messages
    server = HardwareManagerDummy()
    server.registerCallback('new_device', device_connected_callback)
    server.registerCallback('device_disconnected', device_disconnected_callback)
    ws_stream = WebsocketClass('localhost', 8765, start=True)
    ws_messages = WebsocketClass('localhost', 8766, start=True)
    ws_messages.set_message_callback(ws_callback)
    run_robot_loop(server)


if __name__ == '__main__':
    main()
