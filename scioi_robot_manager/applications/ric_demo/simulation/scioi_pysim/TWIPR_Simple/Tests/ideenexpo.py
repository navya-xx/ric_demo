import math

from applications.ric_demo.simulation.scioi_pysim.scioi_py_core.objects.twipr.EnvironmentTWIPR_objects import TWIPR_Agent
from applications.ric_demo.simulation.scioi_pysim.scioi_py_core.objects.twipr.environment_base import EnvironmentBase
from applications.ric_demo.simulation.scioi_pysim.scioi_py_core.objects.world.grid import Grid2D


class Environment_IdeenExpo(EnvironmentBase):
    agent1: TWIPR_Agent

    # obstacle1: CuboidObstacle_3D
    # keys: ArrowKeys

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.agent1 = TWIPR_Agent(agent_id=1, name='Agent 1', world=self.world, speed_control=True)
        self.agent2 = TWIPR_Agent(agent_id=2, name='Agent 2', world=self.world, speed_control=True)
        self.agent3 = TWIPR_Agent(agent_id=3, name='Agent 3', world=self.world, speed_control=True)

        self.agent2.setPosition(x=1, y=0)
        self.agent3.setPosition(x=-1, y=0.75)
        self.agent2.setConfiguration(dimension='psi', value=math.pi/2)

    def action_input(self, *args, **kwargs):
        super().action_input(*args, **kwargs)

    def action_controller(self, *args, **kwargs):
        super().action_controller(*args, **kwargs)
        pass


def main():
    env = Environment_IdeenExpo(visualization='babylon', webapp_config={'title': ''})
    floor = Grid2D(env.world, cell_size=0.285, cells_x=10, cells_y=10, origin=[0, 0])

    env.init()
    env.start()


# TODO: Implement the translate and rotate functions. Also make some objects fixed so that changing
#  any in their config gives an error

if __name__ == '__main__':
    main()
