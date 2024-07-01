import math
import random
import threading
import time

from applications.ric_demo.simulation.scioi_pysim.scioi_py_core.utils.orientations import twiprToRotMat
from applications.ric_demo.simulation.src.ric_demo_environment import Environment_RIC
from applications.ric_demo.simulation.scioi_pysim.scioi_py_core.visualization.babylon_new.babylon import BabylonVisualization
from applications.ric_demo import settings


class RIC_Demo_Simulation:
    env: Environment_RIC

    _thread: threading.Thread
    _visualizationThread: threading.Thread

    def __init__(self):
        self.env = Environment_RIC()
        self.visualization = BabylonVisualization(show='none')

        self._visualizationThread = threading.Thread(target=self._threadFunction)
        self._thread = threading.Thread(target=self.env.start)

    def init(self):
        self.env.init()
        self.visualization.init()

    def start(self):
        self.visualization.start()
        self._thread.start()
        self._visualizationThread.start()

    def _threadFunction(self):
        while True:
            for id, agent in self.env.virtual_agents.items():
                data = {
                    'position': {
                        'x': agent.state['x'].value,
                        'y': agent.state['y'].value,
                    },
                    'orientation': twiprToRotMat(agent.state['theta'].value, agent.state['psi'].value)
                }
                self.visualization.updateObject(id, data)

            for id, agent in self.env.real_agents.items():
                data = {
                    'position': {
                        'x': agent.configuration['pos']['x'],
                        'y': agent.configuration['pos']['y'],
                    },
                    'orientation': twiprToRotMat(agent.configuration['theta'].value, agent.configuration['psi'].value)
                }
                self.visualization.updateObject(id, data)
                # print(agent.configuration['theta'].value, agent.configuration['psi'].value)
            time.sleep(0.05)

    def addVirtualAgent(self, id):
        self.visualization.addObject(id, 'twipr', {})
        self.env.addVirtualAgent(id)

    def addRealAgent(self, id):
        color = settings.agents[id]['color']
        self.visualization.addObject(id, 'twipr', {'color': color})
        self.env.addRealAgent(id)

    def removeVirtualAgent(self, id):
        self.visualization.removeObject(id)
        self.env.removeVirtualAgent(id)

    def removeRealAgent(self, id):
        self.visualization.removeObject(id)
        self.env.removeRealAgent(id)

    def setVirtualAgentInput(self, input, agent_id):
        if agent_id in self.env.virtual_agents.keys():
            self.env.virtual_agents[agent_id].input = input

    def getVirtualAgentData(self, agent_id):
        if agent_id in self.env.virtual_agents.keys():
            agent = self.env.virtual_agents[agent_id]
            data = {
                'x': agent.configuration['pos']['x'],
                'y': agent.configuration['pos']['y'],
                'v': agent.dynamics.state['v'],
                'theta': agent.dynamics.state['theta'],
                'theta_dot': agent.dynamics.state['theta_dot'],
                'psi': agent.dynamics.state['psi'],
                'psi_dot': agent.dynamics.state['psi_dot'],
            }
            return data
        else:
            return None

    def setRealAgentConfiguration(self, agent_id, x, y, theta, psi):
        if agent_id in self.env.real_agents.keys():
            self.env.real_agents[agent_id].setPosition(x=x, y=y)

            self.env.real_agents[agent_id].setConfiguration(value=theta, dimension='theta')
            self.env.real_agents[agent_id].setConfiguration(value=psi, dimension='psi')


def main():
    sim = RIC_Demo_Simulation()
    sim.init()
    sim.start()

    time.sleep(1)
    sim.env.addVirtualAgent('twipr7')
    time.sleep(1)
    sim.setVirtualAgentInput('twipr7', [-0.2, -0.21])

    while True:
        print(sim.getVirtualAgentData('twipr7'))
        time.sleep(1)


if __name__ == '__main__':
    main()
