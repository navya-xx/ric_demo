import time

from applications.ideenexpo.src.twipr_manager import TWIPR_Manager


def main():
    manager = TWIPR_Manager(optitrack=True)

    manager.init()
    manager.start()

    while True:
        time.sleep(1)


if __name__ == '__main__':
    main()
