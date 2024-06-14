import time

from applications.ideenexpo.src.ideenexpo_manager import IdeenExpoManager


def main():
    manager = IdeenExpoManager()
    manager.init()
    manager.start()

    while True:
        time.sleep(1)


if __name__ == '__main__':
    main()