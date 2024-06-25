from applications.TWIPR_Simple.Environment.Environments.Environment_SingleTWIPR import Environment_SingleTWIPR, Environment_SingleTWIPR_KeyboardInput
from applications.ric_demo.simulation.scioi_pysim.scioi_py_core.objects.world import floor
from applications.ric_demo.simulation.scioi_pysim.scioi_py_core.objects.world.grid import Grid2D
import applications.ric_demo.simulation.scioi_pysim.scioi_py_core.core as core


def main():
    env = Environment_SingleTWIPR_KeyboardInput(visualization='babylon', webapp_config={'title': 'This is a title'})
    cell_size = 0.5
    thickness = 0.03
    height = 0.15
    floor = Grid2D(env.world, cell_size=cell_size, cells_x=3, cells_y=1, origin=[0, 0])

    group1 = core.world.WorldObjectGroup(name='Gate', world=env.world, local_space=core.spaces.Space3D())
    group_object1 = core.obstacles.CuboidObstacle_3D(group=group1, size_x=thickness, size_y=thickness, size_z=height,
                                                     position=[0, cell_size/2-thickness/2, height/2])
    group_object2 = core.obstacles.CuboidObstacle_3D(group=group1, size_x=thickness, size_y=thickness, size_z=height,
                                                     position=[0, -(cell_size/2-thickness/2),height/2])
    group_object1 = core.obstacles.CuboidObstacle_3D(group=group1, size_x=thickness, size_y=cell_size, size_z=thickness,
                                                     position=[0, 0, height])


    env.agent1.setPosition(x=-0.5)
    # env.agent2.setPosition(x=0.5)


    env.init()
    env.start()




# TODO: Implement the translate and rotate functions. Also make some objects fixed so that changing
#  any in their config gives an error

if __name__ == '__main__':
    main()
