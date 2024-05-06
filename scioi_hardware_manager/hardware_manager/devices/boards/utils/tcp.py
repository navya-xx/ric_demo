import hardware_manager.utils.utils as utils


class TCPMessageCallback:
    message_filter: list
    callback: utils.Callback

    def __init__(self, callback, message_filter):
        self.message_filter = message_filter
        self.callback = callback

    def __call__(self, *args, **kwargs):
        self.callback(*args, **kwargs)
