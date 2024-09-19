import time

import board


def main():
    i2c = board.I2C()

    g031_address = 0x50

    jj = range(0, 100)

    for k in range(0, 10):
        for i in range(0, 16):
            data = [1, i, 100, 0, 0]
            data = bytes(data)
            i2c.writeto(address=g031_address, buffer=data)
            time.sleep(0.005)

        time.sleep(0.25)

        for i in range(0, 16):
            data = [1, i, 0, 0, 100]
            data = bytes(data)
            i2c.writeto(address=g031_address, buffer=data)
            time.sleep(0.005)
        time.sleep(0.25)

    # j = 200
    # time.sleep(1)
    #
    # for i in range(0, 16):
    #     data = [1, i, j, 0, 0]
    #     data = bytes(data)
    #     i2c.writeto(address=g031_address, buffer=data)
    #     time.sleep(0.01)


if __name__ == '__main__':
    main()
