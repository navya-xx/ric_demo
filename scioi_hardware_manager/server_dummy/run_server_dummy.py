import time

from hardware_manager.devices.robots.twipr.twipr import TWIPR
from server_dummy.server import HardwareManagerDummy
from server_dummy.twipr_dummy import TWIPR_Dummy


def callback_stream(message, device: TWIPR_Dummy):
    print(f"STREAM from {device.information.device_id}")


def device_connected_callback(device: TWIPR_Dummy):
    print(f"Device Connected: {device.information.device_id}")


def device_disconnected_callback(device: TWIPR_Dummy):
    print(f"Device disconnected: {device.information.device_id}")


def main():
    server = HardwareManagerDummy()
    server.registerCallback('new_device', device_connected_callback)
    server.registerCallback('device_disconnected', device_disconnected_callback)

    twipr1 = TWIPR_Dummy()
    twipr1.information.device_id = 'twipr1'
    twipr1.information.device_class = 'robot'
    twipr1.information.device_type = 'twipr'
    twipr1.information.name = 'TWIPR 1'
    twipr1.information.address = ''
    twipr1.information.revision = 3

    twipr1.registerCallback('stream', callback_stream)

    twipr2 = TWIPR_Dummy()
    twipr2.information.device_id = 'twipr2'
    twipr2.information.device_class = 'robot'
    twipr2.information.device_type = 'twipr'
    twipr2.information.name = 'TWIPR 2'
    twipr2.information.address = ''
    twipr2.information.revision = 3

    twipr2.registerCallback('stream', callback_stream)

    server.addNewDevice(twipr1)
    server.addNewDevice(twipr2)

    time.sleep(5)
    server.removeDevice('twipr2')
    time.sleep(2)
    server.addNewDevice(twipr2)

    while True:
        time.sleep(1)


if __name__ == '__main__':
    main()
