import threading
import time
from scipy.spatial.transform import Rotation
import numpy as np
from scipy.optimize import minimize
from applications.ric_demo import settings
from applications.ideenexpo.src.ideenexpo_gui import IdeenExpoGUI
from applications.ric_demo.simulation.src.twipr_data import TWIPR_Control_Mode

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
    set_control_mode_callback: callable
    last_data_timestamp: float
    control_mode: int

    def __init__(self, id):
        self.input_callback = None
        self.set_control_mode_callback = None
        self.get_control_mode_callback = None
        self.id = id
        self.formation_ref = {'x': 0, 'y': 0, 'psi': 0}
        self.is_consensus = False
        self.consensus_normalized_tol = 0.01
        self.last_data_timestamp = 0
        self.state = {'v_integral': 0, 'psi_dot_integral': 0}
        self.control_mode = 0

    def setInput(self, input):
        if self.input_callback is not None:
            self.input_callback(input, self.id)

    def setControlMode(self, mode):
        if self.set_control_mode_callback is not None:
            self.set_control_mode_callback(mode, self.id)
            self.control_mode = mode

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

    def pos_control_cbf(self, centroid, obstacles=None, Ts=0.1):

        K_i = 2 * np.array([[0.0125, 0.006], [0.0125, -0.006]])
        # K_i = np.array([[0.06, 0.00495], [0.06, -0.00495]])
        delta_s = 0.4

        pos = np.array([self.state['x'], self.state['y']])
        pos_ref = centroid + np.array([self.formation_ref['x'], self.formation_ref['y']])
        tol_val = np.linalg.norm(pos - pos_ref) / np.linalg.norm(pos_ref) if np.linalg.norm(pos_ref) > 0 else np.linalg.norm(pos)
        if tol_val <= self.consensus_normalized_tol:
            # print(f"Consensus is reached for agent {self.id}")
            self.is_consensus = True
            # return np.array([0.0, 0.0])
        else:
            self.is_consensus = False

        psi = _wrap2Pi(self.state['psi'])  # self.state['psi']  #
        v_g = pos_ref - np.asarray(pos)

        temp_pos = np.array([[np.cos(psi), np.sin(psi)], [-np.sin(psi), np.cos(psi)]]) @ v_g.T
        theta = np.atan2(temp_pos[1], temp_pos[0]) + psi
        # print(theta - psi)

        u = 1
        if np.cos(theta - psi) < 0:
            u = -1

        v_ref = 0.3 * (np.linalg.norm(v_g) * np.cos(theta - psi))
        v_ref = np.clip(v_ref, -0.2, 0.2)
        psi_dot_ref = (0.8 * np.sin(theta - psi) * u)

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
            K_v = 1 / 20
            d1 = 1 / 4
            d2 = 1 / 4
            U = 0
            r = np.array([0, 0]).T
            r_dot = np.array([0, 0]).T
            check_flag = False
            for id, obs in obstacles.items():
                if id == self.id:
                    continue
                U = U + 1 / ((pos - obs).T @ (pos - obs))
                r = r + 2 * (pos - obs) / ((pos - obs).T @ (pos - obs)) ** 2
                r_dot = r_dot + 2 * p_dot * ((pos - obs).T @ (pos - obs)) / ((pos - obs).T @ (pos - obs)) ** 3 - 8 * (
                        pos - obs) * (p_dot.T @ (pos - obs)) / ((pos - obs).T @ (pos - obs)) ** 3

                check_flag = True

            # if (np.linalg.norm(pos - obstacles['obstacle1']) < 0.6):
            #     f = np.array([[0, -1], [1, 0]]) @ r
            #     f_i = np.array([[0, 1], [-1, 0]]) @ r
            #     if np.inner(v_g, f) > 0:
            #         s = 0.1 * f
            #     else:
            #         s = 0.1 * f_i
            # else:
            #     s = np.array([0, 0])

            # temp_pos = np.array([[np.cos(psi), np.sin(psi)], [-np.sin(psi), np.cos(psi)]]) @ (v_g + s).T
            # theta = np.atan2(temp_pos[1], temp_pos[0]) + psi

            # u = 1
            # if np.cos(theta - psi) < 0:
            #     u = -1
            #
            # v_ref = 0.3 * (np.linalg.norm(v_g + s) * np.cos(theta - psi))
            # # v_ref = np.clip(v_ref, -0.1, 0.1)
            # psi_dot_ref = (0.8 * np.sin(theta - psi) * u)

            if check_flag:
                val = 2 / U ** 3 * (p_dot.T @ r) ** 2 + 1 / U ** 2 * p_dot.T @ r_dot + 1 / U ** 2 * (
                        K_v * (v_ref - v) * np.asarray([np.cos(psi), np.sin(psi)]) @ r + psi_dot * v * np.asarray(
                    [-np.sin(psi), np.cos(psi)]) @ r) + (d1 + d2) / U ** 2 * p_dot.T @ r + d1 * d2 * (
                              1 / U - delta_s ** 2)
                if val < 0:
                    lam = val / ((K_v ** 2 / U ** 4 * (np.asarray([np.cos(psi), np.sin(psi)]) @ r) ** 2) +
                                 v ** 2 / U ** 4 * (np.asarray([-np.sin(psi), np.cos(psi)]) @ r) ** 2)
                    v_ref = v_ref - 1 / U ** 2 * K_v * lam * np.asarray([np.cos(psi), np.sin(psi)]) @ r
                    psi_dot_ref = psi_dot_ref - 1 / U ** 2 * lam * v * np.asarray([-np.sin(psi), np.cos(psi)]) @ r
                    # TODO: check if psi control works for multiple agents
                    # temp_pos = np.array([[np.cos(psi), np.sin(psi)], [-np.sin(psi), np.cos(psi)]]) @ r
                    # alpha = np.atan2(temp_pos[1], temp_pos[0]) + psi + np.pi / 2
                    #
                    # psi_ref = alpha + (theta - alpha) * np.exp(-0.5 * r.T @ r)
                    # psi_dot_ref = 0.8 * np.sin(psi_ref - psi) * u  # 0.8 * np.sin(psi_ref - psi) * u

                # print(f"Norm dist from obs {np.linalg.norm(pos - obstacles['obstacle1'])}")

        if np.abs(v_ref - v) > 0.02:
            self.state['v_integral'] += (v_ref - v) * Ts
            self.state['psi_dot_integral'] += (psi_dot_ref - psi_dot) * Ts

        control_input = - K_i @ np.array([self.state['v_integral'], self.state['psi_dot_integral']]).T
        # clip
        control_input = np.clip(control_input, -0.1, 0.1)
        # print(f"abs(V_ref - v) of {self.id} = {np.abs(v_ref - v)}")
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
        if np.linalg.norm(pos - pos_ref) <= self.consensus_normalized_tol:
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
        return psi_diff <= 0.1

class Consensus:
    agents: dict[str, ConsensusTWIPR]
    obstacles: dict[str, Obstacle]
    reach_consensus: bool
    implement_wmac: bool
    thread: threading.Thread
    gui: IdeenExpoGUI

    def __init__(self, agents=None, optitrack=None, gui=None, formation_type=None, formation_radius=None, formation_spacing=None, implement_wmac=False, *args, **kwargs):
        if agents is not None:
            self.agents = agents
        else:
            self.agents = {}

        self.obstacles = {}

        self.thread = threading.Thread(target=self._threadFunc)

        self.reach_consensus = False

        self.implement_wmac = implement_wmac

        self.thread_running = False

        self.optitrack = optitrack
        self.gui = gui

        if 'Ts' in kwargs.keys():
            self.Ts = kwargs['Ts']
        else:
            self.Ts = 0.05  # Sampling time for consensus

        if 'boundary' in kwargs.keys():
            self.boundary = kwargs['boundary']
        else:
            self.boundary = 2.0

        self.is_formation_control = True

        if formation_type is None:
            self.formation_type = 'line'
        else:
            self.formation_type = formation_type
        if formation_radius is None:
            self.formation_radius = 0.5
        else:
            self.formation_radius = formation_radius
        if formation_spacing is None:
            self.formation_spacing = 1.0
        else:
            self.formation_spacing = formation_spacing

        self.counter_centroid_comp = 0
        self.comp_centroid_every = 100
        # self.circular_trajectory_counter = 0

        self.trajectory_follow = False

    def init(self):
        ...

    def start(self):
        self.thread_running = True
        self.thread.start()

    def stop(self):
        self.thread_running = False
        time.sleep(1)
        self.thread.join()

    def addAgent(self, id):
        self.agents[id] = ConsensusTWIPR(id)

    def removeAgent(self, id):
        self.agents.pop(id)

    def setAgentFormationRef(self, id, formation_ref):
        self.agents[id].formation_ref = formation_ref

    def generate_WMAC_weights(self, N):
        # fully connected network
        WMAC_weights = np.random.uniform(0, 1, [N,])
        WMAC_weights /= np.sum(WMAC_weights)
        return WMAC_weights
    
    def calcCentroid_WMAC(self):
        centroid_dict = {}
        for agent_id in self.agents.keys():
            w = self.generate_WMAC_weights(len(self.agents))
            x = 0; y = 0

            for i, id in enumerate(self.agents.keys()):
                agent = self.agents[id]
                if 'x' not in agent.state:
                    agent.state['x'] = 0
                if 'y' not in agent.state:
                    agent.state['y'] = 0
                x += w[i] * (agent.state['x'] - agent.formation_ref['x'])
                y += w[i] * (agent.state['y'] - agent.formation_ref['y'])
            centroid_dict[agent_id] = np.array([x, y])
        return centroid_dict

    def calcCentroid(self):
        if self.counter_centroid_comp % self.comp_centroid_every == 0:
            num_agents = len(self.agents.keys())
            x = 0
            y = 0
            for agent in self.agents.values():
                x += agent.state['x'] - agent.formation_ref['x']
                y += agent.state['y'] - agent.formation_ref['y']
            x = x / num_agents
            y = y / num_agents
            self.centroid = np.array([x, y])


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

    def opti_pos_rot(self, robot_id):
        optitrack_id = settings.agents[robot_id]['optitrack_id']
        pos = self.optitrack.rigid_bodies[optitrack_id]['pos'][0:2]
        # pos = (-pos[1], pos[0])
        rot = self.optitrack.rigid_bodies[optitrack_id]['rot']
        rot_euler = _quat2eul(rot)
        # print(f"Opti -- {robot_id} : {pos} -- {rot_euler}")
        return pos, rot_euler

    def update_trajectory(self, speed=0.1, ang_speed=0.1):

        def cart_to_pol(x, y):
            rho = np.sqrt(x**2 + y**2)
            phi = np.arctan2(y, x)
            return (rho, phi)


        for agent in self.agents.values():
            # print(f"\n Old position of {agent.id} in polar: {cart_to_pol(agent.formation_ref['x'], agent.formation_ref['y'])}")
            angle = ang_speed
            x, y, psi = agent.formation_ref['x'], agent.formation_ref['y'], agent.formation_ref['psi']
            agent.formation_ref['x'] = x * np.cos(angle) - y * np.sin(angle)
            agent.formation_ref['y'] = x * np.sin(angle) + y * np.cos(angle)
            agent.formation_ref['psi'] = psi + angle
            # print(f"New position of {agent.id} in polar: {cart_to_pol(agent.formation_ref['x'], agent.formation_ref['y'])} \n")

        # self.centroid -= (self.centroid * speed)

    def circular_formation(self, *args, **kwargs):
        num_of_agents = len(self.agents)
        if 'radius' in kwargs:
            radius = kwargs['radius']
        else:
            radius = (num_of_agents - 1) * 0.2 / 2 / np.pi
        pos_list = []
        idx = 0
        num_of_real_agents = 0
        # print(self.agents.keys())
        for agent_id in self.agents.keys():
            pos_list.append([radius * np.cos(2 * np.pi * idx / num_of_agents), radius * np.sin(2 * np.pi * idx / num_of_agents), (2 * np.pi * idx / num_of_agents) + np.pi/2])
            idx += 1
            if agent_id.startswith('twipr'):
                num_of_real_agents += 1
        if num_of_real_agents > 0:
            real_ratio = int(np.ceil(num_of_agents / num_of_real_agents))
        else:
            real_ratio = num_of_agents
        id_order = [0] * num_of_agents
        # Assuming real robots are the first in the list
        if num_of_real_agents > 0:
            for i in range(num_of_real_agents):
                id_order[i] = i * real_ratio
        idx = num_of_real_agents
        for i in range(num_of_agents):
            if i % real_ratio == 0:
                continue
            id_order[idx] = i
            idx += 1
        idx = 0
        for agent_id, agent in self.agents.items():
            agent.formation_ref['x'] = pos_list[id_order[idx]][0]
            agent.formation_ref['y'] = pos_list[id_order[idx]][1]
            agent.formation_ref['psi'] = pos_list[id_order[idx]][2]
            idx += 1

    def line_formation(self, *args, **kwargs):
        num_of_agents = len(self.agents)
        spacing = kwargs['spacing']
        length = (num_of_agents - 1) * spacing
        if num_of_agents == 1:
            spacing = 0
        pos_list = []
        for i in range(num_of_agents):
            pos_list.append(- length / 2 + spacing * i)

        # Real robots are close to center
        pos_list_id = np.argsort(np.abs(pos_list))
        pos_list = np.array(pos_list)[pos_list_id]
        idx = 0
        for agent_id, agent in self.agents.items():
            if agent_id.startswith('twipr'):
                agent.formation_ref['y'] = pos_list[idx]
                idx += 1
            agent.formation_ref['x'] = 0
            agent.formation_ref['psi'] = np.pi/2
        for agent_id, agent in self.agents.items():
            if not agent_id.startswith('twipr'):
                agent.formation_ref['x'] = pos_list[idx]
                idx += 1

    def star_formation(self, *args, **kwargs):
        num_of_agents = len(self.agents)
        if 'radius' in kwargs:
            radius = kwargs['radius']
        else:
            radius = (num_of_agents - 1) * 0.4 / 2 / np.pi
        
        pos_list = []
        idx = 0
        num_of_real_agents = 0
        # print(self.agents.keys())
        first_agent = True
        for agent_id in self.agents.keys():
            if first_agent:
                pos_list.append([0, 0, 0]) # one agent at the center of the circle
                first_agent = False
            else:
                pos_list.append([
                        radius * np.cos(2 * np.pi * idx / (num_of_agents - 1)), 
                        radius * np.sin(2 * np.pi * idx / (num_of_agents - 1)), 
                        (2 * np.pi * idx / (num_of_agents - 1)) + np.pi/2
                        ])
            idx += 1
            if agent_id.startswith('twipr'):
                num_of_real_agents += 1
        if num_of_real_agents > 0:
            real_ratio = int(np.ceil(num_of_agents / num_of_real_agents))
        else:
            real_ratio = num_of_agents
        id_order = [0] * num_of_agents
        # Assuming real robots are the first in the list
        if num_of_real_agents > 0:
            for i in range(num_of_real_agents):
                id_order[i] = i * real_ratio
        idx = num_of_real_agents
        for i in range(num_of_agents):
            if i % real_ratio == 0:
                continue
            id_order[idx] = i
            idx += 1
        idx = 0
        try:
            for agent_id, agent in self.agents.items():
                agent.formation_ref['x'] = pos_list[id_order[idx]][0]
                agent.formation_ref['y'] = pos_list[id_order[idx]][1]
                agent.formation_ref['psi'] = pos_list[id_order[idx]][2]
                idx += 1
        except Exception as e:
            print(e)

    def formation(self, formation_type='circle', *args, **kwargs):
        num_of_agents = len(self.agents)
        if formation_type == 'circle':
            self.circular_formation(*args, **kwargs)

        elif formation_type == 'line':
            self.line_formation(*args, **kwargs)

        elif formation_type == 'star':
            self.star_formation(*args, **kwargs)

    def _threadFunc(self):
        # print('test_thread')
        # time.sleep(5)
        if self.is_formation_control:
            idx = 1
            self.formation(formation_type=self.formation_type, idx=idx, radius=self.formation_radius, spacing=self.formation_spacing)
            # self.add_agents_as_obstacles()
        else:
            if 'twipr1' in self.agents:
                self.agents['twipr1'].formation_ref = {'x':0.2967906892299652, 'y': -0.25703999400138855, 'psi': 0}
                # self.agents['twipr1'].formation_ref = {'x': 0.87483793497085574, 'y': -0.4327182471752167, 'psi': 0}
                pass
            if 'twipr2' in self.agents:
                self.agents['twipr2'].formation_ref = {'x': 1.0641813278198242, 'y': -0.060442324727773666, 'psi': 0}
                # self.agents['twipr2'].formation_ref = {'x': -0.6782307624816895, 'y': -0.3796898126602173, 'psi': 0}
            if 'twipr3' in self.agents:
                self.agents['twipr3'].formation_ref = {'x': 1.3114556074142456, 'y': -1.0620574951171875, 'psi': 0}
            if 'twipr4' in self.agents:
                self.agents['twipr4'].formation_ref = {'x': 0.38619229197502136, 'y': -1.0293278694152832, 'psi': 0}
                # self.agents['twipr4'].formation_ref = {'x': -0.6313509941101074, 'y': -1.239223837852478, 'psi': 0}

            self.calcCentroid()
            print(self.centroid)

        self.gui.print("Starting Consensus")

        trajectory_counter = 0
        print_consensus = True

        while self.thread_running:
            # add position information from optitrack
            if self.optitrack is not None:
                for agent_id in self.agents.keys():
                    if agent_id.startswith("twipr"):
                        pos, rot = self.opti_pos_rot(agent_id)
                        self.agents[agent_id].state['x'] = pos[0]
                        self.agents[agent_id].state['y'] = pos[1]
                        self.agents[agent_id].state['psi'] = rot[2]

                        # if np.linalg.norm(pos) > self.boundary and self.agents[agent_id].control_mode == TWIPR_Control_Mode.TWIPR_CONTROL_MODE_BALANCING:
                        #     print(f"Turning {agent_id} control mode off -- outside boundary at dist {np.linalg.norm(pos)}")
                        #     # self.agents[agent_id].setControlMode(TWIPR_Control_Mode.TWIPR_CONTROL_MODE_OFF)
                        #     # set centroid to 0,0
                        #     self.centroid = [0, 0]


            # add position information for virtual devices

            all_agents_reach_consensus = True
            if not self.reach_consensus:
                if self.trajectory_follow:
                    if trajectory_counter == min(30, int(1.0 // self.Ts)):
                        # update trajectory after every 100 runs of consensus
                        self.update_trajectory(speed=0.1, ang_speed=0.1)
                        # self.circular_trajectory_counter += 1
                        trajectory_counter = 0
                    trajectory_counter += 1
                    # self.update_trajectory(speed=0.05, ang_speed=0.05)
                    print_consensus = True
                else:
                    self.calcCentroid()
                    # self.centroid = np.array([-0.4, 0.5])
                    # pass

                # self.counter_centroid_comp += 1
                # self.centroid = np.array([0, 0])
                print('test1')
                for agent in self.agents.values():
                    # obstacles = {'obstacle1': np.array([0, 0])}
                    obstacles = None #self.listObstacles()
                    control_input = agent.pos_control_cbf(self.centroid, obstacles=obstacles, Ts=self.Ts).tolist()
                    print(f"Control input of {agent.id} is {control_input}")
                    print(f"Intregrators  v: {agent.state['v_integral']}, psi_dot: {agent.state['v_integral']}")
                    print(f"Current pos of {agent.id} : {agent.state['x'], agent.state['y']}")  #, agent.state['v'], agent.state['psi'], agent.state['psi_dot'], agent.state['theta'], agent.state['theta_dot']}")
                    print(f"Ref pos of {agent.id} : {agent.formation_ref['x'], agent.formation_ref['y']}")
                    agent.setInput(control_input)

                    if not agent.is_consensus and all_agents_reach_consensus:
                        all_agents_reach_consensus = False

            if all_agents_reach_consensus:
                if print_consensus:
                    self.gui.print("All agents reached consensus!")
                    print_consensus = False

                self.reach_consensus = False

                # for agent in self.agents.values():
                #     agent.setInput([0.0, 0.0])

                # psi_control_complete = False
                # while psi_control_complete is False:
                #     psi_control_complete = True
                #     for agent in self.agents.values():
                #         tmp = agent.psi_control()
                #         if psi_control_complete and not tmp:
                #             psi_control_complete = False
                #     time.sleep(0.01)

                # if psi_control_complete:
                # trajectory_follow = True

                # time.sleep(2)
                # idx = (idx + 1) % len(self.agents)
                # self.formation(formation_type='circle', idx=idx, radius=1)
                # self.reach_consensus = False

            time.sleep(self.Ts)

        if self.thread_running is False:
            print("Thread is stopping")
            for agent in self.agents.values():
                agent.setInput([0, 0])
                agent.resetIntegrator()
                agent.setControlMode(TWIPR_Control_Mode.TWIPR_CONTROL_MODE_OFF)

            self.thread = threading.Thread(target=self._threadFunc)