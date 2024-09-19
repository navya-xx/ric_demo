import logging
import time

import archive.cm4_core_old2.communication.wifi.core.tcp_socket as tcp

logging.basicConfig(level=logging.INFO)


def main():
    print("Starting Communication")
    ip = tcp.getHostIP(timeout=5)

    sock = tcp.TCP_Socket(server_address=ip, server_port=6666)
    sock.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        sock.close()


if __name__ == "__main__":
    main()
