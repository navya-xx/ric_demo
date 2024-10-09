import logging
import time

import cm4_core.communication.wifi.core.tcp as tcp
import cm4_core.communication.wifi.core.udp as udp
import cm4_core.utils.network as network
from cm4_core.communication.wifi.protocols.tcp_handshake_protocol import TCP_Handshake_Message, TCP_Handshake_Protocol
from cm4_core.communication.wifi.protocols.tcp_base_protocol import TCP_Base_Message
from cm4_core.communication.wifi.protocols.tcp_json_protocol import TCP_JSON_Protocol
import cm4_core.communication.wifi.addresses as uid

logging.basicConfig(level='DEBUG')


def example_simple_tcp_socket():
    server_address_known = False
    server_address: str = None
    server_port: int = None
    time2 = None
    time1 = None

    def udp_rx_callback(message: udp.UDP_Message):
        nonlocal server_port, server_address, server_address_known

        server_address, server_port = network.splitServerAddress(message.data.decode('utf-8'))
        logging.info(f"Received server info. Address = {server_address}, Port = {server_port}")
        server_address_known = True
        udp_socket.close()

    def tcp_rx_callback(*args, **kwargs):
        ...

    udp_socket = udp.UDP_Socket()
    udp_socket.registerCallback('rx', udp_rx_callback)
    udp_socket.start()

    while not server_address_known:
        time.sleep(1)

    tcp_socket = tcp.TCP_Socket(server_address=server_address, server_port=server_port)
    tcp_socket.start()

    while not tcp_socket.connected:
        time.sleep(1)

    tcp_socket.registerCallback('rx', tcp_rx_callback)

    handshake_message = TCP_Handshake_Message()
    handshake_message.protocols = [TCP_JSON_Protocol.identifier]
    handshake_message.name = "TEST"
    handshake_message.uid = [1, 2, 3, 4]

    data = handshake_message.encode()

    msg = TCP_Base_Message()
    msg.data = data
    msg.source = [0, 1]
    msg.address = uid.server
    msg.data_protocol_id = TCP_Handshake_Protocol.identifier
    x = msg.encode()
    tcp_socket.send(x)

    time.sleep(200)

    tcp_socket.close()


if __name__ == '__main__':
    example_simple_tcp_socket()
