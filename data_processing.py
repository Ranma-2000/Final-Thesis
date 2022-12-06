import numpy as np
from scipy import signal
from scipy.signal import butter, sosfilt, sosfilt_zi, sosfiltfilt

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

    @staticmethod
    def butter_bandpass(lowpass_cut, highpass_cut, fs=128, order=5):
        nyq = 0.5 * fs
        low = lowpass_cut / nyq
        high = highpass_cut / nyq
        sos = butter(order, [low, high], analog=False, btype="band", output="sos")
        return sos

    @staticmethod
    def butter_bandpass_filter(data, lowpass_cut, highpass_cut, fs=128, order=5):
        """
        Filter data along one dimension using cascaded second-order sections.
        Using lfilter for each second-order section.
        :param data: 
        :param lowpass_cut:
        :param highpass_cut:
        :param fs:
        :param order:
        :return:
        """
        sos = DataPreprocessing.butter_bandpass(lowpass_cut, highpass_cut, fs, order=order)
        y = sosfilt(sos, data)
        return y

    @staticmethod
    def butter_bandpass_filter_once(data, lowpass_cut, highpass_cut, fs, order=5):
        sos = DataPreprocessing.butter_bandpass(lowpass_cut, highpass_cut, fs, order=order)
        # Apply the filter to data. Use lfilter_zi to choose the initial condition of the filter.
        zi = sosfilt_zi(sos)
        z, _ = sosfilt(sos, data, zi=zi * data[0])
        return sos, z, zi

    @staticmethod
    def butter_bandpass_filter_again(sos, z, zi):
        """
        Apply the filter again, to have a result filtered at an order the same as filtfilt.
        :param sos:
        :param z:
        :param zi:
        :return:
        """
        z2, _ = sosfilt(sos, z, zi=zi * z[0])
        return z2

    def butter_bandpass_forward_backward_filter(self, lowpass_cut, highpass_cut, fs=128, order=5):
        """
        Apply a digital filter forward and backward to a signal.
        This function applies a linear digital filter twice, once forward and once backwards.
        The combined filter has zero phase and a filter order twice that of the original.
        :param lowpass_cut:
        :param highpass_cut:
        :param fs:
        :param order:
        :return:
        """
        sos = DataPreprocessing.butter_bandpass(lowpass_cut, highpass_cut, fs, order=order)
        y = sosfiltfilt(sos, self.signal)
        return y

    def final_filter(self, order=512, rs=60, btype='bandstop', fs=256):
        sos_50hz = signal.iirfilter(N=order, Wn=[49, 51], rs=rs, btype='bandstop',
                               analog=False, ftype='cheby2', fs=fs, output='sos')
        output = self.butter_bandpass_forward_backward_filter(lowpass_cut=0.5, highpass_cut=100, fs=128, order=5)
        # output = signal.sosfilt(sos2, output)
        return output
