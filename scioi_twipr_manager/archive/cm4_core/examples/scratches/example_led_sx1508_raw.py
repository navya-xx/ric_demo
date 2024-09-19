import time
import board
import busio

"""
This example shows how to use the SX1508 to turn on the on-board LED S3
"""


def main():
    i2c = board.I2C()

    i2c.writeto(address=0x20, buffer=b'\x00\x08')
    i2c.writeto(address=0x20, buffer=b'\x03\x00')
    i2c.writeto(address=0x20, buffer=b'\x04\x00')
    i2c.writeto(address=0x20, buffer=b'\x07\xF7')
    i2c.writeto(address=0x20, buffer=b'\x08\x00')

    for i in range(0, 10):
        i2c.writeto(address=0x20, buffer=b'\x08\x08')
        time.sleep(0.25)
        i2c.writeto(address=0x20, buffer=b'\x08\x00')
        time.sleep(0.25)


if __name__ == '__main__':
    main()
