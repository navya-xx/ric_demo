import time


# ======================================================================================================================
def getFromDict(dict, key, default=None):
    if hasattr(dict, key):
        return dict[key]
    else:
        return default


# ======================================================================================================================
class Callback:
    parameters: dict
    lambdas: dict
    function: callable

    def __init__(self, function: callable, parameters: dict = None, lambdas: dict = None):
        self.function = function

        if parameters is None:
            parameters = {}
        self.parameters = parameters

        if lambdas is None:
            lambdas = {}
        self.lambdas = lambdas

    def __call__(self, *args, **kwargs):
        lambdas_exec = {key: value() for (key, value) in self.lambdas.items()}
        ret = self.function(*args, **{**self.parameters, **kwargs, **lambdas_exec})
        return ret


# ======================================================================================================================
def waitForKeyboardInterrupt():
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        ...
