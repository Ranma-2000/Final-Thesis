import numpy as np
import pandas as pd
import serial
import time
import re
from biosppy.signals import ecg
import xgboost as xgb

model = xgb.XGBClassifier()
model.load_model('xgb_ecg.model')

baud_rate = 115200
port = 'COM3'

heartbeats = np.zeros(1250).astype(int)
heartbeats = list(heartbeats)
time_list = []
count = 0

print('Success! Built a Docker Image and can run a container\n')

try:
    while True:
        try:
            z1serial = serial.Serial(port=port, baudrate=baud_rate, timeout=1)
            if z1serial.is_open:
                start = time.time()
                while True:
                    size = z1serial.inWaiting()
                    if size:
                        data = z1serial.read(size)
                        res = data.decode("utf-8")
                        x = re.findall(b"\x1b", data)
                        if len(x) != 0:
                            continue
                        else:
                            if len(res) > 0:
                                res = re.sub("\r\n", ",", res)
                                res = res.split(",")
                                with open('data.csv', 'a+') as txt:
                                    for hbdata in res:
                                        hbdata = hbdata.strip()
                                        if len(hbdata) > 0:
                                            heartbeats.append(int(hbdata))
                                            del heartbeats[0]
                                            txt.write(f'{hbdata},')
                                        # print(hbdata)
                                # print(heartbeats)
                                end = time.time()
                                print(end - start)
                                time_list.append(end - start)
                                start = time.time()
                                # R_peaks, S_pint, Q_point = QRS_util.EKG_QRS_detect(np.array(heartbeats), 125, False, False)
                                # print(R_peaks)
                                try:
                                    list_time_interval = []
                                    output = ecg.ecg(np.array(heartbeats), 125, None, False, False)
                                    R_peaks = output['rpeaks']
                                except:
                                    continue
                                if len(R_peaks) >= 5:
                                    count += 1
                                    print(f'Index :{count}')
                                    with open(f'{count}.csv', 'w+') as file:
                                        for beat in heartbeats:
                                            file.writelines(f'{beat}\n')
                                    with open(f'{count}_R.csv', 'w+') as file:
                                        for rpeak in R_peaks:
                                            file.writelines(f'{rpeak}')
                                    print(R_peaks)
                                    for i in range(0, len(R_peaks) - 1):
                                        time_interval = R_peaks[i + 1] - R_peaks[i]
                                        list_time_interval.append(time_interval)
                                    mean_time_interval = sum(list_time_interval) / len(list_time_interval)
                                    # Append some extra readings from next beat.
                                    beats = heartbeats[R_peaks[-3]:R_peaks[-3] + int(1.2 * mean_time_interval)]
                                    beats = np.array(beats)
                                    print(len(beats))
                                    # Normalize the readings to a 0-1 range for ML purposes.
                                    beats = (beats - beats.min()) / beats.ptp()
                                    # Pad with zeroes.
                                    zerocount = 187 - beats.size
                                    beats = np.pad(beats, (0, zerocount), 'constant', constant_values=(0.0, 0.0))
                                    beats_df = pd.DataFrame(beats)
                                    beats_df = beats_df.T
                                    # print(heartbeats)
                                    # print(R_peaks)
                                    # print(f'Len: {len(beats)}\n')
                                    # print(beats_df)
                                    result = model.predict(beats_df)
                                    if result == 0:
                                        print("Normal")
                                    else:
                                        print("Abnormal")
                                # try:
                                #     R_peaks, S_pint, Q_point = EKG_QRS_detect(heartbeats, 125, False, False)
                                #     print(R_peaks)
                                # except:
                                #     continue
                                # finally:
                                #     print('Failed')
            else:
                z1serial.close()
                print(f'{port} not open or Already in use')
        except serial.SerialException:
            print(f'{port} not open')
            time.sleep(1)
except KeyboardInterrupt:
    z1serial.close()
    print('Mean elapsed time: ', sum(time_list) / len(time_list))
    print('Exit')
