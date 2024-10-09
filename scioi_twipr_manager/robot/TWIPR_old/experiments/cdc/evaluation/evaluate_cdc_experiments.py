import numpy as np
from matplotlib import pyplot as plt

from cm4_core.utils.json_utils import readJSON
from robot.TWIPR_old.utils import getSignal

Ts = 0.01


def evaluate_direct():
    data = readJSON("free_experiment_new_direct_1.json")

    tick = np.asarray(getSignal(data, 'general', 'tick'))
    time = (tick - tick[0]) * Ts
    theta = getSignal(data, 'estimation', 'state', 'theta')

    plt.plot(time, theta)
    plt.show()
    pass


def evaluate_transfer():
    data = readJSON("free_experiment_new_dive_1.json")

    tick = np.asarray(getSignal(data, 'general', 'tick'))
    time = (tick - tick[0]) * Ts
    theta = getSignal(data, 'estimation', 'state', 'theta')

    plt.plot(time, theta)
    plt.show()


def evaluate_estimation():
    data = readJSON("estimation_output.json")

    tick = np.asarray(getSignal(data['samples_experiment'], 'general', 'tick'))
    time = (tick - tick[0]) * Ts
    theta = getSignal(data['samples_experiment'], 'estimation', 'state', 'theta')

    plt.plot(time, theta)
    plt.show()


if __name__ == '__main__':
    # evaluate_direct()
    # evaluate_transfer()
    evaluate_estimation()
