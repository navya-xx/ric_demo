import logging

from archive.cm4_core_old2.communication.wifi.protocols.tcp_json_protocol import TCP_JSONProtocol, TCP_JSONMessage
from archive.cm4_core_old2.communication.wifi.tcp_device import TCP_Device

logging.basicConfig(
    format='%(asctime)s.%(msecs)03d  %(levelname)-8s  %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

registered = False

msg = TCP_JSONMessage()
msg.data = {'answer': 3}


def receive_callback(device, message, *args, **kwargs):
    device.send(message)


def register_callback(device, *args, **kwargs):
    global registered
    registered = True


def main():
    device = TCP_Device(protocols={'json': TCP_JSONProtocol}, uid=[1, 2, 3, 4], name='device01')
    device.registerCallback('rx', receive_callback)
    device.registerCallback('registered', register_callback)
    device.start()

    while not registered:
        pass


if __name__ == "__main__":
    main()
