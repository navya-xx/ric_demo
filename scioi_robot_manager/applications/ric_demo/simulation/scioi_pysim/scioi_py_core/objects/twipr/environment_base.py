from applications.ric_demo.simulation.scioi_pysim.scioi_py_core import core as core

from applications.ric_demo.simulation.scioi_pysim.scioi_py_core.objects.twipr import EnvironmentTWIPR_objects
from applications.ric_demo.simulation.scioi_pysim.scioi_py_core.visualization.babylon_new.babylon import BabylonVisualization

from applications.ric_demo.simulation.scioi_pysim.scioi_py_core.utils.babylon import setBabylonSettings


class EnvironmentBase(core.environment.Environment):
    babylon: (BabylonVisualization, None)
    world: EnvironmentTWIPR_objects.DynamicWorld_XYZR_Simple
    run_mode = 'rt'
    Ts = 0.02
    name = 'environment'

    def __init__(self, visualization=None, show_visualization=True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.world = EnvironmentTWIPR_objects.DynamicWorld_XYZR_Simple(name='world', parent=self)

        if visualization == 'babylon':
            self.visualization = BabylonVisualization()

        # Actions
        core.scheduling.Action(name='input', object=self, priority=0, parent=self.action_step,
                               function=self.action_input)
        core.scheduling.Action(name='controller', object=self, priority=1, parent=self.action_step,
                               function=self.action_controller)
        core.scheduling.Action(name='world', object=self, function=self.action_world, priority=2,
                               parent=self.action_step)

        core.scheduling.Action(name='visualization', object=self, priority=3, parent=self.action_step,
                               function=self.action_visualization)
        core.scheduling.Action(name='output', object=self, priority=4, parent=self.action_step,
                               function=self.action_output)

        core.scheduling.registerActions(self.world, self.scheduling.actions['world'])

    # === ACTIONS ======================================================================================================
    def _init(self, *args, **kwargs):
        ...
        # Set the world configuration in the babylon visualization if needed
        if self.visualization is not None:
            self.visualization.setWorldConfig(self.world.generateWorldConfig())
            self.visualization.start()
            setBabylonSettings(status='')

    def _action_entry(self, *args, **kwargs):
        super()._action_entry(*args, **kwargs)

    def _action_step(self, *args, **kwargs):
        pass

    def action_input(self, *args, **kwargs):
        pass

    def action_controller(self, *args, **kwargs):
        pass

    def action_visualization(self, *args, **kwargs):
        pass

    def action_output(self, *args, **kwargs):
        pass

    def action_world(self, *args, **kwargs):
        pass
