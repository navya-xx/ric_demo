import logging
import time

from extensions.joystick.joystick_manager import JoystickManager, Joystick

logging.basicConfig(
    format='%(asctime)s.%(msecs)03d  %(levelname)-8s  %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')


def callback_new_joystick(joystick, *args, **kwargs):
    joystick.setButtonCallback([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13], 'down', callback_button,
                               parameters={'eventtype': 'down'})

    joystick.setJoyHatCallback(['up', 'down', 'left', 'right'], joyhat_callback)


def callback_button(joystick: Joystick, button, eventtype, *args, **kwargs):
    print(f"Button {button}, Event: {eventtype}, Joystick: {joystick.uuid}")


def joyhat_callback(joystick, direction):
    print(f"JoyHat: Joystick: {joystick.uuid}, Direction: {direction}")
    joystick.rumble(strength=1, duration=500)


def main():
    jm = JoystickManager()
    jm.start()

    jm.registerCallback('new_joystick', callback_new_joystick)

    while True:
        for uuid, joystick in jm.joysticks.items():
            print(f"Joystick {joystick.uuid}, Axis 5: {joystick.axis[5]}")
        time.sleep(0.1)


if __name__ == '__main__':
    main()
