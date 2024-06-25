from applications.ric_demo.simulation.scioi_pysim.TWIPR_Simple.Environment.Environments.Environment_SingleTWIPR import Environment_SingleTWIPR, \
    Environment_SingleTWIPR_KeyboardInput
from applications.ric_demo.simulation.scioi_pysim.scioi_py_core.objects.world import floor
from applications.ric_demo.simulation.scioi_pysim.scioi_py_core.objects.world.grid import Grid2D
import applications.ric_demo.simulation.scioi_pysim.scioi_py_core.core as core


def main():
    env = Environment_SingleTWIPR_KeyboardInput(visualization='babylon', webapp_config={'title': 'This is a title'})
    floor = Grid2D(env.world, cell_size=0.5, cells_x=10, cells_y=10, origin=[0, 0])

    env.init()
    env.start()


# TODO: Implement the translate and rotate functions. Also make some objects fixed so that changing
#  any in their config gives an error

if __name__ == '__main__':
    main()
