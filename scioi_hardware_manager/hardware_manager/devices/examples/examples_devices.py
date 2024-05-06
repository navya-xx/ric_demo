import logging
import time

from hardware_manager.devices.device_manager import DeviceManager
from hardware_manager.devices.device import Device
from hardware_manager.communication.protocols.tcp.tcp_json_protocol import TCP_JSON_Message, TCP_JSON_Protocol

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(name)-8s %(message)s',
    level=logging.INFO,
    datefmt='%H:%M:%S')

device_connected = False
d: Device = None


def new_device(device: Device):
    global device_connected
    global d
    device_connected = True
    d = device
    d.registerCallback('stream', stream_callback)


def stream_callback(message, *args, **kwargs):
    print(message.data)


def device_disconnected():
    ...


def main():
    manager = DeviceManager()
    manager.start()

    manager.registerCallback('new_device', new_device)
    while True:
        if device_connected:
            ...

        time.sleep(0.25)


if __name__ == '__main__':
    main()
