import logging
import time

from archive.cm4_core_old2.communication.serial.protocols.uart_protocol import UART_Message
from archive.cm4_core_old2.communication.serial.serial_device import Serial_Device

logging.basicConfig(
    format='%(asctime)s.%(msecs)03d  %(levelname)-8s  %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

uart: Serial_Device = None


def rx_callback(msg: UART_Message, *args, **kwargs):
    logging.info(f"Receive message with id {msg.msg} and cmd {msg.cmd} and payload {msg.data}")
    uart.send(msg)


def main():
    global uart
    uart = Serial_Device(device="/dev/ttyAMA1", baudrate=115200)
    uart.registerCallback('rx', rx_callback)
    uart.start()

    msg = UART_Message()
    msg.add = [6, 8]
    msg.cmd = 1
    msg.msg = 7
    msg.data = [1, 2, 3, 4, 5]

    # x = msg.encode()
    # x = bytearray(x)
    #
    # x[0] = 0x55
    # uart.sendRaw(x)

    uart.send(msg)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exit")
        uart.close()


if __name__ == '__main__':
    main()
