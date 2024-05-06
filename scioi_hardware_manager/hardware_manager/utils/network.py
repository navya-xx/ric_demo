import logging
import socket
import os
import subprocess
import sys


def getIP():
    """

    :param debug:
    :return:
    """
    if os.name == 'nt':

        hostname = socket.gethostname()
        server_address = socket.gethostbyname_ex(socket.gethostname())

        logging.debug('\t-------------')
        logging.debug("\tIP Tool")
        local_ip = None
        usb_ip = None
        for ip in server_address[2]:
            if ip.startswith("192."):
                local_ip = ip
            if ip.startswith("169."):
                usb_ip = ip
    elif os.name == 'posix':
        # x = os.system('ifconfig | grep "inet" | grep -Fv 127.0.0.1 | awk "{print $2}"')
        hostname = socket.gethostname()
        local_ip = subprocess.check_output(['ipconfig', 'getifaddr', 'en0']).decode(sys.stdout.encoding).strip()
        usb_ip = ''
        server_address = socket.gethostbyname_ex(socket.gethostname())

    output = {'hostname': hostname, 'local': local_ip, 'usb': usb_ip, 'all': server_address[2]}
    logging.debug(f"\tHostname: {socket.gethostname()}")
    logging.debug(f"\tLocal: {local_ip}")
    logging.debug(f"\tUSB: {usb_ip}")
    for i, add in enumerate(server_address[2]):
        if add is not local_ip and add is not usb_ip:
            logging.debug(f"\tIP {i}: {add}")

    logging.debug('\t-------------'
                  '')
    return output
