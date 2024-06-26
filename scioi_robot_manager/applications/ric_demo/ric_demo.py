import logging
import threading
import time

import numpy as np

from applications.ric_demo.robots_demo.ric_demo_manager import RIC_Demo_RobotManager
from applications.ric_demo.simulation.ric_demo_simulation import RIC_Demo_Simulation
from applications.ric_demo.consensus.ric_consensus import ConsensusTWIPR, Consensus
from applications.ric_demo.simulation.src.dummy_device import DummyDevice
from applications.ric_demo.simulation.src.twipr_data import TWIPR_Control_Mode, buildSample
from applications.ric_demo.ric_utils import generate_next_id
from robots.twipr.twipr import TWIPR
from utils.timer import Timer

logger = logging.getLogger("RIC DEMO")
logger.setLevel("DEBUG")


class RIC_Demo:
    mode: str
    ric_robot_manager: RIC_Demo_RobotManager
    simulation: RIC_Demo_Simulation
    optitrack: ...
    gui: ...
    consensus: Consensus

    _virtualRobotStreamTimer: Timer

    _thread: threading.Thread

    def __init__(self):

        self.list_of_agent_ids = ['twipr1', 'twipr2']
        self.num_of_agents = 10

        self.ric_robot_manager = RIC_Demo_RobotManager()
        self.ric_robot_manager.registerCallback('stream', self._robotManagerStream_callback)
        self.ric_robot_manager.registerCallback('new_robot', self._robotManagerNewRobot_callback)
        self.ric_robot_manager.registerCallback('robot_disconnected', self._robotManagerRobotDisconnected_callback)

        self.consensus = Consensus()

        self.simulation = RIC_Demo_Simulation()

        self._virtualRobotStreamTimer = Timer()

        self._thread = threading.Thread(target=self._threadFunction)

    def init(self):
        self.ric_robot_manager.init()
        self.simulation.init()

    def start(self):
        self.ric_robot_manager.start()
        time.sleep(0.5)
        self.simulation.start()
        time.sleep(0.5)
        self.consensus.start()
        time.sleep(0.5)

        self._thread.start()

        time.sleep(4)
        # self.addVirtualAgent('vtwipr1')
        #
        # agent = self.simulation.env.virtual_agents['vtwipr1']
        # agent.setPosition(x=2, y=1)

    def _threadFunction(self):
        self._virtualRobotStreamTimer.start()

        while True:
            if self._virtualRobotStreamTimer > 0.1:
                self._virtualRobotStreamTimer.reset()

                for robot_id, agent in self.simulation.env.virtual_agents.items():
                    sample = self.buildSampleFromSimulation(robot_id)
                    if robot_id in self.ric_robot_manager.robotManager.robots.keys():
                        self.ric_robot_manager.robotManager.robots[robot_id].device.dummyStream(sample)

                        # Update the corresponding TWIPR object in the consensus
                        if robot_id in self.consensus.agents.keys():
                            agent = self.consensus.agents[robot_id]
                            agent.last_data_timestamp = time.time()
                            agent.state['x'] = sample['estimation']['state']['x']
                            agent.state['y'] = sample['estimation']['state']['y']
                            agent.state['v'] = sample['estimation']['state']['v']
                            agent.state['theta'] = sample['estimation']['state']['theta']
                            agent.state['theta_dot'] = sample['estimation']['state']['theta_dot']
                            agent.state['psi'] = sample['estimation']['state']['psi']
                            agent.state['psi_dot'] = sample['estimation']['state']['psi_dot']

            time.sleep(0.01)

    def _robotManagerStream_callback(self, stream, robot, *args, **kwargs):
        if not robot.id.startswith('v'):
            x = stream.data['estimation']['state']['x']
            y = stream.data['estimation']['state']['y']
            v = stream.data['estimation']['state']['v']
            theta = stream.data['estimation']['state']['theta']
            theta_dot = stream.data['estimation']['state']['theta_dot']
            psi = stream.data['estimation']['state']['psi']
            psi_dot = stream.data['estimation']['state']['psi_dot']

            if robot.id in self.simulation.env.real_agents.keys():
                self.simulation.setRealAgentConfiguration(agent_id=robot.id, x=x, y=y, theta=theta, psi=psi)
            else:
                print("I have some error in my code")

            if robot.id in self.consensus.agents.keys():
                agent = self.consensus.agents[robot.id]
                agent.last_data_timestamp = time.time()
                agent.state['x'] = x
                agent.state['y'] = y
                agent.state['v'] = v
                agent.state['theta'] = theta
                agent.state['theta_dot'] = theta_dot
                agent.state['psi'] = psi
                agent.state['psi_dot'] = psi_dot

    def _robotManagerNewRobot_callback(self, robot: TWIPR, *args, **kwargs):
        print(f"RIC DEMO: NEW ROBOT: {robot.id}")
        if not robot.id.startswith('v'):
            self.simulation.addRealAgent(robot.id)
            self.consensus.addAgent(robot.id)
            robot.setControlMode(mode=TWIPR_Control_Mode.TWIPR_CONTROL_MODE_BALANCING)
            time.sleep(0.5)
            self.consensus.agents[robot.id].input_callback = self.ric_robot_manager.robotManager.robots[
                robot.id].setInput

    def _robotManagerRobotDisconnected_callback(self, robot, *args, **kwargs):
        print(f"RIC DEMO: ROBOT DISCONNECTED: {robot.id}")
        self.simulation.removeRealAgent(robot.id)
        self.consensus.removeAgent(robot.id)

    def addVirtualAgent(self, agent_id=None):
        if agent_id is not None and not agent_id.startswith('v'):
            logger.warning(f"Cannot add virtual agent with id not starting with \"v\"")
            return
        if agent_id is None:
            ids = self.simulation.env.virtual_agents.keys()
            agent_id = generate_next_id(ids)
        else:
            if agent_id in self.simulation.env.virtual_agents.keys():
                logger.warning(f"ID {agent_id} already in simulation env")
                return

        self.simulation.addVirtualAgent(agent_id)
        self.consensus.addAgent(agent_id)
        virtual_robot_device = DummyDevice(id=agent_id)
        self.consensus.agents[agent_id].input_callback = self.simulation.setVirtualAgentInput
        # manager.robotManager.deviceManager._deviceRegistered_callback(dummy_twipr_device)
        self.ric_robot_manager.robotManager.deviceManager._deviceRegistered_callback(virtual_robot_device)

    def buildSampleFromSimulation(self, robot_id):
        if robot_id in self.simulation.env.virtual_agents.keys():
            virtual_agent = self.simulation.env.virtual_agents[robot_id]
            sample = buildSample()

            sample['general']['id'] = robot_id
            sample['estimation']['state']['x'] = virtual_agent.dynamics.state['x'].value
            sample['estimation']['state']['y'] = virtual_agent.dynamics.state['y'].value
            sample['estimation']['state']['v'] = virtual_agent.dynamics.state['v'].value
            sample['estimation']['state']['theta'] = virtual_agent.dynamics.state['theta'].value
            sample['estimation']['state']['theta_dot'] = virtual_agent.dynamics.state['theta_dot'].value
            sample['estimation']['state']['psi'] = virtual_agent.dynamics.state['psi'].value
            sample['estimation']['state']['psi_dot'] = virtual_agent.dynamics.state['psi_dot'].value

            return sample

    # def consensusinputcallback(self, agent_id, input):
    #     ...

    def formation(self, formation_type='circle', *args, **kwargs):
        if formation_type == 'circle':
            idx = 0
            radius = kwargs['radius']
            for agent in self.list_of_agent_ids:
                self.consensus.agents[agent].formation_ref['x'] = radius * np.cos(2 * np.pi * idx / self.num_of_agents)
                self.consensus.agents[agent].formation_ref['y'] = radius * np.sin(2 * np.pi * idx / self.num_of_agents)
                idx += 1
        elif formation_type == 'line':
            length = kwargs['length']
            space = length / (self.num_of_agents - 1)
            idx = 0
            for agent in self.list_of_agent_ids:
                self.consensus.agents[agent].formation_ref['x'] = -length / 2 + space * idx
                self.consensus.agents[agent].formation_ref['y'] = 0


def main():
    ric_demo = RIC_Demo()
    ric_demo.init()
    ric_demo.start()

    while True:
        time.sleep(1)


if __name__ == '__main__':
    main()
