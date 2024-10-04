import copy
import random
import time

import numpy as np

twipr_wifi_sample = {
    'general': {
        'status': "normal",  # str
        'configuration': 'default',  # str
        'time': 1245601,  # int [ms]
        'tick': 1000,  # int [-]
        'sample_time': 0.01,  # float [s]
        'name': 'abcdef',  # str
        'id': 'abcdef'  # str
    },
    'control': {
        'status': 'normal',  # str
        'mode': 'velocity',  # str [X]
        'configuration': "default",  # str
        'u_ext': [0.0, 0.0],  # list[float] [-] [X]
        'u': {
            'left': 0,  # float [Nm][0-1] [X]
            'right': 0,  # float [Nm][0-1] [X]
        },
        'balancing_control': {
            'status': 'error',  # str
            'u_ext': [0.0, 0.0],  # list[float] [Nm][0-1]
            'u': [0.0, 0.0]  # list[float] [Nm][0-1]
        },
        'speed_control': {
            'status': 'off',  # str
            'u_ext': {
                'v': 0.0,  # float [m/s]
                'psi_dot': 0.0,  # float [rad/s]
            },
            'u': [0.0, 0.0]  # list[float] [-]
        }
    },
    'estimation': {
        'status': 'normal',  # str
        'mode': 'kalman_ext',  # str
        'configuration': 'default',  # str
        'state': {
            'x': 0.0,  # float [m] [X]
            'y': 0.0,  # float [m] [X]
            'v': 0.0,  # float [m/s] [X]
            'theta': 0.0,  # float [grad] [X]
            'theta_dot': 0.0,  # float [grad/s] [X]
            'psi': 0.0,  # float [grad] [X]
            'psi_dot': 0.0,  # float [grad/s] [X]
        },
        'uncertainties':
            {
                'x': 0,  # float [-]
                'y': 0,  # float [-]
                'v': 0,  # float [-]
                'theta': 0,  # float [-]
                'theta_dot': 0,  # float [-]
                'psi': 0,  # float [-]
                'psi_dot': 0,  # float [-]
            }
    },
    'sensors': {
        'imu': {
            'status': 'normal',  # str
            'gyr': [0, 0, 0],  # list[float] [grad/s] [X]
            'acc': [0, 0, 0],  # list[float] [m/s^2] [X]
        },
        'wheel': {
            'status': 'normal',  # str
            'speed': [0, 0],  # list[float] [grad/s] [X]
            'angle': [0, 0]  # list[float] [grad]
        },
        'distance': {
            'front': 0,  # float [m] [X]
            'back': 0,  # float [m] [X]
        },
        'temperature': {
            'board': 0,  # float [C]
            'bms': 0  # float [C]
        }
    },
    'board': {
        'status': 'normal',  # str
        'battery': 14.2,  # float [V] [X]
        'charging': False,  # bool
    },
    'drive': {
        'left': {
            'status': 'normal',  # str
            'u': 1,  # float [Nm] [X]
            'torque': 1,  # float [Nm] [X]
            'speed': 1,  # float [grad/s] [X]
            'angle': 1  # float [grad]
        },
        'right': {
            'status': 1,  # str
            'u': 1,  # float [Nm] [X]
            'torque': 1,  # float [Nm] [X]
            'speed': 1,  # float [grad/s] [X]
            'angle': 2  # float [grad]
        }
    },
    'consensus': {
        'target_pos_ref_x': 0, # float
        'target_pos_ref_y': 0, # float
        'dist_from_ref': 0 # float
    }
}


def get_twipr_wifi_sample(i, name, id, batteryTimeConst=0.005, radius=0.5, movementSpeed=0.1):
    data = copy.deepcopy(twipr_wifi_sample)
    data['general']['time'] = time.time()
    data['general']['tick'] += i
    data['general']['name'] = name
    data['general']['id'] = id
    data['control']['u_ext'] = np.random.rand(2).tolist()
    data['control']['u']['left'] = random.uniform(0, 1)
    data['control']['u']['right'] = random.uniform(0, 1)
    data['control']['balancing_control']['u_ext'] = np.random.rand(2).tolist()
    data['control']['balancing_control']['u'] = np.random.rand(2).tolist()
    data['control']['speed_control']['u_ext']['v'] = random.uniform(0, 10)
    data['control']['speed_control']['u_ext']['psi_dot'] = random.uniform(0, np.pi * 2)
    data['control']['speed_control']['u'] = np.random.rand(2).tolist()
    # data['estimation']['state']['x'] = random.uniform(-10, 10)
    # data['estimation']['state']['y'] = random.uniform(-10, 10)
    # print(radius)
    data['estimation']['state']['x'] = np.cos(i * movementSpeed) * radius
    # print(data['estimation']['state']['x'])
    data['estimation']['state']['y'] = -np.sin(i * movementSpeed) * radius
    data['estimation']['state']['v'] = random.uniform(0, 10)
    # data['estimation']['state']['theta'] = random.uniform(-180, 180)
    data['estimation']['state']['theta'] = (movementSpeed * i) % 360
    data['estimation']['state']['theta_dot'] = random.uniform(-180, 180)
    data['estimation']['state']['psi'] = (i / ((np.pi * 2) / movementSpeed) * 360 + 90) % 360
    data['estimation']['state']['psi_dot'] = random.uniform(-1, 1)
    data['estimation']['uncertainties']['x'] = random.uniform(0, 1)
    data['estimation']['uncertainties']['y'] = random.uniform(0, 1)
    data['estimation']['uncertainties']['v'] = random.uniform(0, 1)
    data['estimation']['uncertainties']['theta'] = random.uniform(0, 1)
    data['estimation']['uncertainties']['theta_dot'] = random.uniform(0, 1)
    data['estimation']['uncertainties']['psi'] = random.uniform(0, 1)
    data['estimation']['uncertainties']['psi_dot'] = random.uniform(0, 1)
    data['sensors']['imu']['gyr'] = np.random.rand(3).tolist()
    data['sensors']['imu']['acc'] = np.random.rand(3).tolist()
    data['sensors']['wheel']['speed'] = np.random.uniform(0, 10, 2).tolist()
    data['sensors']['wheel']['angle'] = np.random.uniform(-180, 180, 2).tolist()
    data['sensors']['distance']['front'] = random.uniform(0, 10)
    data['sensors']['distance']['back'] = random.uniform(0, 10)
    data['sensors']['temperature']['board'] = random.uniform(20, 40)
    data['sensors']['temperature']['bms'] = random.uniform(25, 50)
    data['board']['battery'] = 14.2 - batteryTimeConst * i
    data['board']['charging'] = False
    data['drive']['left']['u'] = random.uniform(0, 1)
    data['drive']['left']['torque'] = random.uniform(0, 1)
    data['drive']['left']['speed'] = random.uniform(0, 10)
    data['drive']['left']['angle'] = random.uniform(-180, 180)
    data['drive']['right']['u'] = random.uniform(0, 1)
    data['drive']['right']['torque'] = random.uniform(0, 1)
    data['drive']['right']['speed'] = random.uniform(0, 10)
    data['drive']['right']['angle'] = random.uniform(-180, 180)
    data['consensus']['target_pos_ref_x'] = random.uniform(-2.5, 2.5)
    data['consensus']['target_pos_ref_y'] = random.uniform(-2.5, 2.5)
    data['consensus']['dist_from_ref'] = random.uniform(-2.5, 2.5)
    return data
