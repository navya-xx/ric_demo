import logging
import time

from archive.cm4_core_old2.utils.stm32_flash.reset import reset
from archive.lndw_robot.robot import LNDW_Robot

logging.basicConfig(
    format='%(asctime)s.%(msecs)03d  %(levelname)-8s  %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')


def main():
    reset(1)
    robot = LNDW_Robot()
    robot.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        robot.close()


if __name__ == '__main__':
    main()
