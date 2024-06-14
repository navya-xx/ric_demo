import time

import numpy as np

from optitrack import Optitrack


def main():
    op = Optitrack(None)
    op.start()

    while True:
        print(f"Position: {op.bodies['1']['position']}, Psi: {np.rad2deg(op.bodies['1']['psi'])}")
        time.sleep(0.1)


if __name__ == '__main__':
    main()
