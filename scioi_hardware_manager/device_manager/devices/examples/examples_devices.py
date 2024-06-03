import logging
import time

from device_manager.device_manager import DeviceManager
from device_manager.devices.device import Device

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
    d.command()


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
