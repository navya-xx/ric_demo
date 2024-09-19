import logging
import time

import archive.cm4_core_old2.communication.wifi.core.tcp_socket as tcp

from archive.cm4_core_old2.communication.wifi.protocols.tcp_json_protocol import TCP_JSONProtocol, TCP_JSONMessage

logging.basicConfig(level=logging.INFO)


def main():
    print("Starting Communication")
    ip = tcp.getHostIP(timeout=5)

    sock = tcp.TCP_Socket(server_address=ip, server_port=6666)
    sock.start()

    time.sleep(1)

    msg = TCP_JSONMessage
    msg.src = [2, 3]
    msg.add = [1, 2]
    msg.data = {'a': 1, 'b': "zwei", 'c': [1, 2, 3]}
    data = TCP_JSONProtocol.encode(msg, base_encode=True)

    sock.send(data)

    time.sleep(1)
    sock.close()


if __name__ == "__main__":
    main()
