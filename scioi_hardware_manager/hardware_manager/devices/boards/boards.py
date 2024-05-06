import dataclasses
import hardware_manager.utils.utils as utils


@dataclasses.dataclass
class BoardCommunication:
    dev: dict = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class BoardHardware:
    rev: str


@dataclasses.dataclass
class BoardSoftware:
    rev: str
    firmware: str


class Board:
    com: BoardCommunication
    hardware: BoardHardware
    software: BoardSoftware
    name: str
    uid: list
    callbacks: dict[str, list[utils.Callback]]

    # === INIT =========================================================================================================
    def __init__(self):

        self.callbacks = {}

    # === METHODS ======================================================================================================
    def registerCallback(self, callback_id, function: callable, parameters: dict = None, lambdas: dict = None):
        callback = utils.Callback(function, parameters, lambdas)

        if callback_id in self.callbacks:
            self.callbacks[callback_id].append(callback)
        else:
            raise Exception("Invalid Callback type")
