def pos_control_cbf(self, centroid, obstacles=None, Ts=0.1):
    K_i = 2 * np.array([[0.0125, 0.006], [0.0125, -0.006]])
    # K_i = np.array([[0.06, 0.00495], [0.06, -0.00495]])
    delta_s = 0.5

    pos = np.array([self.state['x'], self.state['y']])
    pos_ref = centroid + np.array([self.formation_ref['x'], self.formation_ref['y']])
    if np.linalg.norm(pos - pos_ref) <= self.consensus_normalized_tol:
        print(f"Consensus is reached for agent {self.id}")
        self.is_consensus = True
        # return np.array([0.0, 0.0])

    psi = _wrap2Pi(self.state['psi'])  # self.state['psi']  #
    v_g = pos_ref - np.asarray(pos)

    temp_pos = np.array([[np.cos(psi), np.sin(psi)], [-np.sin(psi), np.cos(psi)]]) @ v_g.T
    theta = np.atan2(temp_pos[1], temp_pos[0]) + psi
    # print(theta - psi)

    u = 1
    if np.cos(theta - psi) < 0:
        u = -1

    v_ref = 0.3 * (np.linalg.norm(v_g) * np.cos(theta - psi))
    # v_ref = np.clip(v_ref, -0.1, 0.1)
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
        K_v = 1 / 100
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
    # control_input = np.clip(control_input, -0.05, 0.05)
    print(f"abs(V_ref - v) of {self.id} = {np.abs(v_ref - v)}")
    return control_input


def pos_control_cbf(self, centroid, obstacles=None, Ts=0.1):

    K_i = 2 * np.array([[0.0125, 0.006], [0.0125, -0.006]])
    # K_i = np.array([[0.06, 0.00495], [0.06, -0.00495]])
    delta_s = 0.1

    pos = np.array([self.state['x'], self.state['y']])
    pos_ref = centroid + np.array([self.formation_ref['x'], self.formation_ref['y']])
    if np.linalg.norm(pos - pos_ref) <= self.consensus_normalized_tol:
        # print(f"Consensus is reached for agent {self.id}")
        self.is_consensus = True
        # return np.array([0.0, 0.0])

    psi = _wrap2Pi(self.state['psi'])  # self.state['psi']  #
    v_g = pos_ref - np.asarray(pos)

    temp_pos = np.array([[np.cos(psi), np.sin(psi)], [-np.sin(psi), np.cos(psi)]]) @ v_g.T
    theta = np.atan2(temp_pos[1], temp_pos[0]) + psi
    # print(theta - psi)

    u = 1
    if np.cos(theta - psi) < 0:
        u = -1

    v_ref = 0.3 * (np.linalg.norm(v_g) * np.cos(theta - psi))
    # v_ref = np.clip(v_ref, -0.1, 0.1)
    psi_dot_ref = (0.8 * np.sin(theta - psi) * u)

    v = self.state['v']
    psi_dot = self.state['psi_dot']

    ## provisional
    # if np.sign(v_ref) != np.sign(v) and np.abs(v_ref - v) > 0.1:
    #    v_ref = 0
    ##
    found_obstacle = False
    min_dist = 5
    if obstacles is not None:
        ## Very simple collision avoidance
        # if agent is close to an obstacle, it will slow down and keep moving away in random direction
        # slowdown starts when agent are at a distance delta_s
        # moving away starts at distance delta_s / 3
        for obs_id, obstacle in obstacles.items():
            if obs_id != self.id and obs_id.startswith('twipr'):
                dist_obs = np.linalg.norm(pos - obstacle)
                if dist_obs < min_dist:
                    min_dist = dist_obs
        if min_dist < delta_s:
            found_obstacle = True

    if np.abs(v_ref - v) > 0.02:
        if found_obstacle:
            # move in opposite direction
            # self.resetIntegrator()
            print(f"Found Obstacle -- Integrators = {self.state['v_integral']}, {self.state['psi_dot_integral']}")
            v_ref -= np.minimum(1.0, 0.2 * delta_s / min_dist)
            psi_dot_ref -= np.random.uniform(0.0, np.pi/2)

        self.state['v_integral'] += (v_ref - v) * Ts
        self.state['psi_dot_integral'] += (psi_dot_ref - psi_dot) * Ts
    else:
        self.resetIntegrator()

    control_input = - K_i @ np.array([self.state['v_integral'], self.state['psi_dot_integral']]).T
    # clip
    # control_input = np.clip(control_input, -0.05, 0.05)
    # print(f"abs(V_ref - v) of {self.id} = {np.abs(v_ref - v)}")
    return control_input