import logging
import time

import archive.cm4_core_old2.communication.wifi.core.tcp_socket as tcp

from archive.cm4_core_old2.communication.wifi.protocols.tcp_protocol import TCP_Message
from archive.cm4_core_old2.communication.wifi.protocols.tcp_handshake import TCP_DeviceHandshakeProtocol, TCP_DeviceHandshakeMessage

logging.basicConfig(level=logging.INFO)


def main():
    print("Starting Communication")
    ip = tcp.getHostIP(timeout=5)

    sock = tcp.TCP_Socket(server_address=ip, server_port=6666)
    sock.start()

    time.sleep(1)

    msg = TCP_DeviceHandshakeMessage()
    msg.address = [1, 0, 0, 4]
    msg.protocols = [2, 3]
    msg.name = "robot-control_01"
    handshake_data = msg.encode()

    tcpmsg = TCP_Message()
    tcpmsg.src = [0, 0]
    tcpmsg.add = [0, 0]
    tcpmsg.data_protocol_id = TCP_DeviceHandshakeProtocol.protocol_identifier
    tcpmsg.data = handshake_data

    sock.send(tcpmsg.encode())

    time.sleep(1)
    sock.close()


if __name__ == "__main__":
    main()
