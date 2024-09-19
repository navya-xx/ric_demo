import time

from archive.lndw_robot.robot import LNDW_Robot


def main():
    robot = LNDW_Robot()
    robot.start()

    robot.setFrontLED([100, 0, 0])
    robot.setBackLED([100, 0, 0])
    for i in range(40, 100):
        robot.setSpeed(0 / 100, 0 / 100)
        time.sleep(0.02)

    time.sleep(20)
    robot.setSpeed(0, 0)
    robot.setFrontLED([0, 0, 0])
    robot.setBackLED([0, 0, 0])

    time.sleep(1)


if __name__ == '__main__':
    main()
