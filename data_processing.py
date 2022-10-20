import numpy as np
from scipy import signal


class DataPreprocessing:

    def __init__(self, ecg_signal):
        self.signal = ecg_signal

    def moving_average(self, window):
        """
        Numpy based moving average function.
        Input is a signal and window size
        Output is average
        :param window:
        :return filtered signal:
        """
        return np.convolve(self.signal, np.ones((window,)) / window, mode='valid')

    def custom_iir_filter(self, order=17, band=(49, 51), rs=60, btype='bandstop', fs=125):
        sos = signal.iirfilter(N=order, Wn=band, rs=rs, btype=btype,
                               analog=False, ftype='cheby2', fs=fs, output='sos')
        output = signal.sosfilt(sos, self.signal)
        return output
