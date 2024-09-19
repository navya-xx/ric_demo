from datetime import datetime


class Callback:
    fun: callable

    def __init__(self, fun, *args, **kwargs):
        self.fun = fun
        self.args = args
        self.kwargs = kwargs

    def __call__(self, *args, **kwargs):
        kw = {**self.kwargs, **kwargs}
        self.fun(*args, **kw)


def bytes_to_string(data, pos=False):
    if pos:
        return " ".join("0x{:02X}({:d})".format(b, i) for (i, b) in enumerate(data))
    else:
        return " ".join("0x{:02X}".format(b) for b in data)


def timestr():
    dateTimeObj = datetime.now()
    timestampStr = dateTimeObj.strftime("%H:%M:%S.%f")[:-3]
    return timestampStr
