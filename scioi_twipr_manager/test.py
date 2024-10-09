import time

from cm4_core_old.communication.i2c.i2c import I2C_Interface
from control_board.io_extension.io_extension import RobotControl_IO_Extension


def main():
    print("HALLO")
    ioe = RobotControl_IO_Extension(I2C_Interface())
    ioe.rgb_led_intern[2].setColor(100, 0, 100)
    ioe.rgb_led_intern[2].setState(1)

    time.sleep(3)


if __name__ == '__main__':
    main()
