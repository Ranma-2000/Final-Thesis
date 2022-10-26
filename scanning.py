import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from biosppy.signals import ecg
import logging

data = pd.read_csv('Khoa_200722_1705.csv', header=None).values.tolist()
heartbeats = np.zeros(1280).astype(int)
ecg_data = np.array(data[7:840]).astype(int)
for i in range(6):
    ecg_data = np.append(ecg_data, ecg_data)
    print(len(ecg_data))
r_left = None
previous_R_peaks = None
previous_R_peaks_index = None
for count_loop in range(0, 100, 1):  # IndexError if len(ecg_data)%16 != 0
    beats = []
    print()
    print("$ Loop: ", count_loop)
    print('----------------------------------------------')
    # Update with input realtime data
    for i in range(0, 16, 1):
        heartbeats = np.append(heartbeats, ecg_data[i])
        heartbeats = np.delete(heartbeats, 0, 0)
    for i in range(0, 16, 1):
        ecg_data = np.delete(ecg_data, 0, 0)
    try:
        # Detect R peak
        out = ecg.ecg(signal=heartbeats, sampling_rate=128, show=False)
        R_peaks_index = np.array(out['rpeaks'])
        R_peaks = np.array(out['rpeaks'])
        if len(R_peaks_index) >= 3 and count_loop >= 43:
            # Correct R peak
            for idx, r in enumerate(R_peaks):
                R_peaks[idx] = max(heartbeats[R_peaks[idx]-3:R_peaks[idx]+3])
                R_peaks_index[idx] = list(heartbeats).index(R_peaks[idx])
            # Initialize previous_R_peaks for the first time run
            if previous_R_peaks is None and previous_R_peaks_index is None:
                previous_R_peaks = R_peaks
                previous_R_peaks_index = R_peaks_index
            # Split beats
            # for r_peak_index in range(0, len(R_peaks) - 1, 1):
            #     beats.append(heartbeats[R_peaks_index[r_peak_index]:R_peaks_index[r_peak_index+1]])
            list_time_interval = []
            for i in range(0, len(R_peaks) - 1):
                time_interval = R_peaks[i + 1] - R_peaks[i]
                list_time_interval.append(time_interval)
            mean_time_interval = sum(list_time_interval) / len(list_time_interval)
            if not np.array_equal(previous_R_peaks, R_peaks):
                print('Peaks changed')
                matching_size = []
                print("R_peaks", R_peaks)
                print("previous_R_peaks", previous_R_peaks)
                for starting_index in range(0, len(R_peaks) - 1, 1):
                    print("Starting matching index: ", starting_index)
                    size = 0
                    for i in range(starting_index, len(R_peaks), 1):
                        print(R_peaks[starting_index:i], previous_R_peaks[0:i])
                        if R_peaks[starting_index:i] == previous_R_peaks[0:i]:
                            # print('Size', size)
                            size += 1
                            print(f'Matching {previous_R_peaks[starting_index:starting_index + size], R_peaks[0:size]}')
                            searching = True
                            matching_size.append(size)
                            print('Current loop Matching size: ', matching_size[-1])
                print('Final Matching size: ', max(matching_size))
                print('Len R_peaks: ', len(R_peaks))
            previous_R_peaks = R_peaks
            previous_R_peaks_index = R_peaks_index
    except BaseException:
        logging.exception("Error")
        break
