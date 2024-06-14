import time

from extensions.gui.nodejs_gui.nodejs_gui import NodeJSGui


def install():
    gui = NodeJSGui()
    gui.install()

    time.sleep(20)


if __name__ == '__main__':
    install()
    