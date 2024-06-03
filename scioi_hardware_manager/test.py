import time

import natnetclient

import natnetclient as natnet


def main():
    client = natnet.NatClient(client_ip='192.168.0.100', data_port=1511, comm_port=1510)


    while True:
        time.sleep(1)


if __name__ == '__main__':
    main()
