import numpy as np
import matplotlib.pyplot as plt 
import pandas as pd 
from scipy.signal import medfilt, butter, filtfilt, find_peaks, savgol_filter
from scipy.fft import fft, fftfreq

# ---------------- LOAD ----------------
cols = ["time_s","ecg_raw","etag","ptag","ecg_mv","ldoff_ph","ldoff_pl","ldoff_nh","ldoff_nl"]
df = pd.read_csv("ecg.csv", skiprows=1, names=cols, na_values=["", " "])
df = df.apply(pd.to_numeric, errors='coerce').dropna(subset=["ecg_mv"])
df = df.drop(columns=["ldoff_ph","ldoff_pl","ldoff_nh","ldoff_nl"])

# Remove bad start and reset time
df = df[df["time_s"] >= 12.5].reset_index(drop=True)
df["time_s"] = df["time_s"] - df["time_s"].iloc[0]

fs = 1 / (df["time_s"].iloc[1] - df["time_s"].iloc[0])
print(f"Sampling rate: {fs:.2f} Hz")

# --------------- SPECTRAL ANALYSIS (PSD) ----------------
def plot_psd(sig, fs, title="Frequency Spectrum of Raw Data"):
    n = len(sig)
    yf = fft(sig)
    xf = fftfreq(n, 1/fs)[:n//2]
    psd = 2.0/n * np.abs(yf[0:n//2])
    plt.figure(figsize=(10, 3))
    plt.semilogy(xf, psd)
    plt.title(title)
    plt.xlabel('Frequency (Hz)'); plt.ylabel('Power'); plt.grid(True); plt.xlim(0, fs/2)
    plt.show()

plot_psd(df["ecg_mv"].values, fs)

# ---------------- FILTERING ----------------
# A. Initial Median Filter for spikes
raw_signal = medfilt(df["ecg_mv"].values, kernel_size=5)

# B. Butterworth (0.67Hz to 20Hz), refer to [4] from report 
def bandpass_filter(sig, low, high, fs, order=4):
    nyq = 0.5 * fs
    b, a = butter(order, [low/nyq, high/nyq], btype='band')
    return filtfilt(b, a, sig)

filtered_bp = bandpass_filter(raw_signal, 0.67, 20, fs)

# C. Savitzky-Golay Smoothing 
df["ecg_final"] = savgol_filter(filtered_bp, window_length=11, polyorder=3)

# D. Baseline correction (Final zero-centering)
baseline = medfilt(df["ecg_final"].values, kernel_size=int(0.5 * fs) | 1)
df["ecg_final"] = df["ecg_final"] - baseline

# ---------------- PEAK DETECTION ----------------
final_sig = df["ecg_final"].values
time = df["time_s"].values

# Primary detection
peaks, _ = find_peaks(final_sig, distance=int(fs*0.6), height=np.std(final_sig))

# Refine peak locations
search_win = int(0.1 * fs)
refined_peaks = []
for p in peaks:
    start, end = max(0, p - search_win//2), min(len(final_sig), p + search_win//2)
    refined_peaks.append(start + np.argmax(final_sig[start:end]))
peaks = np.array(refined_peaks, dtype=int)

print(f"Total peaks found: {len(peaks)}")

# ---------------- VISUALIZATION ----------------
plt.figure(figsize=(12, 4))
plt.plot(time, final_sig, label="Processed ECG")
plt.plot(time[peaks], final_sig[peaks], "rx", label="R-peaks")
plt.xlim(15, 25) # Showing a 10s window for clarity
plt.title(" R-peak Detection")
plt.legend(); plt.show()

# ---------------- METRICS ----------------
rr_intervals = np.diff(time[peaks])
# Physiological filter + IQR outlier removal
rr_physio = rr_intervals[(rr_intervals > 0.4) & (rr_intervals < 1.5)]
q1, q3 = np.percentile(rr_physio, [25, 75])
iqr = q3 - q1
rr_final = rr_physio[(rr_physio > q1 - 1.5*iqr) & (rr_physio < q3 + 1.5*iqr)]

# Calculate Final Metrics
heart_rate = 60 / np.mean(rr_final)
sdnn = np.std(rr_final) * 1000 
rmssd = np.sqrt(np.mean(np.diff(rr_final)**2)) * 1000

print(f"--- Final Results ---")
print(f"Heart Rate: {heart_rate:.2f} BPM")
print(f"SDNN: {sdnn:.2f} ms")
print(f"RMSSD: {rmssd:.2f} ms") 

# ---------------- VISUALIZATION ----------------

plt.figure(figsize=(12, 5))
plt.plot(df["time_s"], df["ecg_mv"], alpha=0.3, label="Raw (with Quantization/Steps)", color='gray')
plt.plot(df["time_s"], df["ecg_final"], label="Final Filtered", color='red', linewidth=1.5)
plt.xlim(15, 18)  # Focus on a 3-second window
plt.title("Raw and Digitally Processed Signal")
plt.xlabel("Time (s)")
plt.ylabel("Amplitude (mV)")
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()

#  HRV  
plt.figure(figsize=(10, 5))
plt.plot(rr_final, marker='o', linestyle='-', color='green', markersize=4)
plt.title("RR-Intervals (Raw Heart Rate Variability)")
plt.xlabel("Beat Number")
plt.ylabel("RR Interval (s)")
plt.grid(True, linestyle='--', alpha=0.6)
plt.show()

# FIGURE 4: Distribution of RR Intervals
plt.figure(figsize=(10, 5))
plt.hist(rr_final * 1000, bins=15, color='purple', edgecolor='black', alpha=0.7)
plt.title("Distribution of RR Intervals")
plt.xlabel("Interval Duration (ms)")
plt.ylabel("Frequency")
plt.show()