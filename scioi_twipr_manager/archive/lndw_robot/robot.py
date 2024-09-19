import logging
import time

from archive.cm4_core_old2.communication.protocols import RawMessage
from archive.cm4_core_old2.communication.serial.serial_device import Serial_Device
from archive.cm4_core_old2.communication.wifi.tcp_device import TCP_Device
from archive.cm4_core_old2.communication.wifi.protocols.tcp_json_protocol import TCP_JSONProtocol, TCP_JSONMessage
from archive.lndw_robot import messages as messages
import board

# DEFINES
lndw_robot_uart_device = "/dev/ttyAMA1"


class LNDW_Robot:
    serial_device: Serial_Device
    tcp_device: TCP_Device

    i2c: board.I2C

    def __init__(self):
        # Serial Device
        self.serial_device = Serial_Device(device=lndw_robot_uart_device, baudrate=115200)

        # I2C
        self.i2c = board.I2C()

        # TCP
        self.tcp_device = TCP_Device(protocols={'json': TCP_JSONProtocol}, uid=[1, 1, 0, 0], name='robot_01')
        self.tcp_device.registerCallback('rx', self._tcp_msg_callback)

    # ------------------------------------------------------------------------------------------------------------------
    def start(self):
        self.serial_device.start()
        self.tcp_device.start()

    # ------------------------------------------------------------------------------------------------------------------
    def close(self):
        self.stopMotors()
        self.setBackLED([0, 0, 0])
        self.setFrontLED([0, 0, 0])
        time.sleep(0.25)
        self.serial_device.close()
        self.tcp_device.close()

    # === MOTORS =======================================================================================================
    def stopMotors(self):
        msg = messages.UART_MSG_CORE_Write_Motors(motor_left_state=0, motor_left_speed=0, motor_right_state=0,
                                                  motor_right_speed=0)
        self.serial_device.send(msg)

    # ------------------------------------------------------------------------------------------------------------------
    def startMotors(self):
        msg = messages.UART_MSG_CORE_Write_Motors(motor_left_state=1, motor_left_speed=0, motor_right_state=1,
                                                  motor_right_speed=0)
        self.serial_device.send(msg)

    # ------------------------------------------------------------------------------------------------------------------
    def setSpeed(self, speed_left, speed_right):
        msg = messages.UART_MSG_CORE_Write_Motors(motor_left_state=1, motor_left_speed=speed_left, motor_right_state=1,
                                                  motor_right_speed=speed_right)

        self.serial_device.send(msg)

    # === LED ==========================================================================================================
    def setFrontLED(self, color):
        for i in range(8, 16):
            data = [1, i, color[0], color[1], color[2]]
            data = bytes(data)
            self.i2c.writeto(address=0x50, buffer=data)
            time.sleep(0.005)

    # ------------------------------------------------------------------------------------------------------------------
    def setBackLED(self, color):
        for i in range(0, 8):
            data = [1, i, color[0], color[1], color[2]]
            data = bytes(data)
            self.i2c.writeto(address=0x50, buffer=data)
            time.sleep(0.005)

    # === COMMUNICATION TCP ============================================================================================
    def _tcp_msg_callback(self, message: RawMessage, *args, **kwargs):

        if message._protocol == TCP_JSONProtocol:
            self._json_message_handler(message)

    # ------------------------------------------------------------------------------------------------------------------
    def _json_message_handler(self, message: TCP_JSONMessage):

        if message.data['cmd'] == 'write':
            if message.data['message'] == 'led_front':
                self.setFrontLED(message.data['data']['color'])
            if message.data['message'] == 'led_back':
                self.setBackLED(message.data['data']['color'])

            if message.data['message'] == 'motor':
                logging.info(f"MSG Speed left: {message.data['data']['speed_left']}, Speed right: {message.data['data']['speed_right']}")
                self.setSpeed(message.data['data']['speed_left'], message.data['data']['speed_right'])


