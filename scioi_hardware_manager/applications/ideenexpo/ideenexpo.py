import threading

from applications.robot_manager import RobotManager


class IdeenExpo:
    robotManager: RobotManager
    gui: GUI
    simulation: BackgroundSimulation

    _thread: threading.Thread

    def __init__(self):
        ...
