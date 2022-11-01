# Dong nay da nhan dc data tu Raspberry
# import socket
# TCP_IP = ""
# TCP_PORT = 12345
# BUFFER_SIZE = 20 #NOrmally 1024 but we want a fast response
# s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# s.bind((TCP_IP, TCP_PORT))
# s.listen(1)
# conn, addr = s.accept()
# print("Connction address: ", addr)
# while 1:
#   data = conn.recv(BUFFER_SIZE)
#   if not data:
#       break
#   print("received data: ", data)
#   conn.send(data) #echo
# conn.close()

# from connect_local_port import *
# import re
# from influxdb import InfluxDBClient
# import datetime
#
#
# def create_json(measurement='gen_ecg', userid='6c89f539-71c6-490d-a28d-6c5d84c0ee2f', data_point=0, timestamp=''):
#     json_body = [
#             {
#                 "measurement": measurement,
#                 "tags": {
#                     "id": userid
#                 },
#                 "fields": {
#                     "value": data_point,
#                     "time": timestamp
#                 }
#             }
#         ]
#     return json_body
#
#
# trans_data = InfluxDBClient(host="localhost", port=8086, username="admin", password="bete1010")
# trans_data.switch_database('IoT')
#
# port = get_available_port()
# device = connect_serial_port(port=port, timeout=None)
# try:
#     while device.is_open:
#         size = device.inWaiting()
#         if size > 0:
#             print('Size: ', size)
#             data = device.read(size)
#             timestamp = datetime.datetime.utcnow()
#             res = data.decode("utf-8")
#             x = re.findall(b"\x1b", data)
#             if len(x) != 0:
#                 continue
#             else:
#                 if len(res) > 0:
#                     res = re.sub("\r\n", ",", res)
#                     res = re.sub(' ', '', res)
#                     res = res.split(",")
#                     print(res)
#                     for index, r in enumerate(res):
#                         if r != '':
#                             delta = datetime.timedelta(milliseconds=(index - 15) * 7.8125)
#                             # print(delta*1000)
#                             current = datetime.datetime.strftime(timestamp + delta, '%Y-%m-%dT%H:%M:%S.%fZ')
#                             trans_data.write_points(create_json(data_point=int(res[index]), timestamp=current))
# except KeyboardInterrupt:
#     device.close()
#     trans_data.close()
#

from influxdb import InfluxDBClient
import datetime
import serial
import re
from biosppy.signals import ecg
import numpy as np


def create_json(measurement='gen_ecg', userid='6c89f539-71c6-490d-a28d-6c5d84c0ee2f', data_point=0, time=''):
    json_body = [
            {
                "measurement": measurement,
                "tags": {
                    "id": userid
                },
                "fields": {
                    "value": data_point,
                    "time": time
                }
            }
        ]
    return json_body


port = 'COM4'
baud_rate = 115200
serial_port = serial.Serial(port=port, baudrate=baud_rate, timeout=1)

trans_data = InfluxDBClient(host='localhost', port=8086, username='admin', password='bete1010')
trans_data.create_database('test')
trans_data.switch_database('test')

heartbeats = [0]*1280
try:
    while serial_port.is_open:
        size = serial_port.inWaiting()
        if size:
            data = serial_port.read(size)
            res = data.decode("utf-8")
            x = re.findall(b"\x1b", data)
            if len(x) != 0:
                continue
            else:
                if len(res) > 0:
                    timestamp = datetime.datetime.utcnow()
                    res = re.sub("\r\n", ",", res)
                    res = res.split(",")
                    for index, heartbeat_data in enumerate(res):
                        heartbeat_data = heartbeat_data.strip()
                        if len(heartbeat_data) > 0:
                            heartbeats.append(int(heartbeat_data))
                            del heartbeats[0]
                            delta = datetime.timedelta(milliseconds=(index - len(res))*7.8125)
                            current = datetime.datetime.strftime(timestamp + delta, '%Y-%m-%dT%H:%M:%S.%fZ')
                            trans_data.write_points(create_json(data_point=int(heartbeat_data), time=current))
                    try:
                        list_time_interval = []
                        output = ecg.ecg(np.array(heartbeats), 125, None, False, False)
                        R_peaks = np.copy(output['rpeaks'])
                        if len(R_peaks) >= 5:
                            for i in range(0, len(R_peaks) - 1):
                                time_interval = R_peaks[i + 1] - R_peaks[i]
                                list_time_interval.append(time_interval)
                            mean_time_interval = sum(list_time_interval) / len(list_time_interval)
                            trans_data.write_points(create_json(measurement='heartrate', data_point=int(mean_time_interval),
                                                                time=datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')))
                            print(mean_time_interval)
                    except:
                        continue


except KeyboardInterrupt:
    trans_data.close()
    serial_port.close()
