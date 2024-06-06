import time
import json
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from hardware_manager.devices.robots.twipr.twipr import TWIPR
from server_dummy.server import HardwareManagerDummy
from server_dummy.twipr_dummy import TWIPR_Dummy
import threading
import random
import asyncio
import websockets
import numpy as np

buffer = {}


def callback_stream(message, device: TWIPR_Dummy):
    global buffer
    #print(f"STREAM from {device.information.device_id}")
    # check if the device_id is already in the buffer
    if device.information.device_id in buffer:
        # if the device_id is already in the buffer, append the new message to the buffer
        buffer[device.information.device_id].append(message.data)
    else:
        # if the device_id is not in the buffer, create a new list with the message as first element
        buffer[device.information.device_id] = [message.data]


def device_connected_callback(device: TWIPR_Dummy):
    print(f"Device Connected: {device.information.device_id}")


def device_disconnected_callback(device: TWIPR_Dummy):
    print(f"Device disconnected: {device.information.device_id}")

def create_robots(max_number_of_robots = 10):
    robots = []
    for i in range(max_number_of_robots):
        robot = TWIPR_Dummy()
        robot.information.device_id = f"twipr{i+1}"
        robot.registerCallback('stream', callback_stream)
        robots.append(robot)
    return robots

def create_random_robot_connections(min_number_of_robots = 1, max_number_of_robots = 10):
    # create a list with either 0 or 1 randomly (lenght of list = max_number_of_robots)
    random_robot_connections = [random.choice([0, 1]) for i in range(max_number_of_robots)]
    while sum(random_robot_connections) < min_number_of_robots:
        random_robot_connections[random_robot_connections.index(0)] = 1
    return random_robot_connections

def connect_disconnect_robots(robots, old_robot_connections, new_robot_connections, server):
    for i in range(len(robots)):
        if old_robot_connections[i] == 0 and new_robot_connections[i] == 1:
            server.addNewDevice(robots[i])
        elif old_robot_connections[i] == 1 and new_robot_connections[i] == 0:
            server.removeDevice(robots[i].information.device_id)

def print_connected_robots(robots_connections):
    for i,con in enumerate(robots_connections):
        if con == 1:
            print("Robot {} is connected".format(i))

async def send_buffer(websocket, path):
    global buffer
    # send the buffer to the websocket
    print("Sending buffer to websocket")
    while True:
        json_data = json.dumps(buffer)
        #print(json_data)
        await websocket.send(json_data)
        await asyncio.sleep(0)
        for key in buffer:
            buffer[key] = []
        #print(f"Sent data: {json_data}")
        await asyncio.sleep(0.1)  # Adjusted sleep time for 10 Hz frequency

def run_robot_loop(server):
    max_number_of_robots = 10
    robots = create_robots(max_number_of_robots)
    old_robot_connections = [0]*max_number_of_robots
    new_robot_connections = create_random_robot_connections()
    time_to_change_robots = 200
    while True:
        connect_disconnect_robots(robots, old_robot_connections, new_robot_connections,server)
        old_robot_connections = new_robot_connections
        new_robot_connections = create_random_robot_connections()
        #print(f"change robot connections:")
        #print_connected_robots(new_robot_connections)
        #print("--------------------")
        time.sleep(time_to_change_robots)
async def main():
    server = HardwareManagerDummy()
    server.registerCallback('new_device', device_connected_callback)
    server.registerCallback('device_disconnected', device_disconnected_callback)

    robot_loop = threading.Thread(target=run_robot_loop, args=(server,))
    robot_loop.start()
    servertest = await websockets.serve(send_buffer, 'localhost', 8765)
    await servertest.wait_closed()


if __name__ == '__main__':
    asyncio.run(main())