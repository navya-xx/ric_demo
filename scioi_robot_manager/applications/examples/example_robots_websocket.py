import json
import time

from applications.ideenexpo.src.twipr_manager import TWIPR_Manager
from extensions.websockets.websocket_server import WebsocketClass

ws_stream = None
ws_messages = None
manager = None

controlModeDict = {"off": 0, "direct": 1, "balancing": 2, "speed": 3}
joysticks = []


def stream_callback(stream, device, *args, **kwargs):
    if ws_stream is not None:
        ws_stream.send(stream)


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
    global manager, controlModeDict
    data = json.loads(message)
    message_type = data.get('type')

    if message_type == 'command' and data.get('data').get('command') == 'emergency':
        timestamp = data.get('timestamp')
        # emergency command at hardwaremanager
        manager.emergencyStop()
        print(f"Emergency command received at {timestamp}")


    elif message_type == 'joysticksChanged':
        joysticks = data.get('data').get('joysticks')
        for joystrick in joysticks:
            controller_id = joystrick.get('id')
            bot_id = joystrick.get('assignedBot')
            if bot_id == "":
                # check if the controller is assigned to a bot
                if controller_id in manager.joystick_assignments.keys():
                    manager.unassignJoystick(controller_id)
                    print(f"Unassigning controller {controller_id}")
            else:
                if controller_id in manager.joystick_assignments.keys():
                    connected_bot_id = manager.joystick_assignments[controller_id]['robot'].device.information.device_id
                    if connected_bot_id == bot_id:
                        pass
                    else:
                        manager.assignJoystick(bot_id, controller_id)
                else:
                    manager.assignJoystick(bot_id, controller_id)
                    # check to what bot the controller is assigned
            timestamp = data.get('timestamp')
            # Assign the controller to the bot with hardware manager
            print(f"Assigning controller {controller_id} to bot {bot_id} at {timestamp}")

    elif message_type == 'set':
        bot_id = data.get('botId')
        key = data.get('data').get('key')
        value = data.get('data').get('value')
        timestamp = data.get('timestamp')
        print(f"Setting {key} to {value} for bot {bot_id} at {timestamp}")
        # Set the control mode for the bot using hardware manager
        modeId = controlModeDict.get(value)
        manager.setRobotControlMode(bot_id, modeId)

    else:
        print(f"Unknown message type: {message_type}")


def ws_connection_callback(*args, **kwargs):
    global ws_messages
    print("ZZZZ")
    message = {"timestamp": time.time(), "type": "joysticksChanged", "data": {"joysticks": joysticks}}
    ws_messages.send(message)


def set_initial_values():
    global joysticks
    message = {"timestamp": time.time(), "type": "joysticksChanged", "data": {"joysticks": joysticks}}
    ws_messages.send(message)


def new_joystick(joystick, *args, **kwargs):
    global joysticks, ws_messages
    id = joystick.uuid
    name = joystick.name
    # check if the joystick is already in the dict if not add
    for j in joysticks:
        if j.get('id') == id:
            return
    joy = {"id": id, "name": name, "assignedBot": ""}
    joysticks.append(joy)
    message = {"timestamp": time.time(), "type": "joysticksChanged", "data": {"joysticks": joysticks}}
    ws_messages.send(message)
    print(joysticks)


def joystick_disconnected(joystick, *args, **kwargs):
    print("YYYY")
    global joysticks, ws_messages
    id = joystick.uuid
    # check if the joystick is in the dict if yes remove
    for j in joysticks:
        if j.get('id') == id:
            joysticks.remove(j)
            message = {"timestamp": time.time(), "type": "joysticksChanged", "data": {"joysticks": joysticks}}
            ws_messages.send(message)
            # send the joysticks to the ws
            break
    pass


def main():
    global ws_stream, ws_messages, manager

    manager = TWIPR_Manager()

    ws_stream = WebsocketClass('localhost', 8765, start=True)
    ws_messages = WebsocketClass('localhost', 8766, start=True)
    ws_messages.set_message_callback(ws_callback)
    ws_messages.set_connection_callback(ws_connection_callback)
    manager.registerCallback('stream', stream_callback)
    manager.registerCallback('new_robot', new_robot)
    manager.registerCallback('new_joystick', new_joystick)
    manager.registerCallback('joystick_disconnected', joystick_disconnected)

    manager.init()
    manager.start()

    set_initial_values()

    while True:
        time.sleep(0.1)


if __name__ == '__main__':
    main()
