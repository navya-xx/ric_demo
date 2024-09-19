import time

from RPi import GPIO

from robot.TWIPR.settings import TWIPR_GPIO_UART_RESET


def reset_uart():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(TWIPR_GPIO_UART_RESET, GPIO.OUT)
    GPIO.output(TWIPR_GPIO_UART_RESET, 1)
    GPIO.output(TWIPR_GPIO_UART_RESET, 0)
    GPIO.cleanup()
