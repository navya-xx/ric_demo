import threading
import time


class ConsensusTWIPR:
    state: dict
    id: str

    input_callback: callable

    def __init__(self, id):
        self.input_callback = None
        self.id = id

    def setInput(self, input):
        if self.input_callback is not None:
            self.input_callback(self.id, input)

    def consensus(self):
        ...


class Consensus:
    agents: dict[str, ConsensusTWIPR]

    thread: threading.Thread

    def __init__(self, agents):
        if agents is not None:
            self.agents = agents
        else:
            self.agents = {}
        ...

    def addAgent(self, id):
        ...

    def removeAgent(self, id):
        ...

    def _threadFunc(self):
        while True:

            for id, agent in self.agents.items():
                x = agent.state['x']

                ...

                agent.setInput([-0.1,-0.1])
                ...
            ...
            time.sleep(0.1)
