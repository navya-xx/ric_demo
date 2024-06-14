import time

from extensions.optitrack.optitrack import OptiTrack


def example_optitrack():
    optitrack = OptiTrack()
    optitrack.start()

    while True:
        time.sleep(1)


if __name__ == '__main__':
    example_optitrack()
