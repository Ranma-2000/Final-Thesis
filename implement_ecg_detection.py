import os
import wfdb as wf
import numpy as np
from scipy import signal
import data.mitdbread as dm
from biosppy.signals import ecg  # R peaks detection algorithm 1
from utils.QRS_util import *  # R peaks detection algorithm 2
import matplotlib.pyplot as plt

records = dm.get_records()
print(records)

# Instead of using the annotations to find the beats, we will
# use R-peak detection instead. The reason for this is so that
# the same logic can be used to analyze new and un-annotated
# ECG data. We use the annotations here only to classify the
# beat as either Normal or Abnormal and to train the model.
# Reference:
# https://physionet.org/physiobank/database/html/mitdbdir/intro.htm
realbeats = ['N','L','R','B','A','a','J','S','V','r',
             'F','e','j','n','E','/','f','Q','?']

# Loop through each input file. Each file contains one
# record of ECG readings, sampled at 360 readings per
# second.
fig, ax = plt.subplots()
for path in records:
    pathpts = path.split('/')
    fn = pathpts[-1]
    print('Loading file:', path)

    # Read in the data
    record = wf.rdsamp(path)
    annotation = wf.rdann(path, 'atr')

    # Print some meta informations
    print('    Sampling frequency used for this record:', record[1].get('fs'))
    print('    Shape of loaded data array:', record[0].shape)
    print('    Number of loaded annotations:', len(annotation.num))

    # Get the ECG values from the file.
    data = record[0].transpose()
    # print(data)

    # Generate the classifications based on the annotations.
    # 0.0 = undetermined
    # 1.0 = normal
    # 2.0 = abnormal
    cat = np.array(annotation.symbol)
    rate = np.zeros_like(cat, dtype='float')
    for catid, catval in enumerate(cat):
        if (catval == 'N'):
            rate[catid] = 1.0 # Normal
        elif (catval in realbeats):
            rate[catid] = 2.0 # Abnormal
    rates = np.zeros_like(data[0], dtype='float')
    rates[annotation.sample] = rate

    indices = np.arange(data[0].size, dtype='int')

    # Process each channel separately (2 per input file).
    for channelid, channel in enumerate(data):
        chname = record[1].get('sig_name')[channelid]
        print('    ECG channel type:', chname)
        ax.cla()
        channel = channel * 1000
        iter_max = 0
        R_peaks, S_pint, Q_point = EKG_QRS_detect(channel[0+iter_max:3600+iter_max], record[1].get('fs'), True, False)
        print(len(channel[0+iter_max:3600+iter_max]))
        ax.plot(channel[0+iter_max:3600+iter_max])
        if len(R_peaks) > 0 and len(S_pint) > 0 and len(Q_point) > 0:
            ax.plot(R_peaks, channel[0+iter_max:3600+iter_max][R_peaks], 'r-o')
            ax.plot(S_pint, channel[0+iter_max:3600+iter_max][S_pint], 'y-o')
            ax.plot(Q_point, channel[0+iter_max:3600+iter_max][Q_point], 'b-o')
        fig_name = path.split("\\")[-1]
        fig.savefig(f'{fig_name}.png')
        with open(f'{fig_name}.txt', 'a+') as txt:
            for point in R_peaks:
                txt.write(f'{point},')
            txt.write("\n\n")
            for point in S_pint:
                txt.write(f'{point},')
            txt.write("\n\n")
            for point in Q_point:
                txt.write(f'{point},')
            txt.write("\n\n")
