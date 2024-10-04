import threading
import time

import math
import numpy as np

from control_board.robot_control_board import RobotControl_Board
from robot.TWIPR.communication.twipr_communication import TWIPR_Communication
from robot.TWIPR.control.twipr_control import TWIPR_Control
from robot.TWIPR.drive.twipr_drive import TWIPR_Drive
from robot.TWIPR.estimation.twipr_estimation import TWIPR_Estimation
from robot.TWIPR.logging.twipr_sample import TWIPR_Sample
from robot.TWIPR.sensors.twipr_sensors import TWIPR_Sensors
from robot.TWIPR.settings import readSettings


# Things to implement:
# - Stream to Server. Where should I put this?

class TWIPR:
    board: RobotControl_Board

    communication: TWIPR_Communication
    control: TWIPR_Control
    estimation: TWIPR_Estimation
    drive: TWIPR_Drive
    sensors: TWIPR_Sensors
    _thread: threading.Thread

    def __init__(self):

        self.robot_settings = readSettings()

        self.board = RobotControl_Board(device_class='robot', device_type='twipr', device_revision='v3',
                                        device_id=self.robot_settings['id'], device_name=self.robot_settings['name'])

        self.communication = TWIPR_Communication(board=self.board)

        self.control = TWIPR_Control(comm=self.communication)
        self.estimation = TWIPR_Estimation(comm=self.communication)
        self.drive = TWIPR_Drive(comm=self.communication)
        self.sensors = TWIPR_Sensors(comm=self.communication)
        self._thread = threading.Thread(target=self._threadFunction)


        self.communication.wifi.addCommand(identifier='testCommand', callback=self.testCommand, arguments=['a', 'b'],
                                            description='')
        self.communication.wifi.addCommand(identifier='getCurrentOrientation', callback=self.getCurrentOrientation,
                                           arguments=['pos'], description='')
        self.communication.wifi.addCommand(identifier='getObstacles', callback=self.getObstacles,
                                           arguments=['obstacles'], description='')

        # General parameters
        self.Ts = 0.1
        self.pos_ref = np.asarray([0,0])

        # State information
        self.pos = np.array([0.0, 0.0])
        self.rot = np.array([0.0, 0.0, 0.0])
        self.obstacles = {}
        self.integral = [0.0, 0.0]

        # Control parameters
        self.K_i = 0
        self.u_offset = self.robot_settings['u_offset']
        self.a1 = self.robot_settings['time_constant_motor']
        self.b0_f = self.robot_settings['v_gain_static_f']
        self.b0_b = self.robot_settings['v_gain_static_b']
        self.c0 = self.robot_settings['psi_dot_gain_static']
        self.pos_ref = self.robot_settings['pos_ref']

        # Kalman filter and measurements
        self.Q_kalman = np.array([[0.00075877, 0],
                      [0, 0.0190076]])
        self.R_kalman = np.array([[6e-9, 0, 0],
                      [0, 6e-9, 0],
                      [0, 0, 3.16e-8]])
        self.kalman_cov = np.eye(3)
        self.old_opti_meas = np.asarray([0.0, 0.0, 0.0])
        self.new_opti_meas = np.asarray([0.0, 0.0, 0.0])

        # Flags
        self.flag_include_integral = 1
        self.flag_pose = 0

    def testCommand(self, a: float, b: float):
        print(f"The sum is {a+b}")

    def getCurrentOrientation(self, pos, rot):
        self.old_opti_meas = self.new_opti_meas
        self.new_opti_meas = np.array([pos[0], pos[1], rot[2]])
        #print(f'OLD MEASUREMENT {self.old_opti_meas}')
        #print(f'NEW MEASUREMENT {self.new_opti_meas}')

        if np.all(self.old_opti_meas == self.new_opti_meas):
            self.flag_pose = 0
        else:
            self.flag_pose = 1

    def getObstacles(self, obstacles):
        self.obstacles = obstacles

    def getTargetPosition(self, pos_ref):
        self.pos_ref = np.array([pos_ref[0], pos_ref[1]])
    # ==================================================================================================================
    def init(self):
        self.board.init()
        self.communication.init()
        self.control.init()

    def start(self):
        self.board.start()
        self.communication.start()
        self.control.start()
        self.control.setStateFeedbackGain(self.robot_settings['balancing_gain'])
        print("START TWIPR ...")

        self._thread.start()

    # ==================================================================================================================
    def _threadFunction(self):

        # TODO: This is just for testing purposes. This should be divided somewhere else. Also the update time should
        #  be fixed and not by a time.sleep
        while True:
            self._update()

            # Update state
            #self.kalmanFilter()
            self.simpleEst()

            # Calculate control input
            u = np.asarray(self._calcFormCtrlInput(pos_ref=self.pos_ref))
            u[0] = np.clip(u[0], -0.02, 0.02)
            u[1] = np.clip(u[1], -0.02, 0.02)
            u_safe = np.asarray(self._calcSafeInput(u))
            #u_safe = u_safe + 0.1*(u-u_safe)
            if (np.abs(u_safe[0]) > 0.04 and np.abs(u[0]) < 0.04) or (np.abs(u_safe[1]) > 0.04 and np.abs(u[1]) < 0.04):
                u_safe = [0, 0]
            #u_safe[0] = np.clip(u_safe[0], -0.05, 0.05)
            #u_safe[1] = np.clip(u_safe[1], -0.05, 0.05)
            self.control.setInput([-u_safe[0] - self.flag_include_integral*self.integral[0] + self.u_offset[0],
                                   -u_safe[1] - self.flag_include_integral*self.integral[1] + self.u_offset[1]])

            #self.control.setInput([-u[0] + self.u_offset[0], -u[1] + self.u_offset[1]])
            #self.control.setInput([0.0044, 0.0044])
            #self.control.setInput([0.01 + self.u_offset[0], 0.01 + self.u_offset[1]])
            #print(self.estimation.getSample().state.v)
            #self.control.setInput([0.03 + self.u_offset[0], -0.03 + self.u_offset[1]])
            #print(self.estimation.getSample().state.psi_dot)

            #print(f"pos: {self.pos}")
            #print(u_safe)

            time.sleep(self.Ts)

    def _update(self):
        sample = self._buildSample()

        if self.communication.wifi.connected:
            self.communication.wifi.sendStream(sample)

    # ------------------------------------------------------------------------------------------------------------------
    # TODO: Should probably be somewhere else
    def _buildSample(self):
        sample = TWIPR_Sample()

        sample.general.id = self.robot_settings['id']
        sample.general.status = 0
        sample.general.configuration = ''
        sample.general.time = self.communication.wifi.getTime()
        sample.general.tick = 0
        sample.general.sample_time = 0.1
        sample.general.opti_track = self.flag_pose == 1

        sample.control = self.control.getSample()
        sample.estimation = self.estimation.getSample()
        sample.drive = self.drive.getSample()
        sample.sensors = self.sensors.getSample()

        sample.consensus.target_pos_ref_x = self.pos_ref[0].item()
        sample.consensus.target_pos_ref_y = self.pos_ref[1].item()
        sample.consensus.dist_from_ref = np.linalg.norm(self.pos_ref - self.pos)

        return sample

    def noEst(self):
        self.pos = self.new_opti_meas[0:2]
        self.rot[2] = self.new_opti_meas[2]
    
    def simpleEst(self):
        if self.flag_pose:
            self.pos = self.new_opti_meas[0:2]
            self.rot[2] = self.new_opti_meas[2]
        else:
            v = self.estimation.getSample().state.v
            psi_dot = self.estimation.getSample().state.psi_dot
            self.pos[0] = self.pos[0] + self.Ts * np.cos(self.rot[2])*v
            self.pos[1] = self.pos[1] + self.Ts * np.sin(self.rot[2])*v
            self.rot[2] = self.rot[2] + self.Ts * psi_dot

    def kalmanFilter(self):
        x_meas = self.new_opti_meas[0] # get value of x-measurement from server
        y_meas = self.new_opti_meas[1] # get value of y-measurement from server
        v = self.estimation.getSample().state.v
        psi_meas = self.new_opti_meas[2] # get value of psi-measurement from server
        psi_dot = self.estimation.getSample().state.psi_dot

        A = self.Ts * np.array([[np.cos(self.rot[2]), 0],
                           [np.sin(self.rot[2]), 0],
                           [0, 1]])

        state_pred = np.array([self.pos[0], self.pos[1], self.rot[2]]) + A @ np.array([v, psi_dot])

        F_k = np.array([[1, 0, -self.Ts*v*np.sin(self.rot[2])], # Linearized motion model
                        [0, 1, self.Ts*v*np.cos(self.rot[2])],
                        [0, 0, 1]])
        H_k = np.eye(3) # linearized measurement model

        cov_input = A @ self.Q_kalman @ A.T # linearized prediction of input covariance
        cov_pred = F_k @ self.kalman_cov @ F_k.T + cov_input

        ''' Correction Step '''
        if self.flag_pose:
            kalman_gain = cov_pred @ H_k.T @ np.linalg.inv(H_k @ cov_pred @ H_k.T + self.R_kalman)
            self.kalman_cov = (np.eye(3) - kalman_gain @ H_k) @ cov_pred
            kalman_est = state_pred + kalman_gain @ (np.array([x_meas, y_meas, psi_meas]).T - state_pred)
            #print(f'MEASUREMENT')
        else:
            self.kalman_cov = cov_pred
            kalman_est = state_pred
            #print(f'NO MEASUREMENT')
        #print(f'kalman: {kalman_est}')
        kalman_est[2] = (kalman_est[2] + np.pi) % (2 * np.pi) - np.pi # wrap angle so it stay in [-pi,pi]
        self.pos = kalman_est[0:2]
        self.rot[2] = kalman_est[2]


    def _calcFormCtrlInput(self, pos_ref):
        v = self.estimation.getSample().state.v
        a1 = self.a1
        if v >= 0:
            b0 = self.b0_f
        else:
            b0 = self.b0_b

        pole = 1.5
        #c0 = 1/1.1**2*a1/b0
        #c1 = (2/1.1*a1-1)/b0
        c0 = pole**2*a1/(2*b0)
        c1 = (2*pole*a1-1)/(2*b0)

        psi_dot = self.estimation.getSample().state.psi_dot
        psi = self.rot[2]
        theta = math.atan2(pos_ref[1]-self.pos[1], pos_ref[0]-self.pos[0])
        v_ref = c0 * math.sqrt((pos_ref[0]-self.pos[0]) ** 2 + (pos_ref[1]-self.pos[1]) ** 2) * math.cos(theta - psi) - c1 * v
        #v_ref = 0.025 * math.sqrt((pos_ref[0] - self.pos[0]) ** 2 + (pos_ref[1] - self.pos[1]) ** 2) * math.cos(
            #theta - psi) - 0.01 * v

        mod = 1
        if math.cos(theta - psi) < 0:
            mod = -1

        psi_dot_ref = 0.02 * math.sin(theta - psi) * mod - 0*0.01*psi_dot

        u1 = 1/2*(v_ref + psi_dot_ref)
        u2 = 1/2*(v_ref - psi_dot_ref)
        """
        print(f'pos: {self.pos}')
        print(f'theta: {theta}')
        print(f'psi: {psi}')
        print(f'u: {[u1, u2]}')
        print(f'v: {v}')
        """
        return [u1, u2]

    def _calcSafeInput(self, u):
        if self.obstacles:
            v = self.estimation.getSample().state.v
            a1 = self.a1
            c0 = self.c0
            if v >= 0:
                b0 = self.b0_f
            else:
                b0 = self.b0_b

            u = np.asarray(u)
            a = b0 / a1 * (u[0] + u[1]) - 1 / a1 * v
            psi = self.rot[2]
            psi_dot = self.estimation.getSample().state.psi_dot
            p = np.asarray(self.pos)
            p_dot = v * np.transpose(np.asarray([math.cos(psi), math.sin(psi)]))
            p_ddot = (a * np.transpose(np.asarray([np.cos(psi), np.sin(psi)])) +
                      v * psi_dot * np.transpose([-np.sin(psi), np.cos(psi)]))
            psi_dot_ref = u[0] - u[1]

            U = 0
            r = np.asarray([0.0, 0.0]).T
            r_dot = np.asarray([0.0, 0.0]).T
            for obstacle in self.obstacles.keys():
                if obstacle == self.robot_settings['id']:
                    continue
                q = np.asarray(self.obstacles[obstacle]['pos']).T

                U += 2/((p-q).T@(p-q))
                r += 4*(p-q) / (((p-q).T@(p-q))**2)
                r_dot += 4*p_dot/(((p-q).T@(p-q))**2) - 16*(p-q) * (p_dot.T@(p-q))/(((p-q).T@(p-q))**3)

            l = -0.2*np.sign(np.asarray([np.cos(psi), np.sin(psi)])@r)
            p_tilde = p + l*np.asarray([np.cos(psi), np.sin(psi)]).T
            p_tilde_dot = p_dot + l*psi_dot*np.asarray([-np.sin(psi), np.cos(psi)]).T
            p_tilde_ddot = (p_ddot + l*psi_dot_ref*np.asarray([-np.sin(psi), np.cos(psi)]).T
                            - l*psi_dot**2*np.asarray([np.cos(psi), np.sin(psi)]).T)

            delta_s = .4
            alpha = 1
            h = 1 / U - 1/2*delta_s ** 2 + 1/U**2 * p_tilde_dot.T@r
            lg_h = np.asarray([1/(U**2)*b0/a1*(np.asarray([np.cos(psi), np.sin(psi)]))@r,
                               l*1/U**2 * c0/a1 * np.asarray([-np.sin(psi), np.cos(psi)]).T@r])
            lambda_val = np.max([0, -(alpha*h + 1/(U**2)*p_dot.T@r + 2/(U**3)*((p_dot.T@r)*(p_tilde_dot@r)) +
                                      1/(U**2)*(p_tilde_ddot.T@r + p_tilde_dot.T@r_dot))/(1/4*lg_h[0]**2 + lg_h[1]**2)])

            u[0] = u[0] + 1/4*1/2 * lambda_val*lg_h[0] + 1/2 * lambda_val*lg_h[1]
            u[1] = u[1] + 1/4*1/2 * lambda_val*lg_h[0] - 1/2 * lambda_val*lg_h[1]

            if (np.abs(u[0]) >= 0.001 or np.abs(u[1]) >= 0.001) and self.control.mode == 2 and lambda_val == 0:
                self.integral[0] += self.K_i*u[0]*self.Ts
                self.integral[1] += self.K_i*u[1]*self.Ts
                self.flag_include_integral = 1
            #elif lambda_val > 0:
                #self.flag_include_integral = 0
            elif self.control.mode == 0:
                self.integral = [0, 0]
            '''
            print(f'mode: {self.control.mode}')
            print(f'p_dot: {p_dot}')
            print(f'psi_dot: {psi_dot}')
            print(f'a: {a}')
            print(f'U: {U}')
            print(f'h: {h}')
            print(f'Lg_h: {lg_h}')
            print(f'lambda: {lambda_val}')
            print(f'u: {u}')
            print(f'integral: {self.integral}')
            print(f'(p-q)^2: {p.T@p}')
            print(f'U: {U}')
            print(f'r: {r}')
            print(f'pos: {p}')
            print(f'v: {v}')
            '''
        return u

    def _calcSafeInput2(self, u):
        if self.obstacles:
            v = self.estimation.getSample().state.v
            a1 = self.a1
            c0 = self.c0
            if v >= 0:
                b0 = self.b0_f
            else:
                b0 = self.b0_b

            u = np.asarray(u)
            a = b0 / a1 * (u[0] + u[1]) - 1 / a1 * v
            psi = self.rot[2]
            psi_dot = self.estimation.getSample().state.psi_dot
            p = np.asarray(self.pos)
            p_dot = v * np.transpose(np.asarray([math.cos(psi), math.sin(psi)]))
            p_ddot = (a * np.transpose(np.asarray([np.cos(psi), np.sin(psi)])) +
                      v * psi_dot * np.transpose([-np.sin(psi), np.cos(psi)]))
            psi_dot_ref = u[0] - u[1]

            l = 0.1
            p_tilde = p + l * np.asarray([np.cos(psi), np.sin(psi)]).T
            p_tilde_dot = p_dot + l * psi_dot * np.asarray([-np.sin(psi), np.cos(psi)]).T
            p_tilde_ddot = (p_ddot + l * psi_dot_ref * np.asarray([-np.sin(psi), np.cos(psi)]).T
                            - l * psi_dot ** 2 * np.asarray([np.cos(psi), np.sin(psi)]).T)

            U = 0
            r = np.asarray([0.0, 0.0]).T
            r_dot = np.asarray([0.0, 0.0]).T
            for obstacle in self.obstacles.keys():
                if obstacle == self.robot_settings['id']:
                    continue
                q = np.asarray(self.obstacles[obstacle]['pos']).T

                U += 2/((p_tilde-q).T@(p_tilde-q))
                r += 4*(p_tilde-q) / (((p_tilde-q).T@(p_tilde-q))**2)
                r_dot += 4*p_tilde_dot/(((p_tilde-q).T@(p_tilde-q))**2) - 16*(p_tilde-q) * (p_tilde_dot.T@(p_tilde-q))/(((p_tilde-q).T@(p_tilde-q))**3)

            delta_s = .4
            alpha = 1
            h = 1 / U - 1/2*delta_s ** 2 + 1/U**2 * p_tilde_dot.T@r
            lg_h = np.asarray([1/(U**2)*b0/a1*(np.asarray([np.cos(psi), np.sin(psi)]))@r,
                               l*1/U**2 * c0/a1 * np.asarray([-np.sin(psi), np.cos(psi)]).T@r])
            lambda_val = np.max([0, -(alpha*h + 1/(U**2)*p_tilde_dot.T@r + 2/(U**3)*((p_tilde_dot.T@r)*(p_tilde_dot@r)) +
                                      1/(U**2)*(p_tilde_ddot.T@r + p_tilde_dot.T@r_dot))/(1/4*lg_h[0]**2 + lg_h[1]**2)])

            u[0] = u[0] + 1/4*1/2 * lambda_val*lg_h[0] + 1/2 * lambda_val*lg_h[1]
            u[1] = u[1] + 1/4*1/2 * lambda_val*lg_h[0] - 1/2 * lambda_val*lg_h[1]

            if (np.abs(u[0]) >= 0.001 or np.abs(u[1]) >= 0.001) and self.control.mode == 2 and lambda_val == 0:
                self.integral[0] += self.K_i*u[0]*self.Ts
                self.integral[1] += self.K_i*u[1]*self.Ts
                self.flag_include_integral = 1
            #elif lambda_val > 0:
                #self.flag_include_integral = 0
            elif self.control.mode == 0:
                self.integral = [0, 0]
            '''
            print(f'mode: {self.control.mode}')
            print(f'p_dot: {p_dot}')
            print(f'psi_dot: {psi_dot}')
            print(f'a: {a}')
            print(f'U: {U}')
            print(f'h: {h}')
            print(f'Lg_h: {lg_h}')
            print(f'lambda: {lambda_val}')
            print(f'u: {u}')
            print(f'integral: {self.integral}')
            print(f'(p-q)^2: {p.T@p}')
            print(f'U: {U}')
            print(f'r: {r}')
            print(f'pos: {p}')
            print(f'v: {v}')
            '''
        return u
