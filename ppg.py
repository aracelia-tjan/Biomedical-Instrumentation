import numpy as np
import matplotlib.pyplot as plt 
import pandas as pd 
from scipy.signal import butter, filtfilt #for filtering 
from scipy.signal import find_peaks #for peak detection

dataset = pd.read_csv('ppg.csv', comment='%')  
dataset = dataset.dropna(axis=1, how='all')
dataset.columns = ['time', 'red', 'ir'] 
dataset = dataset[dataset['time'] >= 2.0].copy()
dataset['time'] = dataset['time'] - dataset['time'].iloc[0]

#extract signals from all columns 
time = dataset['time'].values
red = dataset['red'].values
ir = dataset['ir'].values
fs = 100  # sampling rate (Hz)

#butterworth filter 
def bandpass_filter(signal, lowcut=0.5, highcut=5, fs=100, order=4):
    nyquist = 0.5 * fs
    low = lowcut / nyquist
    high = highcut / nyquist
    
    b, a = butter(order, [low, high], btype='band')
    filtered = filtfilt(b, a, signal)
    return filtered

red_filtered = bandpass_filter(red, fs=fs) 
ir_filtered = bandpass_filter(ir, fs=fs) 
red_filtered = -red_filtered
ir_filtered = -ir_filtered #results are actually inverted so flip them back 

peaks, _ = find_peaks(red_filtered, distance=fs*0.5)  # ~max 120 bpm
peak_times = time[peaks]
intervals = np.diff(peak_times)

# BPM
bpm = 60 / intervals
print("Average BPM:", np.mean(bpm))

# AC/DC 
dc_red = np.mean(red)   # use raw signal
ac_red = np.max(red_filtered) - np.min(red_filtered)

dc_ir = np.mean(ir)
ac_ir  = np.max(ir_filtered) - np.min(ir_filtered)
# print("Red AC/DC Ratio:", ac_red/dc_red)
# print("IR AC/DC Ratio:", ac_ir/dc_ir)

R = (ac_red/dc_red) / (ac_ir/dc_ir) #ratio of ratios 
print("R (ratio of ratios):", R) 

spo2 = 110 - 25 * R  # empirical approximation
print("Estimated SpO2:", spo2) #ideally need calibration curve, but i don't have the curve for this.

#SNR 
snr_red = np.var(red_filtered) / np.var(red - red_filtered)
snr_ir = np.var(ir_filtered) / np.var(ir - ir_filtered)
print("SNR (Red):", 10 * np.log10(snr_red), "dB") 
print("SNR (IR):", 10 * np.log10(snr_ir), "dB")

#consistency check
np.std(intervals)
print("Heart Rate Variability (std of intervals):", np.std(intervals), "s")

## FIGURE PLOTTING 
#All raw signals 
plt.figure()
plt.plot(time, red, label='Red (raw)')
plt.plot(time, ir, label='IR (raw)')
plt.xlabel('Time (s)')
plt.ylabel('Amplitude')
plt.legend()
plt.title('Raw PPG Signals')

#All filtered signals 
plt.figure()
plt.plot(time, red_filtered, label='Red (filtered)')
plt.plot(time, ir_filtered, label='IR (filtered)')
plt.xlabel('Time (s)')
plt.ylabel('Amplitude')
plt.legend()
plt.title('Filtered PPG Signals')

#comparison between raw and filtered signals 
plt.figure()
plt.plot(time, red, alpha=0.4, label='Raw')
plt.plot(time, red_filtered, label='Filtered')
plt.legend()
plt.title('Red Channel: Raw vs Filtered')

#peak detection on filtered red signal
plt.figure()
plt.plot(time, red_filtered)
plt.plot(time[peaks], red_filtered[peaks], "x")
plt.xlabel('Time (s)')
plt.ylabel('Amplitude')
plt.title("Peak Detection")

#checking waveform shape of a single beat
idx = peaks[10]

window = int(0.4 * fs)  # 400 ms on each side

beat = red_filtered[idx - window : idx + window]
beat_time = time[idx - window : idx + window]
beat_time = beat_time - beat_time[0]

plt.figure()
plt.plot(beat_time, beat)
plt.title("Centered Pulse")
plt.show()