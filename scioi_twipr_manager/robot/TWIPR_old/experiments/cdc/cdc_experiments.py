import ctypes
import os
import time
from os import path


import sys
sys.path.append("/home/pi/software/")

from cm4_core_old.utils.json_utils import readJSON, writeJSON

from robot.TWIPR_old.experiments import SimpleTWIPR
from robot.TWIPR_old.utils import transform_input_2d_3d, getSignal

import cm4_core_old.utils.joystick.rpi_joystick as rpi_joystick

Ts = 0.01

K = [0.025, 0.04, 0.007, 0.012,
     0.025, 0.04, 0.007, -0.012]

# offset = +0.0033
offset = +0.0



# Test







def joystick_control_with_offset():
    twipr = SimpleTWIPR(K)

    joystick = rpi_joystick.RpiJoystick()
    joystick.set_callback(event=rpi_joystick.A, callback=twipr.startBalancing)
    joystick.set_callback(event=rpi_joystick.B, callback=twipr.stopBalancing)

    while True:
        val1 = joystick.axes[1] * (-0.03) + offset
        val2 = joystick.axes[2] * 0.06
        twipr.setInput([val1 + val2, val1 - val2])
        time.sleep(0.1)


def balance():
    twipr = SimpleTWIPR()
    twipr.startBalancing()
    time.sleep(1)

    time.sleep(10)
    twipr.stopBalancing()
    time.sleep(1)


def controllerTuning():
    offset = +0.0035
    # offset = 0 +0.005

    twipr = SimpleTWIPR()
    twipr.comm.function(address=8, module=2, data=K, input_type=ctypes.c_float, output_type=None)

    joystick = rpi_joystick.RpiJoystick()
    joystick.set_callback(event=rpi_joystick.A, callback=twipr.startBalancing)
    joystick.set_callback(event=rpi_joystick.B, callback=twipr.stopBalancing)

    while True:
        val1 = joystick.axes[1] * (-0.05) + offset
        val2 = joystick.axes[2] * 0.15 * 0.5
        twipr.setInput([val1 + val2, val1 - val2])
        time.sleep(0.1)


def run_free_experiment():
    experiment_running = False
    experiment_file = ''
    directory = './free_experiments'

    twipr = SimpleTWIPR(K)

    i_start = 1
    prefix = 'new_direct'

    joystick = rpi_joystick.RpiJoystick()
    joystick.set_callback(event=rpi_joystick.A, callback=twipr.startBalancing)
    joystick.set_callback(event=rpi_joystick.B, callback=twipr.stopBalancing)

    def get_next_file_name():
        i = i_start
        flnm = directory + '/' 'free_experiment_' + prefix + "_" + str(i) + ".json"
        while path.exists(flnm):
            flnm = directory + '/' 'free_experiment_' + prefix + "_" + str(i) + ".json"
            i += 1
        return flnm

    def record_experiment():
        nonlocal experiment_running, experiment_file
        if not experiment_running:
            twipr.clear_samples()
            experiment_running = True
            experiment_file = get_next_file_name()
            print(f"Start Experiment {experiment_file}")

    def stop_experiment():
        nonlocal experiment_running
        if experiment_running:
            experiment_running = False
            samples = twipr.getSampleData()
            writeJSON(experiment_file, samples)
            print(f"Stop Experiment {experiment_file}")

    joystick.set_callback(event=rpi_joystick.X, callback=record_experiment)
    joystick.set_callback(event=rpi_joystick.Y, callback=stop_experiment)

    while True:
        val1 = joystick.axes[1] * (-0.05) + offset
        val2 = joystick.axes[2] * 0.15 * 0.5
        twipr.setInput([val1 + val2, val1 - val2])
        time.sleep(0.1)


def run_trajectory():
    twipr = SimpleTWIPR(K)
    if os.path.isfile('estimation/estimation_output.json'):
        os.remove('estimation/estimation_output.json')
    data = readJSON('estimation/estimation.json')
    u_est = transform_input_2d_3d(data['u_est'])

    joystick = rpi_joystick.RpiJoystick()
    joystick.set_callback(event=rpi_joystick.A, callback=twipr.startBalancing)
    joystick.set_callback(event=rpi_joystick.B, callback=twipr.stopBalancing)

    def run():
        print("Start Trajectory...")
        samples_experiment = twipr.runTrajectoryExperiment(u_est, id=1)

        theta = getSignal(samples_experiment, 'estimation', 'state', 'theta')
        data['samples_experiment'] = samples_experiment
        data['samples_all'] = twipr.getSampleData()
        data['y_est'] = theta
        writeJSON('estimation/estimation_output.json', data)
        print("Trajectory finished")

    joystick.set_callback(event=rpi_joystick.X, callback=run)

    while True:
        val1 = joystick.axes[1] * (-0.05) + offset
        val2 = joystick.axes[2] * 0.15 * 0.5
        twipr.setInput([val1 + val2, val1 - val2])
        time.sleep(0.1)


# def run_estimation():
#     twipr = SimpleTWIPR()
#
#     twipr.comm.function(address=8, module=2, data=K, input_type=ctypes.c_float, output_type=None)
#     data = readJSON('./estimation/estimation.json')
#     u_est = transform_input_2d_3d(data['u_est'])
#
#     samples_experiment = twipr.runTrajectoryExperiment(u_est, id=1)
#
#     theta = getSignal(samples_experiment, 'estimation', 'state', 'theta')
#     data['samples_experiment'] = samples_experiment
#     data['samples_all'] = twipr.getSampleData()
#     data['y_est'] = theta
#
#     writeJSON('./estimation/estimation.json', data)
#
#     input_plot = np.asarray(data['u_est'])
#     plt.plot(10 * input_plot)
#     plt.plot(theta)
#     plt.show()


if __name__ == '__main__':
    # run_free_experiment()
    joystick_control_with_offset()

    # run_trajectory()
