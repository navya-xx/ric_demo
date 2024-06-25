import math

from applications.ric_demo.simulation.scioi_pysim.scioi_py_core.objects.twipr.EnvironmentTWIPR_objects import \
    TWIPR_Agent, TWIPR_DynamicAgent
from applications.ric_demo.simulation.scioi_pysim.scioi_py_core.objects.twipr.environment_base import EnvironmentBase
from applications.ric_demo.simulation.scioi_pysim.scioi_py_core.objects.world.grid import Grid2D


class Environment_RIC(EnvironmentBase):
    real_agents: dict
    virtual_agents: dict

    floor: Grid2D

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.virtual_agents = {}
        self.real_agents = {}
        # self.agent1 = TWIPR_DynamicAgent(agent_id='twipr1', name='Agent 1', world=self.world, speed_control=False)
        # self.virtual_agents['twipr1'] = self.agent1

        self.floor = Grid2D(self.world, cell_size=0.5, cells_x=10, cells_y=10, origin=[0, 0])

    # ------------------------------------------------------------------------------------------------------------------
    def addRealAgent(self, agent_id):
        self.real_agents[agent_id] = TWIPR_Agent(agent_id=agent_id, name=agent_id, world=self.world,
                                                 speed_control=False)
        ...

    # ------------------------------------------------------------------------------------------------------------------
    def removeRealAgent(self, agent_id):
        self.world.removeObject(self.real_agents[agent_id])
        self.real_agents.pop(agent_id)
        # TODO: Add message to Babylon to remove the agent
        ...

    # ------------------------------------------------------------------------------------------------------------------
    def addVirtualAgent(self, agent_id):
        self.virtual_agents[agent_id] = TWIPR_DynamicAgent(agent_id=agent_id, name=agent_id, world=self.world,
                                                           speed_control=False)
        self.virtual_agents[agent_id].scheduling.actions['dynamics'].registerAction(
            self.virtual_agents[agent_id].dynamics.scheduling.actions['update']
        )
        self.world.scheduling.actions['dynamics'].registerAction(self.virtual_agents[agent_id].scheduling.actions['dynamics'])
        self.scheduling.actions['controller'].registerAction(self.virtual_agents[agent_id].scheduling.actions['logic'])

    # ------------------------------------------------------------------------------------------------------------------
    def removeVirtualAgent(self, agent_id):
        self.world.removeObject(self.virtual_agents[agent_id])
        self.virtual_agents.pop(agent_id)
        # TODO: Add message to Babylon to remove the agent

    # ------------------------------------------------------------------------------------------------------------------
    # def action_input(self, *args, **kwargs):
    #     super().action_input(*args, **kwargs)
    #
    # def action_controller(self, *args, **kwargs):
    #     super().action_controller(*args, **kwargs)
    #     pass
    #
    # def action_output(self, *args, **kwargs):
    #     super().action_output(*args, **kwargs)
