twipr_wifi_sample = {
    'general': {
        'status': "normal",  # str
        'configuration': 'default',  # str
        'time': 1245601,  # int
        'tick': 1000,  # int
        'sample_time': 0.01,  # float
        'name': 'abcdef',  # str
        'id': 'abcdef'  # str
    },
    'control': {
        'status': 'normal',  # str
        'mode': 'velocity',  # str
        'configuration': "default",  # str
        'u_ext': [0.0, 0.0],  # list[float]
        'u': {
            'left': 0,  # float
            'right': 0,  # float
        },
        'balancing_control': {
            'status': 'error',  # str
            'u_ext': [0.0, 0.0],  # list[float]
            'u': [0.0, 0.0]  # list[float]
        },
        'speed_control': {
            'status': 'off',  # str
            'u_ext': {
                'v': 0.0,  # float
                'psi_dot': 0.0,  # float
            },
            'u': [0.0, 0.0]  # list[float]
        }
    },
    'estimation': {
        'status': 'normal',  # str
        'mode': 'kalman_ext',  # str
        'configuration': 'default',  # str
        'state': {
            'x': 0.0,  # float
            'y': 0.0,  # float
            'v': 0.0,  # float
            'theta': 0.0,  # float
            'theta_dot': 0.0,  # float
            'psi': 0.0,  # float
            'psi_dot': 0.0,  # float
        },
        'uncertainties':
            {
                'x': 0,  # float
                'y': 0,  # float
                'v': 0,  # float
                'theta': 0,  # float
                'theta_dot': 0,  # float
                'psi': 0,  # float
                'psi_dot': 0,  # float
            }
    },
    'sensors': {
        'imu': {
            'status': 'normal',  # str
            'gyr': [0, 0, 0],  # list[float]
            'acc': [0, 0, 0],  # list[float]
        },
        'wheel': {
            'status': 'normal',  # str
            'speed': [0, 0],  # list[float]
            'angle': [0, 0]  # list[float]
        },
        'distance': {
            'front': 0,  # float
            'back': 0,  # float
        },
        'temperature': {
            'board': 0,  # float
            'bms': 0  # float
        }
    },
    'board': {
        'status': 'normal',  # str
        'battery': 14.2,  # float
        'charging': 0,  # float
    },
    'drive': {
        'left': {
            'status': 'normal',  # str
            'u': 1,  # float
            'torque': 1,  # float
            'speed': 1,  # float
            'angle': 1  # float
        },
        'right': {
            'status': 1,  # str
            'u': 1,  # float
            'torque': 1,  # float
            'speed': 1,  # float
            'angle': 2  # float
        }
    }
}
