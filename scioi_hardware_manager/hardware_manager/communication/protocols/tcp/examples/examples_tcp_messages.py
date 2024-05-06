import logging

import hardware_manager.communication.protocols.tcp.tcp_base_protocol as tcp_base_protocol
import hardware_manager.communication.protocols.tcp.tcp_json_protocol as tcp_json_protocol
import hardware_manager.communication.protocols.tcp.tcp_handshake_protocol as tcp_handshake_protocol
from hardware_manager.utils.bytes import bytearray_to_string

logging.basicConfig(level=logging.DEBUG)


def example_raw_message():
    logging.info("Example Raw Protocol")
    msg = tcp_base_protocol.TCP_Base_Message()
    msg.data = [1, 2, 3, 4, 5]
    msg.src = [1, 2]
    msg.add = [3, 4]
    byte_msg = msg.encode()
    logging.info(bytearray_to_string(byte_msg))


def example_json_message():
    logging.info("Example JSON Protocol")
    data = {
        'value_1': 3,
        'value_2': [99, 87, -12, 0.123],
        'value_3': "this is a test",
    }

    msg = tcp_json_protocol.TCP_JSON_Message()
    msg.data = data
    byte_msg = msg.encode()
    logging.info(bytearray_to_string(byte_msg))

    # Revert the byte msg back to a normal message
    msg_recovered = tcp_json_protocol.TCP_JSON_Protocol.decode(byte_msg)


def example_handshake():
    logging.info("Example Handshake Protocol")
    msg = tcp_handshake_protocol.TCP_Handshake_Message()
    msg.protocols = [1, 2, 3]
    msg.address = [10, 11, 12, 13]
    msg.name = "ABCDEFGH"
    byte_msg = msg.encode()
    logging.info(bytearray_to_string(byte_msg))

    msg_recovered = tcp_handshake_protocol.TCP_Handshake_Protocol.decode(byte_msg)

    pass


if __name__ == '__main__':
    example_raw_message()
    example_json_message()
    example_handshake()
