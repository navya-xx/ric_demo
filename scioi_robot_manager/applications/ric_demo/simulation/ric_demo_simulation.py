import math
import random
import threading
import time

from applications.ric_demo.simulation.src.ric_demo_environment import Environment_RIC


class RIC_Demo_Simulation:
    env: Environment_RIC

    _thread: threading.Thread

    def __init__(self):
        self.env = Environment_RIC(visualization='babylon', webapp_config={'title': 'RIC Demo'})

        self._thread = threading.Thread(target=self._threadFunction)

    def init(self):
        self.env.init()

    def start(self):
        self._thread.start()

    def _threadFunction(self):
        self.env.start()
        ...

    def setVirtualAgentInput(self, agent_id, input):
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
