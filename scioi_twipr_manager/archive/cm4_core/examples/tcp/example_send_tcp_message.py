import logging
import time

import archive.cm4_core_old2.communication.wifi.core.tcp_socket as tcp

from archive.cm4_core_old2.communication.wifi.protocols.tcp_protocol import TCP_Protocol, TCP_Message

logging.basicConfig(level=logging.INFO)


def main():
    print("Starting Communication")
    ip = tcp.getHostIP(timeout=5)

    sock = tcp.TCP_Socket(server_address=ip, server_port=6666)
    sock.start()

    time.sleep(1)

    msg = TCP_Message()
    msg.src = [0, 0]
    msg.add = [0, 0]
    msg._protocol = 4
    msg.data = [1, 2, 3, 4, 5]

    data = TCP_Protocol.encode(msg)

    sock.send(data)

    time.sleep(1)
    sock.close()


if __name__ == "__main__":
    main()
