import math
import threading

from scioi_ritl.application.lndw.optitrack.NatNetClient import NatNetClient
import matplotlib.pyplot as plt
import numpy as np
import qmt


class Optitrack:

    def __init__(self, bodies: int):
        self._thread = threading.Thread(target=self.run, daemon=True)
        self.bodies = {
            '1': {
                'position': [0, 0],
                'psi': 0,
            },
            '2': {
                'position': [0, 0],
                'psi': 0,
            },

        }

    def start(self):
        self._thread.run()

    def run(self):
        self.client = NatNetClient()
        self.client.rigidBodyListener = self.rigidBodyFrame_Callback
        self.client.newFrameListener = self.newFrameCallback
        self.client.run()

    def rigidBodyFrame_Callback(self, id, position, rotation):
        if id == 1:
            self.bodies['1']['position'] = [position[2]*1000-10, position[0]*1000-50]
            self.bodies['1']['psi'] = qmt.wrapTo2Pi(
                qmt.eulerAngles(rotation, 'yxz', intrinsic=True)[0] + math.pi / 2)
        if id == 2:
            self.bodies['2']['position'] = [position[2]*1000-10, position[0]*1000-50]
            self.bodies['2']['psi'] = qmt.wrapTo2Pi(
                qmt.eulerAngles(rotation, 'yxz', intrinsic=True)[0] + math.pi / 2)

    def newFrameCallback(self, *args, **kwargs):
        pass
