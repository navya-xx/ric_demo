# def test_comm():
#     twipr = TWIPR()
#     twipr.init()
#     twipr.start()
#
#     def rx_samples(samples, *args, **kwargs):
#         sample = samples[0]
#         print(f"{np.rad2deg(sample['estimation']['state']['theta'])}")
#
#     twipr.communication.registerCallback('rx_samples', rx_samples)
#
#     state = 1
#     while True:
#         twipr.communication.serial.debug(state)
#         state = not state
#         time.sleep(0.25)
import time

from cm4_core_old.utils.joystick import rpi_joystick
from cm4_core_old.utils.stm32.stm32 import stm32_reset
from robot.TankRobot.VisionRobot import VisionRobot


def test_comm():
    # stm32_reset(0.25)
    robot = VisionRobot()
    robot.init()
    robot.start()

    state = 1

    while True:
        robot.debug(state)
        robot.setSpeed([0.5, 0.25])
        state = not state
        time.sleep(0.25)


def test_board():
    robot = VisionRobot()
    robot.init()
    robot.start()

    state = 1
    for i in range(0, 10):
        robot.board.setStatusLed(state)
        state = not state
        time.sleep(0.25)

    time.sleep(1)


def test_speed_control():
    stm32_reset(0.25)
    robot = VisionRobot()
    robot.init()
    robot.start()
    time.sleep(2)

    def led_on():
        print("LED ON")
        robot.debug(1)

    def led_off():
        print("LED OFF")
        robot.debug(0)

    joystick = rpi_joystick.RpiJoystick()
    joystick.set_callback(event=rpi_joystick.A, callback=led_on)
    joystick.set_callback(event=rpi_joystick.B, callback=led_off)

    while True:
        val1 = joystick.axes[1]
        val2 = joystick.axes[2]
        speed_left = 0.5 * val1 + 0.5 * val2
        speed_right = 0.5 * val1 - 0.5 * val2
        robot.setSpeed([speed_left, speed_right])
        time.sleep(0.1)


def test_server_comm():
    stm32_reset(0.25)
    robot = VisionRobot()
    robot.init()
    robot.start()

    while True:
        time.sleep(1)


if __name__ == '__main__':
    # test_board()
    # print("HALLO")
    # test_speed_control()
    test_server_comm()
