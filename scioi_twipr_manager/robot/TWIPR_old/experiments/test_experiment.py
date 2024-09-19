import ctypes
import time
import numpy as np

from cm4_core.utils.json_utils import readJSON, writeJSON

from robot.TWIPR_old.experiments import SimpleTWIPR
from robot.TWIPR_old.utils import transform_input_2d_3d, getSignal

import cm4_core.utils.joystick.rpi_joystick as rpi_joystick

import matplotlib.pyplot as plt

Ts = 0.01

K = [0.02, 0.04, 0.006, 0.007,
     0.02, 0.04, 0.006, -0.007]


K = [0.025, 0.04, 0.007, 0.007,
     0.025, 0.04, 0.007, -0.007]

offset = +0.0035


def joystick_control():
    twipr = SimpleTWIPR()

    joystick = rpi_joystick.RpiJoystick()
    joystick.set_callback(event=rpi_joystick.A, callback=twipr.startBalancing)
    joystick.set_callback(event=rpi_joystick.B, callback=twipr.stopBalancing)

    while True:
        val1 = joystick.axes[1] * (-0.05) + offset
        val2 = joystick.axes[2] * 0.15
        twipr.setInput([val1 + val2, val1 - val2])
        time.sleep(0.1)








def runCDC_1():
    twipr = SimpleTWIPR(K)

    joystick = rpi_joystick.RpiJoystick()
    joystick.set_callback(event=rpi_joystick.A, callback=twipr.startBalancing)
    joystick.set_callback(event=rpi_joystick.B, callback=twipr.stopBalancing)

    twipr.clear_samples()
    time_start = time.time()

    while abs(time.time() - time_start) < 20:
        val1 = joystick.axes[1] * (-0.05) + offset
        val2 = joystick.axes[2] * 0.15 * 0.5
        twipr.setInput([val1 + val2, val1 - val2])
        time.sleep(0.1)

    twipr.stopBalancing()
    samples = twipr.getSampleData()
    theta = getSignal(samples, 'estimation', 'state', 'theta')

    writeJSON('./cdc/cdc1.json', samples)

def run_estimation():
    twipr = SimpleTWIPR()

    twipr.comm.function(address=8, module=2, data=K, input_type=ctypes.c_float, output_type=None)
    data = readJSON('cdc/estimation/estimation.json')
    u_est = transform_input_2d_3d(data['u_est'])

    samples_experiment = twipr.runTrajectoryExperiment(u_est, id=1)

    theta = getSignal(samples_experiment, 'estimation', 'state', 'theta')
    data['samples_experiment'] = samples_experiment
    data['samples_all'] = twipr.getSampleData()
    data['y_est'] = theta

    writeJSON('cdc/estimation/estimation.json', data)

    input_plot = np.asarray(data['u_est'])
    plt.plot(10 * input_plot)
    plt.plot(theta)
    plt.show()


if __name__ == '__main__':
    # print("HALLO")
    joystick_control_with_offset()
    # runCDC_1()
    # run_estimation()
    # balance()
    # joystick_control()
    # controllerTuning()
