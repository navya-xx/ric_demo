import logging
import time
import numpy as np

import archive.cm4_core_old2.communication.wifi.tcp_client as tcp

logging.basicConfig(level=logging.INFO)


def main():
    print("Starting Communication")
    ip = tcp.getHostIP(timeout=5)

    sock = tcp.TCP_Socket(server_address=ip, server_port=6666)
    sock.start()

    time.sleep(1)
    for i in range(0, 10):
        x = np.random.randint(0, 8, 10, dtype=np.uint8)
        data = bytes(x)
        sock.send(data)
        time.sleep(1)

    try:
        while True:
            pass
    except KeyboardInterrupt:
        sock.close()


if __name__ == "__main__":
    main()
