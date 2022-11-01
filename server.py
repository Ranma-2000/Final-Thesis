import socket
from custom_threading import CustomThread
import numpy as np
import logging
import pandas as pd
import xgboost as xgb
from biosppy.signals import ecg
from data_processing import *
from database import DatabaseHandler
import time


def create_json(measurement='ecg', userid='6c89f539-71c6-490d-a28d-6c5d84c0ee2f', data_point=0.0):
    json_body = {
        "measurement": measurement,
        "tags": {
            "id": userid,
        },
        "fields": {
            "value": data_point
        }
    }
    return json_body


class LoadModel:
    def __init__(self, model_mode):
        self.mode = model_mode
        self.model = None
        self.heartbeats = None
        self.rrpeak_mean_interval = 0
        self.r_left = 0
        self.previous_R_peaks = None

    def create_model(self):
        if self.mode == 0:
            self.model = xgb.XGBClassifier()

    def load_model(self):
        if self.mode == 0:
            self.model.load_model('xgb_ecg.model')

    def data_preprocessing(self, heartbeats):
        try:
            list_time_interval = []
            print(type(heartbeats))
            output = ecg.ecg(heartbeats, 125, None, False, False)
            R_peaks = np.copy(output['rpeaks'])
            R_peaks_index = np.copy(output['rpeaks'])
            print('R index: ', R_peaks_index)
            if len(R_peaks) >= 5:
                for i in range(0, len(R_peaks) - 1):
                    time_interval = R_peaks[i + 1] - R_peaks[i]
                    list_time_interval.append(time_interval)
                mean_time_interval = sum(list_time_interval) / len(list_time_interval)
                self.rrpeak_mean_interval = mean_time_interval
                # Append some extra readings from next beat.
                for idx, r in enumerate(R_peaks):
                    R_peaks[idx] = max(heartbeats[R_peaks[idx] - 3:R_peaks[idx] + 3])
                if self.previous_R_peaks is None:
                    self.previous_R_peaks = np.copy(R_peaks)
                    print('Init: ', self.previous_R_peaks)
                if not np.array_equal(self.previous_R_peaks[-1], R_peaks[-1]):
                    print('previous: ', self.previous_R_peaks)
                    print('current: ', R_peaks)
                    if R_peaks_index[-1] > int(1.2*mean_time_interval):
                        print(R_peaks[-1], "-----------------------------------------------------")
                    # starting_index = np.where(self.previous_R_peaks == R_peaks[0])[0]
                    # if len(starting_index) == 0:
                    #     starting_index = np.where(self.previous_R_peaks == R_peaks[1])[0]
                    # starting_index = starting_index[0]
                    # if len(starting_index) >= 1:
                    #     starting_index = starting_index[0]
                    # print('R_peaks[0]', R_peaks[0])
                    # print(starting_index)
                    # matching_size = 0
                    # for size in range(min(len(self.previous_R_peaks[starting_index:]), len(R_peaks))):
                    #     if np.array_equal(self.previous_R_peaks[starting_index:starting_index+size+1], R_peaks[0:0+size+1]):
                    #         matching_size = size + 1
                    # print("Matching: ", matching_size)
                    # if matching_size < len(R_peaks_index):
                    #     self.r_left = len(R_peaks_index) - matching_size
                    # count = self.r_left
                    # for i in range(- count, 0, 1):
                    #     print(count)
                    #     kernel_size = len(heartbeats[R_peaks_index[i]:R_peaks_index[i]+int(1.2 * mean_time_interval)])
                    #     print('i:', i)
                    #     print('kernel: ', kernel_size)
                    #     print('index: ', R_peaks_index[i])
                    #     if kernel_size < 1250 - R_peaks_index[i]:
                    #         if self.r_left == 0:
                    #             continue
                    #         else:
                    #             self.r_left -= 1
                    #     else:
                    #         self.r_left += 1
                    # print('r_left', self.r_left)
                    self.previous_R_peaks = np.copy(R_peaks)
                    # print('update: ', self.previous_R_peaks)
                    beats = heartbeats[R_peaks_index[-1]:R_peaks_index[-1] + int(1.2 * mean_time_interval)]
                    # Normalize the readings to a 0-1 range for ML purposes.
                    beats = (beats - beats.min()) / beats.ptp()
                    input_beat = DataPreprocessing(beats)
                    beats = input_beat.moving_average(3)  # Might occur TypeError
                    # Pad with zeroes.
                    zerocount = 187 - beats.size
                    beats = np.pad(beats, (0, zerocount), 'constant', constant_values=(0.0, 0.0))[np.newaxis]  # Might occur ValueError
                    # print(f"Beats: shape {np.append(beats, beats, axis=0).T.shape}, type {type(beats)}")
                    output = True
                    return output, beats
                else:
                    output = False
                    return output, "Unchanged beat"
        except BaseException:
            logging.exception("An exception was thrown!")
            output = False
            message = "Error"
            return output, message

    def predict(self, data):
        # data = np.array(data)
        status, obj = self.data_preprocessing(data)
        if status:
            result = self.model.predict(obj)
            if result == 0:
                output = "Normal"
            else:
                output = "Abnormal"
            return output
        elif obj == "Unchanged beat":
            output = ' '
            return output
        else:
            output = 'Error'
            return output


class ServerHandler:
    def __init__(self, port=5050, model_mode=0):
        self.PORT = port
        # self.SERVER_NAME = socket.gethostbyname(socket.gethostname())
        self.SERVER_NAME = ""
        self.ENCODING_FORMAT = 'utf-8'
        self.DISCONNECT_MESSAGE = "!DISCONNECT"
        self.FEEDBACK = ''
        self.MODEL = LoadModel(model_mode)
        self.conn = None
        self.addr = None
        self.server = None
        self.count_loop = 0
        # self.database = DatabaseHandler(host="localhost", port=8086, username="admin", password="bete1010")

    def connect(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.SERVER_NAME, self.PORT))
        self.server.listen()

    def client_accept(self):
        try:
            self.conn, self.addr = self.server.accept()
            print(f"[NEW CONNECTION] {self.addr} connected.")
            connected = True
            self.MODEL.create_model()
            self.MODEL.load_model()
            while connected:
                start = time.time()
                self.count_loop += 1
                msg = self.conn.recv(7000).decode(self.ENCODING_FORMAT)
                if msg == self.DISCONNECT_MESSAGE:
                    connected = False
                else:
                    print(f"[{self.addr}] Sent {type(msg[0])}, Length: {len(msg)}")
                    print(msg)
                    data = []
                    # data = np.array([float(d) for d in msg.split(',') if d != ''])
                    for d in msg.split(','):
                        print(d)
                        if d != '':
                            data.append(float(d))
                    data = np.array(data)
                    # for d in data:
                    #     time_series_data.append(create_json(data_point=d))
                    # self.database.json_body = time_series_data
                    # self.database.insert_data()
                    # t1 = CustomThread(target=save_csv, args=(self.count_loop, data,))
                    # t2 = CustomThread(target=self.MODEL.predict, args=(data, self.count_loop,))
                    # t1.start()
                    # t2.start()
                    # save_result = t1.join()
                    # output = t2.join()
                    # print(data[-10:-1])
                    output = self.MODEL.predict(data)
                    # output = "Sent"
                    self.conn.send(output.encode(self.ENCODING_FORMAT))
                end = time.time()
                print("Elapsed time: ", end - start)
                self.conn.sendall(b"Waiting...")
        except:
            logging.exception("An exception was thrown!")
            self.conn.close()
            # self.database.close()
