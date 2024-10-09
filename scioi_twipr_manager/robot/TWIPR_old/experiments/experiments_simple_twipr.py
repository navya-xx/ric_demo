import copy
import ctypes
import time
import board
import busio
from RPi import GPIO
import logging

from robot.TWIPR.communication.twipr_comm_stm import TWIPR_Communication_STM32
from robot.TWIPR.communication.twipr_comm_utils import reset_uart
from cm4_core.utils.ctypes_utils import struct_to_dict

logging.basicConfig(format='%(asctime)s.%(msecs)03d %(levelname)s %(message)s', datefmt='%Y-%m-%d,%H:%M:%S',
                    level='INFO')

TRAJECTORY_BUFFER_SIZE = 10 * 100
TRAJECTORY_SIZE = 12

SAMPLE_BUFFER_SIZE = 10
SAMPLE_SIZE = 84

PIN_INT_0 = 5

Ts = 0.01


class sample_general(ctypes.Structure):
    _fields_ = [("tick", ctypes.c_uint32)]


class twipr_gyr_data(ctypes.Structure):
    _fields_ = [("x", ctypes.c_float), ("y", ctypes.c_float), ("z", ctypes.c_float)]


class twipr_acc_data(ctypes.Structure):
    _fields_ = [("x", ctypes.c_float), ("y", ctypes.c_float), ("z", ctypes.c_float)]


class twipr_sensor_data(ctypes.Structure):
    _fields_ = [("speed_left", ctypes.c_float), ("speed_right", ctypes.c_float), ("acc", twipr_acc_data),
                ("gyr", twipr_gyr_data)]


class twipr_estimation_state(ctypes.Structure):
    _fields_ = [("v", ctypes.c_float), ("theta", ctypes.c_float), ("theta_dot", ctypes.c_float),
                ("psi", ctypes.c_float), ("psi_dot", ctypes.c_float)]


class sample_estimation(ctypes.Structure):
    _fields_ = [('state', twipr_estimation_state), ('data', twipr_sensor_data)]


class twipr_control_input(ctypes.Structure):
    _fields_ = [("u1", ctypes.c_float), ("u2", ctypes.c_float)]


class twipr_control_output(ctypes.Structure):
    _fields_ = [("u_left", ctypes.c_float), ("u_right", ctypes.c_float)]


class sample_control(ctypes.Structure):
    _fields_ = [('status', ctypes.c_int8), ('mode', ctypes.c_int8), ("input", twipr_control_input),
                ("output", twipr_control_output), ("trajectory_step", ctypes.c_uint32),
                ("trajectory_id", ctypes.c_uint16)]


class twipr_sample(ctypes.Structure):
    _fields_ = [("general", sample_general), ("control", sample_control), ("estimation", sample_estimation)]


class trajectory_input(ctypes.Structure):
    _fields_ = [("step", ctypes.c_uint32), ("u_1", ctypes.c_float), ("u_2", ctypes.c_float)]


class trajectory_struct(ctypes.Structure):
    _fields_ = [('step', ctypes.c_uint16), ('id', ctypes.c_uint16), ('length', ctypes.c_uint16)]


pin_samples_ready = 6


class SimpleTWIPR:
    comm: TWIPR_Communication_STM32

    def __init__(self, K=None):
        reset_uart()
        self.comm = TWIPR_Communication_STM32()
        self.comm.start()
        self.spi = board.SPI()
        while not self.spi.try_lock():
            pass
        self.spi.configure(baudrate=10000000)

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin_samples_ready, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(PIN_INT_0, GPIO.OUT)
        GPIO.add_event_detect(pin_samples_ready, GPIO.RISING,
                              callback=self.samples_ready_callback, bouncetime=1)

        self.samples = []

        if K is not None:
            self.comm.function(address=8, module=2, data=K, input_type=ctypes.c_float, output_type=None)

        self.first_sample_received = False

    def clear_samples(self):
        self.samples = []

    def samples_ready_callback(self, *args, **kwargs):
        # logging.info("RX")
        new_samples = self.readSampleData()
        if not self.first_sample_received:
            logging.info("READY")
            self.first_sample_received = True
            # logging.info(f"Samples Ready, tick = {new_samples[0]['general']['tick']}")
        self.samples.extend(new_samples)
        pass

    def readSampleData(self):
        data_rx_bytes = bytearray(SAMPLE_SIZE * SAMPLE_BUFFER_SIZE)
        self.spi.readinto(data_rx_bytes, start=0, end=SAMPLE_SIZE * SAMPLE_BUFFER_SIZE, write_value=2)
        samples = []
        for i in range(0, SAMPLE_BUFFER_SIZE):
            samples.append(
                struct_to_dict(twipr_sample.from_buffer_copy(data_rx_bytes[i * SAMPLE_SIZE:(i + 1) * SAMPLE_SIZE])))

        return samples

    def startBalancing(self):
        self.comm.function(module=0x02, address=4, data=2, input_type=ctypes.c_uint8, output_type=None)

    def stopBalancing(self):
        self.comm.function(module=0x02, address=4, data=0, input_type=ctypes.c_uint8, output_type=None)

    def setInput(self, input: list):
        assert (isinstance(input, list))
        assert (len(input) == 2)
        assert (all(isinstance(elem, (float, int)) for elem in input))

        input_struct = twipr_control_input(u1=input[0], u2=input[1])

        self.comm.function(module=0x02, address=1, data=input_struct, input_type=twipr_control_input)

    def sendTrajectory(self, trajectory: list):
        assert (isinstance(trajectory, list))
        assert (all(isinstance(elem, list) for elem in trajectory))
        assert (all(len(elem) == 2 for elem in trajectory))
        assert (len(trajectory) <= TRAJECTORY_BUFFER_SIZE)

        trajectory_buffer = bytearray(TRAJECTORY_SIZE * TRAJECTORY_BUFFER_SIZE)
        for i, elem in enumerate(trajectory):
            trajectory_step_bytes = bytes(trajectory_input(step=i, u_1=elem[0], u_2=elem[1]))
            trajectory_buffer[i * TRAJECTORY_SIZE:(i + 1) * TRAJECTORY_SIZE] = trajectory_step_bytes

        # Signal to the STM32 that there is a trajectory transfer now
        GPIO.output(PIN_INT_0, 0)
        GPIO.output(PIN_INT_0, 1)

        self.spi.write(trajectory_buffer, start=0, end=TRAJECTORY_SIZE * TRAJECTORY_BUFFER_SIZE)

    def startTrajectory(self, length, id, step=0):
        trajectory = trajectory_struct(step=step, length=length, id=id)
        self.comm.function(module=0x02, address=5, data=trajectory, input_type=trajectory_struct)

    def getSampleData(self):
        return copy.deepcopy(self.samples)

    def getTrajectorySamples(self, trajectory_id):
        trajectory_id_samples = [sample['control']['trajectory_id'] for sample in self.samples]
        indexes = [idx for idx, val in enumerate(trajectory_id_samples) if val == trajectory_id]
        index_first = min(indexes)
        index_last = max(indexes)
        return self.samples[index_first:index_last + 1]

    def waitForTrajectory(self, trajectory_id, timeout=None):

        # Wait for the trajectory to start
        while not (self.samples[-1]['control']['trajectory_id']) == trajectory_id:
            pass

        while (self.samples[-1]['control']['trajectory_id']) == trajectory_id:
            pass

    def runTrajectoryExperiment(self, u, id):
        self.sendTrajectory(u)
        self.startTrajectory(length=len(u), id=id)
        self.waitForTrajectory(trajectory_id=id)

        return self.getTrajectorySamples(id)
