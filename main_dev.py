# from biosppy.signals import ecg
# from connect_local_port import *
# from data_processing import *
# import xgboost as xgb
# import logging
# import numpy as np
# import pandas as pd
# import time
# import re
# import pickle
# import socket
#
# def run(device_serial_object, port, model, input_heartbeat):
#     # time_list = []
#     heartbeats = input_heartbeat
#     try:
#         while device_serial_object.is_open:
#             size = device_serial_object.inWaiting()
#             if size:
#                 data = device_serial_object.read(size)
#                 res = data.decode("utf-8")
#                 x = re.findall(b"\x1b", data)
#                 if len(x) != 0:
#                     continue
#                 else:
#                     if len(res) > 0:
#                         # start = time.time()
#                         res = re.sub("\r\n", ",", res)
#                         res = res.split(",")
#                         for heartbeat_data in res:
#                             heartbeat_data = heartbeat_data.strip()
#                             if len(heartbeat_data) > 0:
#                                 heartbeats.append(int(heartbeat_data))
#                                 del heartbeats[0]
#                         try:
#                             list_time_interval = []
#                             output = ecg.ecg(np.array(heartbeats), 125, None, False, False)
#                             R_peaks = output['rpeaks']
#                         except BaseException:
#                             logging.exception("An exception was thrown!")
#                             continue
#                         if len(R_peaks) >= 5:
#                             for i in range(0, len(R_peaks) - 1):
#                                 time_interval = R_peaks[i + 1] - R_peaks[i]
#                                 list_time_interval.append(time_interval)
#                             mean_time_interval = sum(list_time_interval) / len(list_time_interval)
#                             # Append some extra readings from next beat.
#                             beats = heartbeats[R_peaks[-3]:R_peaks[-3] + int(1.2 * mean_time_interval)]
#                             beats = np.array(beats)
#                             # Normalize the readings to a 0-1 range for ML purposes.
#                             beats = (beats - beats.min()) / beats.ptp()
#                             input_beat = DataPreprocessing(beats)
#                             beats = input_beat.moving_average(3)  # Might occur TypeError
#                             # Pad with zeroes.
#                             zerocount = 187 - beats.size
#                             beats = np.pad(beats, (0, zerocount), 'constant', constant_values=(0.0, 0.0))  # Might occur ValueError
#                             beats_df = pd.DataFrame(beats)
#                             beats_df = beats_df.T
#                             result = model.predict(beats_df)
#                             if result == 0:
#                                 print("Normal")
#                             else:
#                                 print("Abnormal")
#                             print(beats)
#                             return pickle.dumps(beats), heartbeats
#                         # end = time.time()
#                         # time_list.append(end - start)
#
#     except TypeError:
#         device_serial_object.close()
#     except serial.SerialException:
#         print(f'{port} not open or already in use')
#     except ValueError:
#         device_serial_object.close()
#     except KeyboardInterrupt:
#         device_serial_object.close()
#         if len(time_list) > 0:
#             print('Mean elapsed time: ', sum(time_list) / len(time_list))
#         print('Exit')
#
#
# if __name__ == "__main__":
#     HOST = '192.168.1.7'
#     PORT = 5050
#
#     s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     server_address = (HOST, PORT)
#     print('connecting to %s port ' + str(server_address))
#     xgb_model = xgb.XGBClassifier()
#     xgb_model.load_model('xgb_ecg.model')
#     output_heartbeats = np.zeros(1250).astype(int)
#     output_heartbeats = list(output_heartbeats)
#     try:
#         active_port = get_available_port()
#         print(active_port)
#     except IndexError:
#         active_port = "COM4"
#     finally:
#         serial_port = connect_serial_port(active_port)
#         while True:
#             s.connect(server_address)
#             msg, output_heartbeats = run(serial_port, active_port, xgb_model, output_heartbeats)
#             print(f"Sent {len(msg)}")
#             s.send(msg)
