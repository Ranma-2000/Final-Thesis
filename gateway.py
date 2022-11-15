import xgboost as xgb
from biosppy.signals import ecg
from data_processing import *
from connect_local_port import *
import re
import logging
from influxdb import InfluxDBClient
import datetime
import pandas as pd
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
        "fields": {
            "value": data_point,
            "time": time
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
# token = "KukNM3hreF1X5P32uR-aFOO9nogqcZwuasMYCptw0mghxdUiBforHrAB_vtIkEqmundgnKzPKqvkjJpRQSiv3A=="
# org = "18146115@student.hcmute.edu.vn"
# url = "https://us-east-1-1.aws.cloud2.influxdata.com"
#
# client = influxdb_client.InfluxDBClient(url=url, token=token, org=org)
# bucket = "iot_device"
#
# write_api = client.write_api(write_options=SYNCHRONOUS)

loop = 0
while device.is_open:
    loop += 1
    try:
        list_time_interval = []
        size = device.inWaiting()
        if size:
            data = device.read(size)
            res = data.decode("utf-8")
            x = re.findall(b"\x1b", data)
            if len(x) != 0:
                continue
            else:
                if len(res) > 0:
                    res = re.sub("\r\n", ",", res)
                    res = res.split(",")
                    res = [r.strip() for r in res]
                    res.remove('')
                    print(res)
                    current_timestamp = datetime.datetime.utcnow()
                    for index, heartbeat_data in enumerate(res):
                        if len(heartbeat_data) > 0:
                            heartbeats = np.append(heartbeats, int(heartbeat_data))
                            heartbeats = np.delete(heartbeats, 0)
                            delta = datetime.timedelta(milliseconds=(index - (len(res) - 1)) * 7.8125)
                            timestamp = datetime.datetime.strftime(current_timestamp + delta, '%Y-%m-%dT %H:%M:%S.%fZ')
                            print(timestamp)
                            database.write_points(create_json(data_point=int(heartbeat_data), time=timestamp))
                            # dictionary = {
                            #     "measurement": "ecg",
                            #     "tags": {"id": "Ti1sO"},
                            #     "fields": {"signal": int(heartbeat_data)},
                            #     "time": timestamp
                            # }
                            # point = Point.from_dict(dictionary, write_precision=WritePrecision.NS)
                            # point = (
                            #     Point("ecg")
                            #     .tag("id", "Ti1sO")
                            #     .field("signal", int(heartbeat_data))
                            #     .field("_time", timestamp)
                            #     .write_precision(WritePrecision.NS)
                            # )
                            # write_api.write(bucket=bucket, org="18146115@student.hcmute.edu.vn", record=point)
                            # self.database.insert_data(create_json(data_point=int(heartbeat_data), time=current))

                    output = ecg.ecg(heartbeats, 125, None, False, False)
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
                            R_peaks[idx] = max(heartbeats[R_peaks[idx] - 3:R_peaks[idx] + 3])
                        if previous_R_peaks is None:
                            previous_R_peaks = np.copy(R_peaks)
                            print('Init: ', previous_R_peaks)
                        if not np.array_equal(previous_R_peaks[-1], R_peaks[-1]):
                            # print('previous: ', previous_R_peaks)
                            # print('current: ', R_peaks)
                            if R_peaks_index[-1] > int(1.2 * mean_time_interval):
                                # print(R_peaks[-1], "-----------------------------------------------------")
                                previous_R_peaks = np.copy(R_peaks)
                                # print('update: ', self.previous_R_peaks)
                                beats = heartbeats[R_peaks_index[-1]:R_peaks_index[-1] + int(1.2 * mean_time_interval)]
                                # Normalize the readings to a 0-1 range for ML purposes.
                                beats = (beats - beats.min()) / beats.ptp()
                                input_beat = DataPreprocessing(beats)
                                beats = input_beat.moving_average(3)  # Might occur TypeError
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
                                print('R peaks are not changed')
    except KeyboardInterrupt:
        break
    except:
        logging.exception("An exception was thrown!")
database.close()
device.close()

