import asyncio
import json
import time

import websockets

from applications.ideenexpo.src.twipr_manager import TWIPR_Manager
from device_manager.devices.robots.twipr.twipr import TWIPR
from extensions.joystick.joystick_manager import Joystick
from socketify import OpCode

time_last = time.time()


def streamCallback(stream, device, *args, **kwargs):
    ...

    # print(f"Time Diff: {time.time() - stream.data['general']['time']}")
    # print(f"My time: {time.time()}, Device time: {stream.data['general']['time']}")
    # teleplot.sendValue('theta', stream.data['estimation']['state']['theta'])
    # teleplot.sendValue('mode', stream.data['control']['mode'])


def test(joystick, button, input_string, *args, **kwargs):
    print(input_string)


def ws_open(ws):
    print('A WebSocket got connected!')
    ws.send("Hello World!", OpCode.TEXT)


def ws_message(ws, message, opcode):
    # Ok is false if backpressure was built up, wait for drain
    ok = ws.send(message, opcode)


def robot_manager_example_1():
    max_forward_torque_cmd = 0.10
    max_turning_torque_cmd = 0.15
    robot: TWIPR = None
    joystick: Joystick = None

    manager = TWIPR_Manager()
    manager.init()
    manager.start()

    def new_robot_callback(new_robot, *args, **kwargs):
        nonlocal robot
        print(f"Detected Robot with id {new_robot.device.information.device_id}")
        if new_robot.device.information.device_id == 'twipr1':
            print("Detected Wanted Robot")
            robot = new_robot

    def setControlMode(joystick, button, mode):
        nonlocal robot
        if robot is not None:
            print(f"Setting Control mode to {mode}")
            robot.setControlMode(mode)

    def new_joystick_callback(new_joystick, *args, **kwargs):
        nonlocal joystick
        joystick = new_joystick
        print("New Joystick")

    # manager.deviceManager.registerCallback('stream', streamCallback)
    manager.registerCallback('new_joystick', new_joystick_callback)
    manager.registerCallback('new_robot', new_robot_callback)
    manager.registerCallback('stream', streamCallback)

    while True:
        if robot is not None and joystick is not None:
            if joystick.uuid not in manager.joystick_assignments.keys():
                manager.assignJoystick(robot, joystick)
            else:
                val1 = joystick.axis[1] * (max_forward_torque_cmd)
                val2 = joystick.axis[2] * max_turning_torque_cmd
                if robot.device.connection.connected:
                    robot.setInput([val1 + val2, val1 - val2])
        time.sleep(0.1)


buffer = {}


def stream_callback(stream, device, *args, **kwargs):
    global buffer
    #print(f"STREAM from {device.information.device_id}")
    # check if the device_id is already in the buffer
    if device.information.device_id in buffer:
        # if the device_id is already in the buffer, append the new message to the buffer
        buffer[device.information.device_id].append(stream.data)
    else:
        # if the device_id is not in the buffer, create a new list with the message as first element
        buffer[device.information.device_id] = [stream.data]

async def send_buffer(websocket, path):
    global buffer
    # send the buffer to the websocket
    print("Sending buffer to websocket")
    while True:
        json_data = json.dumps(buffer)
        # print(json_data)
        await websocket.send(json_data)
        await asyncio.sleep(0)
        for key in buffer:
            buffer[key] = []
        # print(f"Sent data: {json_data}")
        await asyncio.sleep(0.1)  # Adjusted sleep time for 10 Hz frequency


async def main():
    hardware_manager = TWIPR_Manager()
    hardware_manager.init()
    hardware_manager.start()

    hardware_manager.registerCallback('stream', stream_callback)
    servertest = await websockets.serve(send_buffer, 'localhost', 8765)
    await servertest.wait_closed()


if __name__ == '__main__':
    # asyncio.run(main())
    robot_manager_example_1()
