import socket
from connect_local_port import *
import re
import numpy as np
import pickle


def run(device_serial_object):
    heartbeats = np.zeros(1250).astype(int)
    heartbeats = list(heartbeats)
    try:
        while device_serial_object.is_open:
            print("Reading")
            size = device_serial_object.inWaiting()
            if size:
                data = device_serial_object.read(size)
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
                                heartbeats.append(int(heartbeat_data))
                                del heartbeats[0]
                                print(heartbeats[0:10])
            output = pickle.dumps(heartbeats)
            return output
    except:
        pass


HOST = '127.0.0.1'
PORT = 8000

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = (HOST, PORT)
print('connecting to %s port ' + str(server_address))
s.connect(server_address)
try:
    while True:
        active_port = get_available_port()
        serial_port = connect_serial_port(active_port)

        msg = run(serial_port)
        print("Sent")
        s.sendall(msg)

finally:
    s.close()
    pass
