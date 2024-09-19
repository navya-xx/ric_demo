import sys

from robot.TWIPR.twipr import TWIPR
import time
import logging

sys.path.append("/home/pi/software/")

logging.basicConfig(level=logging.DEBUG)

K = [0.035, 0.06, 0.01, 0.009,
     0.035, 0.06, 0.01, -0.009]


def main():
    twipr = TWIPR()

    twipr.init()
    twipr.start()

    twipr.control._setStateFeedbackGain_LL(K)

    while True:
        time.sleep(1)


if __name__ == '__main__':
    main()
