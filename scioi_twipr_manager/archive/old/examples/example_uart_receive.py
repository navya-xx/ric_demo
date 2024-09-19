import sys
import time

from archive import cm4_core_old2 as utils
from archive.cm4_core_old2.hardware import UART


def print_data(data):
    print(f"[UART][{utils.timestr()}] ({len(data)}) {utils.bytes_to_string(data, pos=False)}")


def main():
    uart = UART(dev='/dev/serial0', baudrate=115200, timeout=None, cobs_encode_rx=True, cobs_encode_tx=False,
                delimiter=b'\x00', data='bin')
    uart.registerCallback('rx', fun=print_data)
    uart.start()

    try:
        while 1:
            # uart.send([0xAA, 0xBB, 0x01, 0x01, 0x03, 0x02, 0x00, 0x01, 0x02, 0xCC])
            uart.send([1, 2, 3, 4, 5])
            time.sleep(1)
    except KeyboardInterrupt:
        uart.close()
        print("UART Closed!")
        sys.exit()


if __name__ == '__main__':
    main()
