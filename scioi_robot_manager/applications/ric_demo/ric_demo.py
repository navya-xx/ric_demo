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
from applications.ric_demo.consensus.ric_consensus import _quat2eul, _wrap2Pi

from applications.ric_demo.optitrack.OptiClass import OptiClient
from applications.ric_demo import settings

logger = logging.getLogger("RIC DEMO")
logger.setLevel("DEBUG")


class RIC_Demo:
    mode: str
    ric_robot_manager: RIC_Demo_RobotManager
    simulation: RIC_Demo_Simulation
    gui: ...
    consensus: Consensus

    _virtualRobotStreamTimer: Timer

    _thread: threading.Thread
    def __init__(self):

        self.optitrack = OptiClient("127.0.0.1", "127.0.0.1", True, 0)
        self.optitrack.run()

        self.ric_robot_manager = RIC_Demo_RobotManager()
        self.ric_robot_manager.registerCallback('stream', self._robotManagerStream_callback)
        self.ric_robot_manager.registerCallback('new_robot', self._robotManagerNewRobot_callback)
        self.ric_robot_manager.registerCallback('robot_disconnected', self._robotManagerRobotDisconnected_callback)

        self.Ts = 0.1
        self.consensus = Consensus(optitrack=self.optitrack, gui=self.ric_robot_manager.gui, Ts=self.Ts)

        self.simulation = RIC_Demo_Simulation()

        # self._virtualRobotStreamTimer = Timer()

        self.ric_robot_manager.gui.registerCallback('rx_message', self._guiMessage_callback)

        self._thread = threading.Thread(target=self._threadFunction)

        self.agent_info = {}
        self.obs_dict = {}

        # TODO: REMOVE after experiments are finished
        self.X = []
        self.Y = []
        self.PSI = []
        self.V = []
        self.PSI_DOT = []


    def init(self):
        self.ric_robot_manager.init()
        self.simulation.init()

    def start(self):
        self.ric_robot_manager.start()
        time.sleep(1)
        self.simulation.start()
        time.sleep(1)
        self._thread.start()

        while not self.simulation.visualization.loaded:
            time.sleep(0.1)
        self.simulation.visualization.addObject('floor1', 'floor', {'tile_size': 0.5, 'tiles_x': 20, 'tiles_y': 20})

        time.sleep(5)

        self.ric_robot_manager.gui.print("START")
        print("START")

    def opti_pos_rot(self, robot_id):
        optitrack_id = settings.agents[robot_id]['optitrack_id']
        pos = self.optitrack.rigid_bodies[optitrack_id]['pos'][0:2]
        # pos = (-pos[1], pos[0])
        rot = self.optitrack.rigid_bodies[optitrack_id]['rot']
        rot_euler = _quat2eul(rot)
        # print(f"Opti -- {robot_id} : {pos} -- {rot_euler}")
        return pos, rot_euler

    def getAllAgentsInfo(self):
        for robot_id in self.ric_robot_manager.robotManager.robots.keys():
            [pos, rot] = self.opti_pos_rot(robot_id)
            self.agent_info[robot_id] = {'pos': pos, 'rot': rot.tolist()}

    def getAllObstacles(self):
        for obs in settings.obstacles.keys():
            if settings.obstacles[obs]['optitrack_id'] in self.optitrack.rigid_bodies.keys():
                self.obs_dict[obs] = {'pos': self.optitrack.rigid_bodies[settings.obstacles[obs]['optitrack_id']]['pos'][0:2]}

    def _threadFunction(self):
        # self._virtualRobotStreamTimer.start()
        while True:
            self.getAllAgentsInfo()
            self.getAllObstacles()
            current_centroid = self.consensus.calcCentroid_WMAC()
            for robot_id in self.ric_robot_manager.robotManager.robots.keys():
                # OPTITRACK POSITION
                robot = self.ric_robot_manager.robotManager.robots[robot_id]
                robot.sendPosInfo(pos_dict=self.agent_info[robot_id])

                #print(self.agent_info)
                self.obs_dict.update((self.agent_info.copy()))
                # print(self.agent_info)
                # OBSTACLES
                obs_dict = self.agent_info.copy()
                #obs_dict.pop(robot_id)
                #obs_dict['v1'] = {'pos': [0,0], 'rot': [0,0,0]}
                print(robot_id, obs_dict)
                robot.sendObstacleInfo(obs_dict={'obstacles': obs_dict})

                # TARGET POS
                robot_target_pos = {
                    'x': self.consensus.agents[robot_id].formation_ref['x'] - current_centroid[0], 
                    'y': self.consensus.agents[robot_id].formation_ref['y'] - current_centroid[1]
                }
                robot.sendTargetInfo(pos_dict=robot_target_pos)

            current_virtual_agents = self.simulation.env.virtual_agents.copy()
            for robot_id, agent in current_virtual_agents.items():
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

            time.sleep(self.Ts)

    def _robotManagerStream_callback(self, stream, robot, *args, **kwargs):
        if not robot.id.startswith('v'):
            pos, rot = self.opti_pos_rot(robot.id)
            # print(f"Stream data for {robot.id} -- {stream.data['estimation']['state']}")
            x = pos[0]  # stream.data['estimation']['state']['x']
            y = pos[1]  # stream.data['estimation']['state']['y']
            v = stream.data['estimation']['state']['v']
            theta = stream.data['estimation']['state']['theta']
            theta_dot = stream.data['estimation']['state']['theta_dot']
            psi = rot[2]  # stream.data['estimation']['state']['psi']
            psi_dot = stream.data['estimation']['state']['psi_dot']
            # TODO: REMOVE after experiments are finished
            if stream.data['control']['mode'] != 0:
                if len(self.X) <= 200:
                    self.X.append(x)
                    self.Y.append(y)
                    self.PSI.append(psi)
                    self.V.append(v)
                    self.PSI_DOT.append(psi_dot)
                    '''print('SAVING DATA')
                    np.savetxt("X_f008.txt", self.X, delimiter=",")
                    np.savetxt("Y_f008.txt", self.Y, delimiter=",")
                    np.savetxt("PSI_f008.txt", self.PSI, delimiter=",")
                    np.savetxt("V_f008.txt", self.V, delimiter=",")
                    np.savetxt("PSI_DOT_f008.txt", self.PSI_DOT, delimiter=",")'''

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
            robot.setControlMode(mode=TWIPR_Control_Mode.TWIPR_CONTROL_MODE_OFF)
            self.consensus.agents[robot.id].control_mode = TWIPR_Control_Mode.TWIPR_CONTROL_MODE_OFF
            self.consensus.agents[robot.id].input_callback = self.ric_robot_manager.robotManager.robots[robot.id].setInput
            self.consensus.agents[robot.id].set_control_mode_callback = self.ric_robot_manager.robotManager.robots[robot.id].setControlMode

    def _robotManagerRobotDisconnected_callback(self, robot, *args, **kwargs):
        print(f"RIC DEMO: ROBOT DISCONNECTED: {robot.id}")
        self.simulation.removeRealAgent(robot.id)
        self.consensus.removeAgent(robot.id)

    def addVirtualAgent(self, agent_id=None):
        if agent_id is not None and not agent_id.startswith('v'):
            logger.warning(f"Cannot add virtual agent with id not starting with \"v\"")
            return
        if agent_id is None:
            ids = list(self.simulation.env.virtual_agents.keys())
            agent_id = generate_next_id(ids)
        else:
            if agent_id in self.simulation.env.virtual_agents.keys():
                logger.warning(f"ID {agent_id} already in simulation env")
                return

        self.simulation.addVirtualAgent(agent_id)
        self.consensus.addAgent(agent_id)
        virtual_robot_device = DummyDevice(id=agent_id)
        self.consensus.agents[agent_id].input_callback = self.simulation.setVirtualAgentInput
        self.ric_robot_manager.robotManager.deviceManager._deviceRegistered_callback(virtual_robot_device)
        time.sleep(2)

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

    def _guiMessage_callback(self, message, *args, **kwargs):
        # print(message)
        if 'command' in message['data']:
            if message['data']['command'].startswith('cs'):
                tmp = message['data']['command'].split("_")
                if len(tmp) > 1:
                    self.consensus.formation_type = tmp[1]
                else:
                    self.consensus.formation_type = None
                if len(tmp) > 2:
                    if tmp[1] == 'circle':
                        self.consensus.formation_radius = float(tmp[2])
                    elif tmp[1] == 'line':
                        self.consensus.formation_spacing = float(tmp[2])
                self.run_consensus()
            elif message['data']['command'].startswith('stop'):
                self.ric_robot_manager.gui.print(f"Stop Consensus")
                self.stop_consensus()
            elif message['data']['command'].startswith('vdevs'):
                num_devs = int(message['data']['command'].split("_")[-2])
                spawn_type = str(message['data']['command'].split("_")[-1])
                self.create_virtual_devices(num_devs, spawn_type=spawn_type)
            elif message['data']['command'].startswith('sinput'):
                input_l = float(message['data']['command'].split("_")[-2])
                input_r = float(message['data']['command'].split("_")[-1])
                self.set_dummy_input([input_l, input_r])
            elif message['data']['command'] == 'ss':
                self.run_single_obs_avd()
            elif message['data']['command'] == 'pos':
                self.current_pos()
            elif message['data']['command'] == 'tf':
                self.consensus.trajectory_follow = True
                self.ric_robot_manager.gui.print("Starting Trajectory following")
            elif message['data']['command'] == 'tfs':
                self.consensus.trajectory_follow = False
                self.ric_robot_manager.gui.print("Stopping Trajectory following")


    def create_virtual_devices(self, num_devs, spawn_type='random'):
        for i in range(num_devs):
            if len(self.simulation.env.virtual_agents.keys()) == 0:
                agent_id = 'vtwipr1'
            else:
                agent_id = generate_next_id(list(self.simulation.env.virtual_agents.keys()))
            self.addVirtualAgent(agent_id)
            if spawn_type == 'random':
                x_rand, y_rand = np.random.uniform(-2, 2, 2).tolist()
                self.simulation.env.virtual_agents[agent_id].setPosition(x=x_rand, y=y_rand)
            elif spawn_type == 'line':
                x_line = -2 + i*4/num_devs + 2/num_devs
                y_line = 0
                self.simulation.env.virtual_agents[agent_id].setPosition(x=x_line, y=y_line)
            time.sleep(0.5)

    def run_consensus(self):
        for robot in self.ric_robot_manager.robotManager.robots.values():
            robot.setControlMode(mode=TWIPR_Control_Mode.TWIPR_CONTROL_MODE_BALANCING)
            self.consensus.agents[robot.id].control_mode = TWIPR_Control_Mode.TWIPR_CONTROL_MODE_BALANCING

        # self.addVirtualAgent('vtwipr1')
        # self.consensus.agents['vtwipr1'].state['x'] = 0.5
        # self.consensus.agents['vtwipr1'].state['x'] = -1.0
        # time.sleep(2)
        # self.consensus.start()

    def stop_consensus(self):
        self.consensus.stop()

    def set_dummy_input(self, input):
        print("Set dummy inputs to all devices")
        for robot in self.ric_robot_manager.robotManager.robots.values():
            robot.setControlMode(mode=TWIPR_Control_Mode.TWIPR_CONTROL_MODE_BALANCING)
        time.sleep(1)
        for agent in self.consensus.agents.values():
            agent.setInput(input)

    def run_single_obs_avd(self):
        print("Avoid single obstacle")
        for robot in self.ric_robot_manager.robotManager.robots.values():
            robot.setControlMode(mode=TWIPR_Control_Mode.TWIPR_CONTROL_MODE_BALANCING)
        self.consensus._sThread.start()


    def current_pos(self):
        for agent_id in self.consensus.agents.keys():
            pos, rot = self.opti_pos_rot(agent_id)
            self.ric_robot_manager.gui.print(f"Pos of {agent_id} is {pos} -- {rot}")

def main():
    ric_demo = RIC_Demo()
    ric_demo.init()
    ric_demo.start()

    while True:
        time.sleep(1)


if __name__ == '__main__':
    main()
