import numpy as np
import matplotlib.pyplot as plt 
import pandas as pd 
from scipy.signal import medfilt, butter, filtfilt
from scipy.ndimage import uniform_filter1d
from scipy.signal import find_peaks

# ---------------- LOAD ----------------
cols = [
    "time_s","ecg_raw","etag","ptag","ecg_mv",
    "ldoff_ph","ldoff_pl","ldoff_nh","ldoff_nl"
]

df = pd.read_csv("ecg.csv", skiprows=1, names=cols, na_values=["", " "])
df = df.apply(pd.to_numeric, errors='coerce')
df = df.dropna(subset=["ecg_mv"])
df = df.drop(columns=["ldoff_ph","ldoff_pl","ldoff_nh","ldoff_nl"])

# ---------------- REMOVE BAD START ----------------
df = df[df["time_s"] >= 12.5].reset_index(drop=True)
df["time_s"] = df["time_s"] - df["time_s"].iloc[0]

# ---------------- FINDING SAMPLING RATE ----------------
fs = 1 / (df["time_s"].iloc[1] - df["time_s"].iloc[0])
print("Sampling rate:", fs)

# ---------------- FILTERING ----------------
# median filter 
df["ecg_mv"] = medfilt(df["ecg_mv"], kernel_size=5)

# NOW extract signal (important)
signal = df["ecg_mv"].values
time = df["time_s"].values

# bandpass
def bandpass(sig, low, high, fs, order=4):
    nyq = 0.5 * fs
    b, a = butter(order, [low/nyq, high/nyq], btype='band')
    return filtfilt(b, a, sig)

filtered = bandpass(signal, 0.5, 40, fs)
filtered = -filtered #invert because the signal appears to be inverted

# ------- PEAK DETECTION --------

# removes slight upwards trend so signal sits at zero
baseline = medfilt(filtered, kernel_size=int(0.5 * fs) | 1) # 500ms window
filtered = filtered - baseline

search_win = int(0.1 * fs)
# Find anything significantly above the noise floor
peaks, _ = find_peaks(filtered, distance=int(fs*0.6), height=np.std(filtered))

refined_peaks = []
for p in peaks:
    start, end = max(0, p - search_win//2), min(len(filtered), p + search_win//2)
    refined_peaks.append(start + np.argmax(filtered[start:end]))
peaks = np.array(refined_peaks, dtype=int)

print(f"Total peaks found: {len(peaks)}")

# --- VISUALIZE ---
plt.figure(figsize=(12, 4))
plt.plot(time, filtered, label="Filtered ECG")
plt.plot(time[peaks], filtered[peaks], "rx", label="Refined R-peaks")
plt.title("R-peak Detection")
plt.legend()
plt.show()

# ---------------- RR + HR ----------------
rr_intervals = np.diff(time[peaks])

# Keep physiological range 
rr_intervals = rr_intervals[(rr_intervals > 0.4) & (rr_intervals < 1.5)]

# Use the interquartile range to kill outliers
q1, q3 = np.percentile(rr_intervals, [25, 75])
iqr = q3 - q1
lower_bound = q1 - (1.5 * iqr)
upper_bound = q3 + (1.5 * iqr)

rr_final = rr_intervals[(rr_intervals > lower_bound) & (rr_intervals < upper_bound)]

plt.figure(figsize=(10, 5))
plt.plot(rr_final, marker='o', linestyle='-')
plt.title("RR final (Raw Variability)")
plt.ylabel("Time (s)")
plt.show()

heart_rate = 60 / np.mean(rr_final)
print(f"Heart Rate (BPM): {heart_rate:.2f}")

# ---------------- HRV ----------------
# Standard deviation of the intervals
sdnn_ms = np.std(rr_final) * 1000 

# Root Mean Square of Successive Differences
rmssd_ms = np.sqrt(np.mean(np.diff(rr_final)**2)) * 1000

print(f"SDNN (ms): {sdnn_ms:.2f}")
print(f"RMSSD (ms): {rmssd_ms:.2f}")