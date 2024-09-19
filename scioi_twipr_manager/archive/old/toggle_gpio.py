import RPi.GPIO as GPIO
import time


import cobs.cobs as cobs



pin = 18

GPIO.setmode(GPIO.BCM)
GPIO.setup(pin, GPIO.OUT)

for i in range(1,100):
    GPIO.output(pin, GPIO.HIGH)
    time.sleep(0.25)
    GPIO.output(pin, GPIO.LOW)
    time.sleep(0.25)

GPIO.cleanup()
