import signal
import sys
import time
import RPi.GPIO as GPIO

# pin_output = 16
pin_output = 5
pin_input = 6


def test_send_interrupt():
    # GPIO.setwarnings(False)
    GPIO.cleanup()
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pin_output, GPIO.OUT)
    GPIO.output(pin_output, 1)
    time.sleep(0.1)
    GPIO.output(pin_output, 0)
    GPIO.cleanup()


def test_receive_interrupt():
    def signal_handler(sig, frame):
        GPIO.cleanup()
        print("exit")
        sys.exit(0)

    def interrupt_callback(*args, **kwargs):
        print("Interrupt!")

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pin_input, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.add_event_detect(pin_input, GPIO.RISING,
                          callback=interrupt_callback, bouncetime=1)

    signal.signal(signal.SIGINT, signal_handler)
    signal.pause()


if __name__ == '__main__':
    # test_receive_interrupt()
    test_send_interrupt()
