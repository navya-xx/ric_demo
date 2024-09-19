import random
import time

import board


def main():
    i2c = board.I2C()

    device_address = 0x02
    memory_address = 0x00
    data = []
    data_len = 10
    for i in range(0, data_len):
        data.append(random.randint(0, 255))

    buffer_out = bytearray([memory_address]) + bytearray(data)
    i2c.writeto(device_address, buffer_out)
    time.sleep(1)

    data_read = bytearray([0] * data_len)
    i2c.writeto_then_readfrom(device_address, buffer_out=bytes([memory_address]), buffer_in=data_read)
    data_read = list(data_read)

    if data == data_read:
        print("Success")
    else:
        print("Fail")
    print(data)
    print(data_read)
    time.sleep(1)
    i2c.deinit()


if __name__ == '__main__':
    main()
