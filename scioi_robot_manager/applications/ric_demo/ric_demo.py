import threading

from applications.ric_demo.robots.ric_demo_manager import RIC_Demo_RobotManager
from applications.ric_demo.simulation.ric_demo_simulation import RIC_Demo_Simulation
from applications.ric_demo.consensus.ric_consensus import ConsensusTWIPR, Consensus


class RIC_Demo:
    mode: str
    ric_robot_manager: RIC_Demo_RobotManager
    simulation: RIC_Demo_Simulation
    optitrack: ...
    gui: ...
    consensus: Consensus

    _thread: threading.Thread

    def __init__(self):


        ...

        self.ric_robot_manager.robotManager.registerCallback('stream', self._streamCallback)

        ctwipr1 = ConsensusTWIPR(id='twipr1')
        ctwipr1.input_callback = self.consensusinputcallback
        self.consensus.addAgent(ctwipr1)

    def consensusinputcallback(self, agent_id, input):
        ...

