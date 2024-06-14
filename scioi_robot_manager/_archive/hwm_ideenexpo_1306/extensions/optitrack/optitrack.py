import logging

from extensions.optitrack.lib.NatNetClient import NatNetClient


class OptiTrack:
    callbacks: dict
    natnetclient: NatNetClient

    def __init__(self, server_address, local_address, multicast_address):

        self.natnetclient = NatNetClient(server_address, local_address, multicast_address)

        self.natnetclient.rigidBodyListener = self._natnet_newRigidBodyFrame_callback
        self.natnetclient.newFrameListener = self._natnet_newFrame_callback

        self.callbacks = {
            'new_frame': []
        }

    # === METHODS ======================================================================================================
    def registerCallback(self, callback_id, callback):
        if callback_id in self.callbacks.keys():
            self.callbacks[callback_id].append(callback)
        else:
            raise Exception(f"TCP Device: No callback with id {callback_id} is known.")

    # ------------------------------------------------------------------------------------------------------------------
    def init(self):
        ...

    def start(self):
        self.natnetclient.run()
        ...

    # === PRIVATE METHODS ==============================================================================================
    def _natnet_newRigidBodyFrame_callback(self, id, position, rotation, *args, **kwargs):
        print(f"New rigid body frame with ID {id}")
        for callback in self.callbacks['new_frame']:
            callback(id, position, rotation)

    def _natnet_newFrame_callback(self, *args, **kwargs):
        pass
