import threading
import time
from scipy.spatial.transform import Rotation
import numpy as np
from scipy.optimize import minimize

max_forward_torque_cmd = 0.01
max_turning_torque_cmd = 0.03
state = 1

MAX_TORQUE_FORWARD = 0.1

MAX_TORQUE_TURN = 0.15


def increaseForwardTorqueValues(forward, *args, **kwargs):
    global max_turning_torque_cmd, max_forward_torque_cmd
    max_forward_torque_cmd = max_forward_torque_cmd + forward

    if max_forward_torque_cmd > MAX_TORQUE_FORWARD:
        max_forward_torque_cmd = MAX_TORQUE_FORWARD

    print(f"Set Torque values to Turning: {max_turning_torque_cmd}, Forwards: {max_forward_torque_cmd}")


def lowerForwardTorqueValues(forward, *args, **kwargs):
    global max_turning_torque_cmd, max_forward_torque_cmd
    max_forward_torque_cmd = max_forward_torque_cmd - forward

    if max_forward_torque_cmd < 0.01:
        max_forward_torque_cmd = 0.01

    print(f"Set Torque values to Turning: {max_turning_torque_cmd}, Forwards: {max_forward_torque_cmd}")


def increaseTurningTorqueValues(turning, *args, **kwargs):
    global max_turning_torque_cmd
    max_turning_torque_cmd = max_turning_torque_cmd + turning

    if max_turning_torque_cmd > MAX_TORQUE_TURN:
        max_turning_torque_cmd = MAX_TORQUE_TURN
    print(f"Set Torque values to Turning: {max_turning_torque_cmd}, Forwards: {max_forward_torque_cmd}")


def lowerTurningTorqueValues(turning, *args, **kwargs):
    global max_turning_torque_cmd
    max_turning_torque_cmd = max_turning_torque_cmd - turning

    if max_turning_torque_cmd < 0.03:
        max_turning_torque_cmd = 0.03
    print(f"Set Torque values to Turning: {max_turning_torque_cmd}, Forwards: {max_forward_torque_cmd}")


def resetTorqueValues():
    global max_turning_torque_cmd, max_forward_torque_cmd
    max_forward_torque_cmd = 0.02
    max_turning_torque_cmd = 0.04

    print(f"Set Torque values to Turning: {max_turning_torque_cmd}, Forwards: {max_forward_torque_cmd}")


def _quat2eul(rot_quat):
    rot = Rotation.from_quat(rot_quat)
    rot_euler = rot.as_euler('xyz', degrees=False)
    #euler_df = pd.DataFrame(data=rot_euler, columns=['x', 'y', 'z'])
    return rot_euler


def _wrap2Pi(x):
    pi = np.pi
    x_wrapped = (x + np.pi) % (2 * np.pi) - np.pi
    return x_wrapped

class Obstacle:
    state: dict
    id: str
    dynamic: bool

    def __init__(self, id, state, dynamic=True):
        self.state = state
        self.id = id
        self.dynamic = dynamic

class ConsensusTWIPR:
    state: dict
    id: str
    formation_ref: dict
    is_consensus: bool
    input_callback: callable
    last_data_timestamp: float

    def __init__(self, id):
        self.input_callback = None
        self.id = id
        self.formation_ref = {'x': 0, 'y': 0, 'psi': 0}
        self.is_consensus = False
        self.consensus_tol = 0.1
        self.last_data_timestamp = 0
        self.state = {'v_integral': 0, 'psi_dot_integral': 0}

    def setInput(self, input):
        if self.input_callback is not None:
            self.input_callback(input, self.id)

    def resetIntegrator(self):
        self.state['v_integral'] = 0
        self.state['psi_dot_integral'] = 0

    def pos_control_pf(self, centroid, obstacles = None):
        Ts = 0.1
        K_i = 2 * np.array([[0.0125, 0.006],
                            [0.0125, -0.006]])
        delta_s = 0.3
        delta_c = 0.1

        r = np.zeros((2,))
        # dist = np.inf * np.ones(2)
        pos = np.array([self.state['x'], self.state['y']])
        pos_ref = centroid + np.array([self.formation_ref['x'], self.formation_ref['y']])
        psi = self.state['psi']
        v = self.state['v']
        psi_dot = self.state['psi_dot']

        for id, obs in obstacles.items():
            if id == self.id:
                continue
            l_ij = pos - obs
            if np.linalg.norm(l_ij) <= delta_c:
                r = r + (l_ij / np.linalg.norm(l_ij) * (delta_c - delta_s) ** 2 * delta_c / (
                            np.linalg.norm(l_ij) - delta_s) ** 2 - l_ij)
        v_max = 2
        # Calculate the velocity towards the goal
        v_g = 0.05 * (pos_ref - pos)

        # Limit the velocity to v_max
        if np.linalg.norm(v_g) >= v_max:
            v_g = v_max * v_g / np.linalg.norm(v_g)

        r = 0.05 * r
        print(f'for agent {self.id} r is {r}')
        # Calculate temp_pos using rotation matrix
        rotation_matrix = np.array([[np.cos(psi), np.sin(psi)], [-np.sin(psi), np.cos(psi)]])
        temp_pos = rotation_matrix.dot(v_g + r)
        theta = np.arctan2(temp_pos[1], temp_pos[0]) + psi

        # Calculate v_ref
        v_ref = 0.4 * np.linalg.norm(v_g + r) * np.cos(theta - psi)

        u = 1
        if np.cos(theta - psi) < 0:
            u = -1

        # Calculate psi and alpha
        temp_pos = rotation_matrix.dot(pos_ref - pos)
        beta = np.arctan2(temp_pos[1], temp_pos[0]) + psi
        temp_pos = rotation_matrix.dot(r)
        alpha = np.arctan2(temp_pos[1], temp_pos[0]) + psi

        # Calculate phi_ref
        psi_ref = (np.linalg.norm(r) / (np.linalg.norm(r) + np.linalg.norm(v_g))) * alpha + (
                    np.linalg.norm(v_g) / (np.linalg.norm(r) + np.linalg.norm(v_g))) * beta

        # Calculate phi_dot_ref
        psi_dot_ref = 3 * np.sin(psi_ref - psi) * u
        print(f"psi_dot_ref for agent {self.id} is {psi_dot_ref}")
        self.state['v_integral'] += (v_ref - v) * Ts
        self.state['psi_dot_integral'] += (psi_dot_ref - psi_dot) * Ts
        control_input = -K_i @ np.array([self.state['v_integral'], self.state['psi_dot_integral']]).T

        return control_input

    def pos_control_cbf(self, centroid, obstacles=None):

        Ts = 0.1
        K_i = np.array([[0.0125, 0.006],
                            [0.0125, -0.006]])
        delta_s = 0.2

        pos = np.array([self.state['x'], self.state['y']])
        pos_ref = centroid + np.array([self.formation_ref['x'], self.formation_ref['y']])
        if np.linalg.norm(pos - pos_ref) <= self.consensus_tol:
            print(f"Consensus is reached for agent {self.id}")
            self.is_consensus = True
            # return np.array([0.0, 0.0])

        psi =  _wrap2Pi(self.state['psi']) #self.state['psi']  #
        v_g = 0.2 * ( pos_ref - np.asarray(pos) )

        temp_pos = np.array([[np.cos(psi), np.sin(psi)], [-np.sin(psi), np.cos(psi)]]) @ v_g.T
        theta = np.atan2(temp_pos[1], temp_pos[0]) + psi
        # print(theta - psi)

        u = 1
        if np.cos(theta - psi) < 0:
            u = -1

        v_ref = (np.linalg.norm(v_g) * np.cos(theta - psi))
        # v_ref = np.clip(v_ref, -0.1, 0.1)
        psi_dot_ref = (0.2 * np.sin(theta - psi) * u)

        v = self.state['v']
        psi_dot = self.state['psi_dot']

        ## provisional
        # if np.sign(v_ref) != np.sign(v) and np.abs(v_ref - v) > 0.1:
        #    v_ref = 0
        ##

        if obstacles is not None:

            ## Collision Avoidance ##
            # TODO: check if CA parameters are suited for MA case
            pos = np.asarray(pos).T
            p_dot = v * np.array([np.cos(psi), np.sin(psi)]).T
            K_v = 1 / 3
            d1 = 1 / 4
            d2 = 1 / 4
            U = 0
            r = np.array([0, 0]).T
            r_dot = np.array([0, 0]).T
            for id, obs in obstacles.items():
                if id == self.id:
                    continue
                U = U + 1 / ((pos - obs).T @ (pos - obs))
                r = r + 2 * (pos - obs) / ((pos - obs).T @ (pos - obs)) ** 2
                r_dot = r_dot + 2 * p_dot * ((pos - obs).T @ (pos - obs)) / ((pos - obs).T @ (pos - obs)) ** 3 - 8 * (
                        pos - obs) * (p_dot.T @ (pos - obs)) / ((pos - obs).T @ (pos - obs)) ** 3

            val = 2 / U ** 3 * (p_dot.T @ r) ** 2 + 1 / U ** 2 * p_dot.T @ r_dot + 1 / U ** 2 * (
                    K_v * (v_ref - v) * np.asarray([np.cos(psi), np.sin(psi)]) @ r + psi_dot_ref * v * np.asarray(
                [-np.sin(psi), np.cos(psi)]) @ r) + (d1 + d2) / U ** 2 * p_dot.T @ r + d1 * d2 * (
                          1 / U - delta_s ** 2)
            if val < 0:
                lam = val / (K_v ** 2 / U ** 4 * (
                            np.asarray([np.cos(psi), np.sin(psi)]) @ r) ** 2 + v ** 2 / U ** 4 * (
                                     np.asarray([-np.sin(psi), np.cos(psi)]) @ r) ** 2)
                v_ref = v_ref - 1 / U ** 2 * K_v * lam * np.asarray([np.cos(psi), np.sin(psi)]) @ r
                psi_dot_ref = psi_dot_ref - 1 / U ** 2 * lam * v * np.asarray([-np.sin(psi), np.cos(psi)]) @ r
                # TODO: check if psi control works for multiple agents
                # temp_pos = np.array([[np.cos(psi), np.sin(psi)], [-np.sin(psi), np.cos(psi)]]) @ r
                # alpha = np.atan2(temp_pos[1], temp_pos[0]) + psi + np.pi / 2
                #
                # psi_ref = alpha + (theta - alpha) * np.exp(-0.5 * r.T @ r)
                # psi_dot_ref = 0.8 * np.sin(psi_ref - psi) * u  # 0.8 * np.sin(psi_ref - psi) * u

        if np.abs(v_ref - v) > 0.02:
            self.state['v_integral'] += (v_ref - v) * Ts
            self.state['psi_dot_integral'] += (psi_dot_ref - psi_dot) * Ts
        control_input = - K_i @ np.array([self.state['v_integral'], self.state['psi_dot_integral']]).T
        # clip
        control_input = np.clip(control_input, -0.05, 0.05)

        return control_input

    def pos_control_opt(self, centroid, obstacles=None):

        if self.is_consensus == True:
            return np.array([0.0, 0.0])

        Ts = 0.1
        K_i = 2 * np.array([[0.0125, 0.006],
                            [0.0125, -0.006]])
        delta_s = 0.3

        pos = np.array([self.state['x'], self.state['y']])
        pos_ref = centroid + np.array([self.formation_ref['x'], self.formation_ref['y']])
        # print(f'pos_ref for agent {self.id} is {pos_ref}')
        # print(f'pos for agent {self.id} is {pos}')
        # print(f"Distance from consensus for agent {self.id} is {np.linalg.norm(pos - pos_ref)}")
        if np.linalg.norm(pos - pos_ref) <= self.consensus_tol:
            print(f"Consensus is reached for agent {self.id}")
            self.is_consensus = True
            return np.array([0.0, 0.0])

        psi = self.state['psi']  # _wrap2Pi(self.state['psi'])
        v_g = pos_ref - np.asarray(pos)

        temp_pos = np.array([[np.cos(psi), np.sin(psi)], [-np.sin(psi), np.cos(psi)]]) @ v_g.T
        theta = np.atan2(temp_pos[1], temp_pos[0]) + psi

        u = 1
        if np.cos(theta - psi) < 0:
            u = -1

        v_ref = (0.3 * np.linalg.norm(v_g) * np.cos(theta - psi))
        psi_dot_ref = (0.5 * np.sin(theta - psi) * u)

        v = self.state['v']
        psi_dot = self.state['psi_dot']

        ## provisional
        # if np.sign(v_ref) != np.sign(v) and np.abs(v_ref - v) > 0.1:
        #    v_ref = 0
        ##

        if obstacles is not None:

            kappa = 0.1
            obs_sep = 0.5

            def obj(u):
                v_i, psi_dot_i = u
                loss = (v_i - v_ref) ** 2 + (psi_dot_i - psi_dot_ref) ** 2
                return loss

            def constraints(u):
                v_i, psi_dot_i = u
                constraints = []

                for id, obs in obstacles.items():
                    if self.id == id:
                        continue
                    h_ij = 2 * (self.state['x'] - obs.state['x']) * (
                                self.state['v'] * np.cos(self.state['psi']) - obs.state['v'] * np.cos(
                            obs.state['psi'])) + \
                           2 * (self.state['y'] - obs.state['y']) * (
                                       self.state['v'] * np.sin(self.state['psi']) - obs.state['v'] * np.sin(
                                   obs.state['psi'])) + \
                           kappa * ((self.state['x'] - obs.state['x']) ** 2 + (
                                self.state['y'] - obs.state['y']) ** 2 - obs_sep ** 2)
                    constraints.append(h_ij)
                return [{'type': 'ineq', 'fun': lambda u, c=c: c} for c in constraints]

            u0 = np.array([v, psi_dot])

            result = minimize(obj, u0, constraints=constraints(u0), method='SLSQP')

            if result.success:
                v_ref, psi_dot_ref = result.x
            else:
                print(f"Optimization failed for agent {self.id}")

        # if np.abs(v_ref - v) > 0.05:
        self.state['v_integral'] += (v_ref - v) * Ts
        self.state['psi_dot_integral'] += (psi_dot_ref - psi_dot) * Ts
        control_input = -K_i @ np.array([self.state['v_integral'], self.state['psi_dot_integral']]).T

        return control_input

    def psi_control(self):
        torque_val = 0.001
        psi_diff = (self.state['psi'] - self.formation_ref['psi']) % (2 * np.pi)
        if psi_diff > 0.1:
            self.setInput([-torque_val, torque_val])
            psi_diff = (self.state['psi'] - self.formation_ref['psi']) % (2 * np.pi)
            if psi_diff <= 0.1:
                self.setInput([0, 0])
        else:
            self.setInput([0, 0])
        psi_diff = (self.state['psi'] - self.formation_ref['psi']) % (2 * np.pi)
        return (psi_diff <= 0.1)

class Consensus:
    agents: dict[str, ConsensusTWIPR]
    obstacles: dict[str, Obstacle]
    reach_consensus: bool
    thread: threading.Thread

    def __init__(self, agents=None):
        if agents is not None:
            self.agents = agents
        else:
            self.agents = {}

        self.obstacles = {}

        self.thread = threading.Thread(target=self._threadFunc)
        self._sThread = threading.Thread(target=self._thread_single_obs_avoidance)

        self.reach_consensus = False

    def init(self):
        ...

    def start(self):
        self.thread.start()

    def addAgent(self, id):
        self.agents[id] = ConsensusTWIPR(id)

    def removeAgent(self, id):
        self.agents.pop(id)

    def setAgentFormationRef(self, id, formation_ref):
        self.agents[id].formation_ref = formation_ref

    def calcCentroid(self):
        num_agents = len(self.agents.keys())
        x = 0
        y = 0
        for agent in self.agents.values():
            x += agent.state['x'] - agent.formation_ref['x']
            y += agent.state['y'] - agent.formation_ref['y']
        x = x / num_agents
        y = y / num_agents
        return np.array([x, y])

    def listObstacles(self):
        obstacles = {}
        for agent in self.agents.values():
            obstacles[agent.id] = np.array([agent.state['x'], agent.state['y']])
        return obstacles

    def add_agents_as_obstacles(self):
        for agent in self.agents.values():
            self.obstacles[agent.id] = Obstacle(agent.id, agent.state, dynamic=True)

    def add_static_obstacle(self, id, pos):
        obs_state = {'x': pos['x'], 'y': pos['y'], 'v':0, 'psi':0, 'theta':0, 'psi_do':0, 'theta_dot':0}
        self.obstacles[id] = Obstacle(id, obs_state, dynamic=False)

    def formation(self, formation_type='circle', idx=0, *args, **kwargs):
        num_of_agents = len(self.agents)
        # print(num_of_agents)
        if formation_type == 'circle':
            if 'radius' in kwargs:
                radius = kwargs['radius']
            else:
                radius = (num_of_agents - 1) * 0.2 / 2 / np.pi
            for agent in self.agents.values():
                agent.formation_ref['x'] = radius * np.cos(2 * np.pi * idx / num_of_agents)
                agent.formation_ref['y'] = radius * np.sin(2 * np.pi * idx / num_of_agents)
                agent.formation_ref['psi'] = (2 * np.pi * idx / num_of_agents) + np.pi/2
                idx += 1
                idx = idx % num_of_agents
        elif formation_type == 'line':
            length = kwargs['length']
            if (num_of_agents > 1):
                space = length / (num_of_agents - 1)
            else:
                space = 0
            idx = 0
            for agent in self.agents.values():
                agent.formation_ref['x'] = - length / 2 + space * idx
                agent.formation_ref['y'] = 0
                idx += 1

    def _threadFunc(self):
        # time.sleep(5)
        idx = 0
        # self.formation(formation_type='circle', idx=idx, radius=1, length=2.0)
        # self.add_agents_as_obstacles()
        # self.agents['twipr1'].formation_ref = {'x': self.agents['twipr1'].state['x'] - 0.5, 'y': self.agents['twipr1'].state['y'] + 0.5}
        self.agents['twipr1'].formation_ref = {'x': -0.6685745120048523, 'y': -0.3451452851295471}
        # self.agents['twipr2'].formation_ref = {'x': -0.5, 'y': self.agents['twipr2'].state['y']}
        # self.agents['twipr3'].formation_ref = {'x': -0.5, 'y': self.agents['twipr3'].state['y']}
        # self.agents['twipr4'].formation_ref = {'x': -0.5, 'y': self.agents['twipr4'].state['y']}
        while True:
            all_agents_reach_consensus = True
            if not self.reach_consensus:
                for agent in self.agents.values():
                    # centroid = self.calcCentroid()
                    centroid = np.array([0, 0])
                    obstacles = {'obstacle1': np.array([0, 0])}
                    # obstacles = None  # self.listObstacles()
                    control_input = agent.pos_control_cbf(centroid, obstacles).tolist()
                    print(f"Control input of {agent.id} is {control_input}")
                    print(f"Current pos of {agent.id} : {agent.state['x'], agent.state['y'], agent.state['v'], agent.state['psi'], agent.state['psi_dot'], agent.state['theta'], agent.state['theta_dot']}")
                    print(f"Ref pos of {agent.id} : {agent.formation_ref['x'], agent.formation_ref['y']}")
                    agent.setInput(control_input)

                    if not agent.is_consensus and all_agents_reach_consensus == True:
                        all_agents_reach_consensus = False

            if all_agents_reach_consensus:
                self.reach_consensus = False
                print("All agents reached consensus!")
                # for agent in self.agents.values():
                #     agent.setInput([0.0, 0.0])

                # psi_control_complete = False
                # while psi_control_complete is False:
                #     psi_control_complete = True
                #     for agent in self.agents.values():
                #         tmp = agent.psi_control()
                #         if psi_control_complete and not tmp:
                #             psi_control_complete = False
                #     time.sleep(0.1)

                # time.sleep(2)
                # idx = (idx + 1) % len(self.agents)
                # self.formation(formation_type='circle', idx=idx, radius=1)
                # self.reach_consensus = False

            time.sleep(0.1)

    def _thread_single_obs_avoidance(self):
        # time.sleep(5)

        if len(self.agents.keys()) == 1:
            for agent in self.agents.values():
                agent.formation_ref = {'x': -1.0, 'y': 0.0, 'psi': 0.0}
        else:
            idx = 0
            self.formation(formation_type='line', idx=idx, radius=1, length=2.0)

        while True:
            all_agents_reach_consensus = True
            if not self.reach_consensus:
                for agent in self.agents.values():
                    # centroid = self.calcCentroid()
                    centroid = np.array([0, 0])
                    self.add_static_obstacle('obstacle1', {'x': 0, 'y': 0})
                    obstacles = {'obstacle1': self.obstacles['obstacle1']}  # self.listObstacles()
                    control_input = agent.pos_control_cbf(centroid, obstacles).tolist()
                    print(f"Control input of {agent.id} is {control_input}")
                    print(f"Current pos of {agent.id} : {agent.state['x'], agent.state['y']}")
                    # agent.state['v'], agent.state['psi'], agent.state['psi_dot'], agent.state['theta'], agent.state['theta_dot']}")
                    print(
                        f"Ref pos of {agent.id} : {agent.formation_ref['x'], agent.formation_ref['y'], agent.formation_ref['psi']}")
                    agent.setInput(control_input)

                    if not agent.is_consensus and all_agents_reach_consensus == True:
                        all_agents_reach_consensus = False

            if all_agents_reach_consensus:
                self.reach_consensus = True
                print("All agents reached consensus!")
                for agent in self.agents.values():
                    agent.setInput([0.0, 0.0])

                # psi_control_complete = False
                # while psi_control_complete is False:
                #     psi_control_complete = True
                #     for agent in self.agents.values():
                #         tmp = agent.psi_control()
                #         if psi_control_complete and not tmp:
                #             psi_control_complete = False
                #     time.sleep(0.1)

                # time.sleep(2)
                # idx = (idx + 1) % len(self.agents)
                # self.formation(formation_type='circle', idx=idx, radius=1)
                # self.reach_consensus = False

            time.sleep(0.1)