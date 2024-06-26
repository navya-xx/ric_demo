import threading
import time
from scipy.spatial.transform import Rotation
import numpy as np

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
        self.formation_ref = None
        self.is_consensus = False
        self.consensus_tol = .01
        self.last_data_timestamp = 0
        self.state = {}

    def setInput(self, input):
        if self.input_callback is not None:
            self.input_callback(input, self.id)

    def resetIntegrator(self):
        self.state['v_integral'] = 0
        self.state['psi_dot_integral'] = 0

    def _quat2eul(self, rot_quat):
        rot = Rotation.from_quat(rot_quat)
        rot_euler = rot.as_euler('xyz', degrees=False)
        #euler_df = pd.DataFrame(data=rot_euler, columns=['x', 'y', 'z'])
        return rot_euler

    def _wrap2Pi(self, x):
        pi = np.pi
        x_wrapped = (x + np.pi) % (2 * np.pi) - np.pi
        return x_wrapped


def _posControl(self, centroid, obstacles):
    Ts = 0.2
    K_i = 2 * np.array([[0.0125, 0.006],
                        [0.0125, -0.006]])
    delta_s = 0.5

    pos = np.array([self.state['x'], self.state['y']])
    pos_ref = centroid - np.array([self.formation_ref['x'], self.formation_ref['y']])

    if np.linalg.norm(pos - pos_ref) <= self.consensus_tol:
        self.is_consensus = True
        return [0.0, 0.0]

    psi = self._wrap2Pi(self.state['psi'] - np.pi)
    v_g = pos_ref - np.asarray(pos)

    temp_pos = np.array([[np.cos(psi), np.sin(psi)], [-np.sin(psi), np.cos(psi)]]) @ v_g.T
    theta = np.atan2(temp_pos[1], temp_pos[0]) + psi

    u = 1
    if np.cos(theta - psi) < 0:
        u = -1

    v_ref = (0.3 * np.linalg.norm(v_g) * np.cos(theta - psi))
    psi_dot_ref = (0.8 * np.sin(theta - psi) * u)

    v = self.state['v']
    psi_dot = self.state['psi_dot']

    ## provisional
    if np.sign(v_ref) == np.sign(v) or np.abs(v_ref - v) <= 0.1:
        v_ref = v_ref
    else:
        v_ref = 0
    ##

    ## Collision Avoidance ##
    # TODO: check if CA parameters are suited for MA case
    pos = np.asarray(pos).T
    p_dot = v * np.array([np.cos(psi), np.sin(psi)]).T
    K_v = 1 / 3
    d1 = 1 / 2
    d2 = 1 / 2
    U = 0
    r = np.array([0, 0]).T
    r_dot = np.array([0, 0]).T
    for obs in obstacles:
        U = U + 1 / ((pos - obs).T @ (pos - obs))
        r = r + 2 * (pos - obs) / ((pos - obs).T @ (pos - obs)) ** 2
        r_dot = r_dot + 2 * p_dot * ((pos - obs).T @ (pos - obs)) / ((pos - obs).T @ (pos - obs)) ** 3 - 8 * (
                pos - obs) * (p_dot.T @ (pos - obs)) / ((pos - obs).T @ (pos - obs)) ** 3

    val = 2 / U ** 3 * (p_dot.T @ r) ** 2 + 1 / U ** 2 * p_dot.T @ r_dot + 1 / U ** 2 * (
            K_v * (v_ref - v) * np.asarray([np.cos(psi), np.sin(psi)]) @ r + 0 * psi_dot_ref * v * np.asarray(
        [-np.sin(psi), np.cos(psi)]) @ r) + (d1 + d2) / U ** 2 * p_dot.T @ r + d1 * d2 * (
                  1 / U - delta_s ** 2)
    if val < 0:
        lam = val / (K_v ** 2 / U ** 4 * (np.asarray([np.cos(psi), np.sin(psi)]) @ r) ** 2 + 0 * v ** 2 / U ** 4 * (
                np.asarray([-np.sin(psi), np.cos(psi)]) @ r) ** 2)
        v_ref = v_ref - 1 / U ** 2 * K_v * lam * np.asarray([np.cos(psi), np.sin(psi)]) @ r
        psi_dot_ref = psi_dot_ref - 0 * 1 / U ** 2 * lam * v * np.asarray([-np.sin(psi), np.cos(psi)]) @ r

        # TODO: check if psi control works for multiple agents
        temp_pos = np.array([[np.cos(psi), np.sin(psi)], [-np.sin(psi), np.cos(psi)]]) @ r
        alpha = np.atan2(temp_pos[1], temp_pos[0]) + psi + np.pi / 2

        psi_ref = alpha + (theta - alpha) * np.exp(-0.5 * r.T @ r)
        psi_dot_ref = 0.8 * np.sin(psi_ref - psi) * u  # 0.8 * np.sin(psi_ref - psi) * u

    if np.abs(v_ref - v) > 0.05:
        self.state['v_integral'] += (v_ref - v) * Ts
    self.state['psi_dot_integral'] += (psi_dot_ref - psi_dot) * Ts
    u = -K_i @ np.array([self.state['v_integral'], self.state['psi_dot_integral']]).T

    return u


class Consensus:
    agents: dict[str, ConsensusTWIPR]

    thread: threading.Thread

    def __init__(self, agents=None):
        if agents is not None:
            self.agents = agents
        else:
            self.agents = {}

        self.thread = threading.Thread(target=self._threadFunc)

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
        obstacles = []
        for agent in self.agents.values():
            obstacles.append(np.array([agent.state['x'], agent.state['y']]))
        return obstacles

    def _threadFunc(self):
        while True:
            for id, agent in self.agents.items():
                ...
                # agent.setInput([-0.03, -0.04])
                # centroid = self.calcCentroid()
                # obstacles = self.listObstacles()
                # agent.setInput(agent._posControl(centroid, obstacles).tolist())
                #
                # ...

            time.sleep(0.1)
