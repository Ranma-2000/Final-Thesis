import xgboost as xgb
from biosppy.signals import ecg
from data_processing import *
from connect_local_port import *
import re
import logging
from influxdb import InfluxDBClient
import datetime
from scipy.signal import butter, sosfilt, sosfilt_zi, sosfiltfilt, lfilter, lfilter_zi, filtfilt, sosfreqz, resample
import pandas as pd
import heartpy as hp
# from database import *
# import influxdb_client
# from influxdb_client import InfluxDBClient, Point, WritePrecision
# from influxdb_client.client.write_api import SYNCHRONOUS


def create_json(measurement='ecg', userid='T1lsO', data_point=0.0, time=""):
    json_body = [{
        "measurement": measurement,
        "tags": {
            "id": userid
        },
        "time": time,
        "fields": {
            "value": data_point
        }
    }]
    return json_body


xgb_model = xgb.XGBClassifier()
xgb_model.load_model('xgb_ecg.model')

active_port = get_available_port()
device = connect_serial_port(active_port)

heartbeats = np.zeros(1250).astype(int)
previous_R_peaks = None

host = "localhost"
port = 8086
username = "admin"
password = "bete1010"
database = InfluxDBClient(host=host, port=port, username=username, password=password)
# database.create_database("IoT")
database.switch_database('iot_device')

loop = 0
while device.is_open:
    loop += 1
    try:
        list_time_interval = []
        size = device.inWaiting()
        if size:
            data = device.read(size)
            res = data.decode("utf-8")
            # print(len(res))
            x = re.findall(b"\x1b", data)
            if len(x) != 0:
                continue
            else:
                if len(res) > 0:
                    res = re.sub("\r\n", ",", res)
                    res = res.split(",")
                    current_timestamp = datetime.datetime.utcnow()
                    res = [r.strip() for r in res if len(r.strip()) > 0]
                    # print('Reset count data')
                    # count_data = 0
                    data = []
                    for index, heartbeat_data in enumerate(res):
                        if len(heartbeat_data) > 0:
                            # count_data += 1
                            heartbeats = np.append(heartbeats, int(heartbeat_data))
                            heartbeats = np.delete(heartbeats, 0)
                            delta = datetime.timedelta(milliseconds=(index - len(res)) * 7.8125)
                            timestamp = datetime.datetime.strftime(current_timestamp + delta, '%Y-%m-%dT %H:%M:%S.%fZ')
                            data_point = create_json(measurement='raw', data_point=float(heartbeat_data), time=timestamp)
                            data.append(data_point[0])
                    database.write_points(data)

                    pd.DataFrame(heartbeats).to_csv(f'data/baseline_wander/raw_{loop}.csv', index=False, header=False)
                    input_heartbeats = hp.scale_data(hp.remove_baseline_wander(np.copy(heartbeats), 256, cutoff=0.01))
                    # print(count_data)
                    pd.DataFrame(input_heartbeats).to_csv(f'data/baseline_wander/filtered_{loop}.csv', index=False, header=False)
                    output = ecg.ecg(input_heartbeats, 128, None, False, False)
                    R_peaks = np.copy(output['rpeaks'])
                    R_peaks_index = np.copy(output['rpeaks'])

                    # print('R index: ', R_peaks_index)
                    if len(R_peaks) >= 5:
                        for i in range(0, len(R_peaks) - 1):
                            time_interval = R_peaks[i + 1] - R_peaks[i]
                            list_time_interval.append(time_interval)
                        mean_time_interval = sum(list_time_interval) / len(list_time_interval)
                        database.write_points(create_json(measurement="heartrate",
                                                          data_point=int(60000/(mean_time_interval*7.8125)),
                                                          time=current_timestamp.strftime('%Y-%m-%dT %H:%M:%S.%fZ')))
                        # Append some extra readings from next beat.
                        for idx, r in enumerate(R_peaks):
                            R_peaks[idx] = max(input_heartbeats[R_peaks[idx] - 3:R_peaks[idx] + 3])
                        if previous_R_peaks is None:
                            previous_R_peaks = np.copy(R_peaks)
                            print('Init: ', previous_R_peaks)
                        if not np.array_equal(previous_R_peaks[-1], R_peaks[-1]):
                            # print(previous_R_peaks, '\n', R_peaks)
                            # print(R_peaks_index, len(heartbeats), mean_time_interval)
                            # print(R_peaks_index[-1], R_peaks_index[-1] + int(1.2 * mean_time_interval))
                            # print(R_peaks[-1], "-----------------------------------------------------")
                            if (R_peaks_index[-1] + int(1.2 * mean_time_interval)) <= 1250:
                                print("OK -----------------------------------")
                                previous_R_peaks = np.copy(R_peaks)
                                # print('update: ', self.previous_R_peaks)
                                input_heartbeats = hp.scale_data(input_heartbeats, lower=0, upper=1)
                                beats = np.copy(input_heartbeats[R_peaks_index[-1]:(R_peaks_index[-1] + int(1.2 * mean_time_interval))])
                                # for index in range(0, len(beats), 1):
                                #     delta = datetime.timedelta(milliseconds=(index - len(beats)) * 7.8125)
                                #     timestamp = datetime.datetime.strftime(current_timestamp + delta, '%Y-%m-%dT %H:%M:%S.%fZ')
                                #     database.write_points(create_json(measurement='extracted',
                                #                                       data_point=input_heartbeats[index - len(beats)],
                                #                                       time=timestamp))

                                # beats = butter_bandpass_forward_backward_filter(beats, 0.05 * 3.3, 2, fs=125, order=5)
                                # input_beat = DataPreprocessing(beats)
                                # beats = input_beat.moving_average(3)  # Might occur TypeError
                                # for index, value in enumerate(beats):
                                # Pad with zeroes.
                                zerocount = 187 - beats.size
                                beats = np.pad(beats, (0, zerocount), 'constant', constant_values=(0.0, 0.0))[np.newaxis]  # Might occur ValueError
                                pd.DataFrame(beats).to_csv(f'{loop}.csv')
                                result = xgb_model.predict(beats)
                                if result == 0:
                                    output = "Normal"
                                else:
                                    output = "Abnormal"
                                json_body = [{
                                    "measurement": "log",
                                    "tags": {
                                        "id": "Ti1sO",
                                        "result": result
                                    },
                                    "fields": {
                                        "value": output,
                                        "time": current_timestamp.strftime('%Y-%m-%dT %H:%M:%S.%fZ')
                                    }
                                }]
                                database.write_points(json_body)
                                print(result, output)
                        else:
                            continue
                            # print('R peaks are not changed')
    except KeyboardInterrupt:
        break
    except:
        logging.exception("An exception was thrown!")
database.close()
device.close()

