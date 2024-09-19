import logging
import time

from archive.cm4_core_old2.communication.serial.core.serial_socket import UART_Socket

logging.basicConfig(
    format='%(asctime)s.%(msecs)03d  %(levelname)-8s  %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')


def rx_callback(data, *args, **kwargs):
    logging.info("Received something")


def main():
    uart = UART_Socket(device="/dev/ttyAMA1", baudrate=115200)
    uart.registerCallback('rx', rx_callback)
    uart.start()

    try:
        while True:
            data = bytes([1, 2, 3, 4, 5])

            uart.send(data)
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exit")
        uart.close()


if __name__ == '__main__':
    main()
