import re
import socket
from connect_local_port import *
from timeit import default_timer as timer
from datetime import timedelta


class Device:
    def __init__(self):
        self.active_port = get_available_port()
        self.active_device = connect_serial_port(self.active_port)


class ClientHandler:
    def __init__(self, host='192.168.1.11', port=5050):
        self.HOST = host
        self.PORT = port
        self.SERVER_CONNECTION = None
        self.device = Device().active_device

    def connect_server(self):
        self.SERVER_CONNECTION = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.SERVER_CONNECTION.connect((self.HOST, self.PORT))

    def get_data(self, heartbeats):
        heartbeats = heartbeats
        while self.device.is_open:
            size = self.device.inWaiting()
            if size:
                data = self.device.read(size)
                res = data.decode("utf-8")
                x = re.findall(b"\x1b", data)
                if len(x) != 0:
                    continue
                else:
                    if len(res) > 0:
                        res = re.sub("\r\n", ",", res)
                        res = res.split(",")
                        for heartbeat_data in res:
                            heartbeat_data = heartbeat_data.strip()
                            if len(heartbeat_data) > 0:
                                heartbeats.append(str(heartbeat_data))
                                del heartbeats[0]
                        output = ','.join(heartbeats).encode('utf-8')
                        return output

    def run(self, init_heartbeats):
        msg = self.get_data(init_heartbeats)
        self.SERVER_CONNECTION.sendall(msg)
        feedback = self.SERVER_CONNECTION.recv(1024).decode('utf-8')
        if feedback != ' ':
            print(feedback)
