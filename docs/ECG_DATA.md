# ECG Data — `ecg.csv`

## Overview

`ecg.csv` contains a single-lead electrocardiogram (ECG) recording captured from an ECG sensor. The file includes the raw ADC output, a calibrated millivolt channel, event tags, and lead-off detection status flags.

## File Format

- **Format:** CSV with one header row (skipped on load)
- **Delimiter:** Comma (`,`)
- **Encoding:** UTF-8

### Columns

| Column | Unit | Description |
|--------|------|-------------|
| `time_s` | s | Elapsed time since recording start |
| `ecg_raw` | ADC counts | Raw 12-bit ADC output from the front-end IC |
| `etag` | — | Event tag (sensor-specific annotation) |
| `ptag` | — | Packet tag / sequence counter |
| `ecg_mv` | mV | Calibrated ECG amplitude in millivolts |
| `ldoff_ph` | binary | Lead-off detect: positive electrode, high threshold *(dropped)* |
| `ldoff_pl` | binary | Lead-off detect: positive electrode, low threshold *(dropped)* |
| `ldoff_nh` | binary | Lead-off detect: negative electrode, high threshold *(dropped)* |
| `ldoff_nl` | binary | Lead-off detect: negative electrode, low threshold *(dropped)* |

> The four `ldoff_*` columns are discarded during loading 


## Sampling

- **Sampling rate:** Inferred from the `time_s` column at load time as `fs = 1 / Δt`.
- The first **12.5 seconds** of the recording are discarded to allow the sensor front-end and patient skin contact to stabilise.

## Signal Characteristics

| Property | Value / Notes |
|----------|---------------|
| Lead configuration | Single-lead (LA–RA or equivalent) |
| Amplitude range | Typically ±1–2 mV for a healthy adult |
| Primary artefacts | Baseline wander, motion artefact, 50/60 Hz mains interference, quantisation steps visible in `ecg_raw` |
| Useful bandwidth | 0.67–20 Hz (QRS complex, P and T waves) |

### Observed Artefacts

- **Quantisation steps** visible in `ecg_raw` due to limited ADC resolution; the calibrated `ecg_mv` channel inherits these steps.
- **Baseline wander** caused by respiration and electrode movement; removed in the processing pipeline via a long median filter.
- **Impulsive spikes** at recording start; mitigated by trimming the first 12.5 s and applying an initial median filter.


## Reproducing the Analysis

```bash
python ecg.py
```

Expected console output:

```
Sampling rate: <fs> Hz
Total peaks found: <N>
--- Final Results ---
Heart Rate: <BPM> BPM
SDNN: <value> ms
RMSSD: <value> ms
```