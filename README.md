# Physiological Signal Processing — ECG & PPG Analysis

This Python project processes and analyses the author's raw biosignals recorded from ECG and PPG sensors.  Digital filtering, R-peak / pulse-peak detection, and HRV metrics from scratch using standard libraries were implemented. 



## Project Structure

```
.
├── ecg.py              # ECG processing pipeline
├── ppg.py              # PPG processing pipeline
├── ecg.csv             # Raw ECG recording (see docs/ECG_DATA.md)
├── ppg.csv             # Raw PPG recording (see docs/PPG_DATA.md)
├── docs/
│   ├── ECG_DATA.md     # ECG dataset description & column reference
│   └── PPG_DATA.md     # PPG dataset description & column reference
└── README.md
```


## Background

Electrocardiography (ECG) and photoplethysmography (PPG) are two of the most widely used non-invasive methods for monitoring cardiovascular health. This project records real signals from hardware sensors and applies a full digital signal processing (DSP) pipeline to extract clinically meaningful metrics including:

- **Heart rate** (BPM)
- **Heart rate variability** -> SDNN and RMSSD
- **Oxygen saturation estimation** (SpO₂) via the ratio-of-ratios method



## Dependencies

```
numpy
pandas
scipy
matplotlib
```

Install with:

```bash
pip install numpy pandas scipy matplotlib
```

Python 3.8+ recommended.


## ECG Pipeline (`ecg.py`)

### Processing Steps

1. **Load and Clean**: reads `ecg.csv`, drops lead-off status columns, trims the first 12.5 s of artefact, and resets the time axis.
2. **Spectral analysis**: plots the PSD of the raw signal to guide filter design.
3. **Median filter**: kernel size 5; suppresses impulsive spikes before the bandpass stage.
4. **Butterworth bandpass**: 4th-order, 0.67–20 Hz; removes baseline wander and high-frequency noise while preserving the QRS complex.
5. **Savitzky-Golay smoothing**: window 11, polynomial order 3; additional smoothing without distorting peak shapes.
6. **Baseline correction**: median filter at 0.5 s scale subtracted from the signal to zero-centre.
7. **R-peak detection**: `scipy.signal.find_peaks` with a minimum inter-peak distance of 0.6 s and a height threshold of 1 σ; peaks are then refined within a ±50 ms window.

### Output Metrics

| Metric | Description |
|--------|-------------|
| Heart Rate | Mean BPM derived from RR intervals |
| SDNN | Standard deviation of NN intervals (ms) -> overall HRV |
| RMSSD | Root mean square of successive RR differences (ms) -> parasympathetic activity |

### Visualisations

- PSD of raw ECG
- Detected R-peaks overlaid on processed signal (10 s window)
- Raw vs. filtered comparison (3 s window)
- RR interval time series
- Distribution histogram of RR intervals



## PPG Pipeline (`ppg.py`)

### Processing Steps

1. **Load & clean**: reads `ppg.csv`, drops the first 2 s of settling artefact, resets the time axis.
2. **Butterworth bandpass**: 4th-order, 0.5–5 Hz; isolates the cardiac frequency band in both the Red and IR channels.
3. **Signal inversion**: raw sensor output is inverted relative to the physiological waveform; both channels are negated.
4. **Peak detection**: applied to the filtered Red channel with a minimum distance of 0.5 s (~120 BPM upper limit).
5. **SpO₂ estimation**: ratio-of-ratios R = (AC_red / DC_red) / (AC_ir / DC_ir), then SpO₂ ≈ 110 − 25R (empirical approximation; a proper calibration curve is needed for clinical accuracy).
6. **SNR calculation**: signal power (filtered) vs. noise power (raw − filtered) for both channels.

### Output Metrics

| Metric | Description |
|--------|-------------|
| Heart Rate | Mean BPM from inter-peak intervals |
| HRV | Standard deviation of inter-peak intervals (s) |
| SpO₂ | Estimated oxygen saturation (%) uncalibrated |
| SNR Red | Signal-to-noise ratio of the Red channel (dB) |
| SNR IR | Signal-to-noise ratio of the IR channel (dB) |

### Visualisations

- Raw Red & IR signals
- Filtered Red & IR signals
- Raw vs. filtered overlay for each channel
- Peak detection on filtered Red and IR channels
- Single centred pulse waveform (400 ms each side)


## Limitations & Notes

- The SpO₂ formula (`110 − 25R`) is an empirical approximation. Accurate SpO₂ requires a sensor-specific calibration curve derived from reference measurements.
- ECG metrics are computed after physiological filtering (0.4–1.5 s) and IQR-based outlier rejection to reduce the effect of motion artefacts.
- Sampling rates are inferred from the data (`ecg.py`) or hard-coded to 100 Hz (`ppg.py`) 


## References

Signal processing design choices were informed by standard biomedical DSP literature, including recommended bandpass cutoffs for ECG (0.67–20 Hz) as referenced in the accompanying project report.
