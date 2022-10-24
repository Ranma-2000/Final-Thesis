import socket
import threading
import numpy as np
import logging
import pandas as pd
import xgboost as xgb
from biosppy.signals import ecg
from data_processing import *


class LoadModel:
    def __init__(self, model_mode):
        self.mode = model_mode
        self.model = None
        self.heartbeats = None
        self.rrpeak_mean_interval = 0

    def create_model(self):
        if self.mode == 0:
            self.model = xgb.XGBClassifier()

    def load_model(self):
        if self.mode == 0:
            self.model.load_model('xgb_ecg.model')

    def data_preprocessing(self, heartbeats):
        try:
            list_time_interval = []
            output = ecg.ecg(heartbeats, 125, None, False, False)
            R_peaks = output['rpeaks']
            if len(R_peaks) >= 5:
                for i in range(0, len(R_peaks) - 1):
                    time_interval = R_peaks[i + 1] - R_peaks[i]
                    list_time_interval.append(time_interval)
                mean_time_interval = sum(list_time_interval) / len(list_time_interval)
                self.rrpeak_mean_interval = mean_time_interval
                # Append some extra readings from next beat.
                beats = heartbeats[R_peaks[-3]:R_peaks[-3] + int(1.2 * mean_time_interval)]
                beats = np.array(beats)
                # Normalize the readings to a 0-1 range for ML purposes.
                beats = (beats - beats.min()) / beats.ptp()
                input_beat = DataPreprocessing(beats)
                beats = input_beat.moving_average(3)  # Might occur TypeError
                # Pad with zeroes.
                zerocount = 187 - beats.size
                beats = np.pad(beats, (0, zerocount), 'constant', constant_values=(0.0, 0.0))  # Might occur ValueError
                beats_df = pd.DataFrame(beats)
                beats_df = beats_df.T
                output = True
                return output, beats_df
        except BaseException:
            logging.exception("An exception was thrown!")
            output = False
            message = "Error"
            return output, message

    def predict(self, data):
        status, obj = self.data_preprocessing(data)
        if status:
            result = self.model.predict(obj)
            if result == 0:
                output = "Normal"
            else:
                output = "Abnormal"
            return output
        else:
            output = "Error"
            return output


class ServerHandler:
    def __init__(self, port=5050, model_mode=0):
        self.PORT = port
        self.SERVER_NAME = socket.gethostbyname(socket.gethostname())
        self.ENCODING_FORMAT = 'utf-8'
        self.DISCONNECT_MESSAGE = "!DISCONNECT"
        self.FEEDBACK = ''
        self.MODEL = LoadModel(model_mode)
        self.conn = None
        self.addr = None
        self.server = None

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
                msg = self.conn.recv(7000).decode(self.ENCODING_FORMAT)
                if msg == self.DISCONNECT_MESSAGE:
                    connected = False
                else:
                    print(f"[{self.addr}] Sent {type(msg[0])}, Length: {len(msg)}")
                    data = [float(d) for d in msg.split(',')]
                    data = np.array(data)
                    output = self.MODEL.predict(data)
                    self.conn.send(output.encode(self.ENCODING_FORMAT))
        except:
            self.conn.close()
