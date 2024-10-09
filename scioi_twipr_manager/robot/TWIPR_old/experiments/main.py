import time
import numpy as np

from cm4_core_old.utils.json_utils import readJSON, writeJSON


from robot.TWIPR_old.experiments import SimpleTWIPR
from robot.TWIPR_old.utils import transform_input_2d_3d, getSignal

import cm4_core_old.utils.joystick.rpi_joystick as rpi_joystick

import matplotlib.pyplot as plt

Ts = 0.01

def balance():
    twipr = SimpleTWIPR()
    twipr.startBalancing()
    time.sleep(5)
    twipr.stopBalancing()
    time.sleep(1)

def control_joystick():
    twipr = SimpleTWIPR()

    joystick = rpi_joystick.RpiJoystick()
    joystick.set_callback(event=rpi_joystick.A, callback=twipr.startBalancing)
    joystick.set_callback(event=rpi_joystick.B, callback=twipr.stopBalancing)

    while True:
        val1 = joystick.axes[1]*(-0.05)
        val2 = joystick.axes[2]* 0.15
        twipr.setInput([val1+val2, val1-val2])
        time.sleep(0.1)


def run_estimation():
    twipr = SimpleTWIPR()
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
    control_joystick()

