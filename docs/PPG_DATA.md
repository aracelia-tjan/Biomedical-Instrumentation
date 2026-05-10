# PPG Data — `ppg.csv`

## Overview

`ppg.csv` contains a dual-channel photoplethysmography (PPG) recording from a reflectance or transmittance optical sensor with separate **Red** (~660 nm) and **Infrared** (~940 nm) LED channels. These two wavelengths allow both pulse detection and SpO₂ estimation via the ratio-of-ratios method.


## File Format

- **Format:** CSV; lines beginning with `%` are treated as comments and skipped on load
- **Delimiter:** Comma (`,`)
- **Encoding:** UTF-8

### Columns

| Column | Unit | Description |
|--------|------|-------------|
| `time` | s | Elapsed time since recording start |
| `red` | ADC counts (a.u.) | Photodetector output under Red LED illumination |
| `ir` | ADC counts (a.u.) | Photodetector output under IR LED illumination |

> Fully empty columns in the raw file are dropped automatically on load (`dropna(axis=1, how='all')`).


## Sampling

| Property | Value |
|----------|-------|
| Sampling rate | **100 Hz** (hard-coded in `ppg.py`) |
| Settling period removed | First **2.0 seconds** discarded |
| Time axis | Reset to zero after trimming |

Verify that the 100 Hz assumption matches sensor firmware before interpreting results as incorrect `fs` will shift all frequency-domain operations and BPM calculations.

## Filtering
Filttering must be performed in order to extract any useful information. In this analysis, a 4th order butterworth (bandpass) filter was used.  

## Signal Characteristics

| Property | Value / Notes |
|----------|---------------|
| Measurement type | Optical (reflectance or transmittance) |
| Red wavelength | ~660 nm |
| IR wavelength | ~940 nm |
| Cardiac band | 0.5–5 Hz (~30–300 BPM) |
| Signal polarity | **Inverted** relative to conventional PPG; both channels are negated in the pipeline |
| Primary artefacts | Motion artefact, ambient light leakage, low-frequency baseline drift |

### Signal Polarity Note

The raw sensor output is **inverted**. The peaks in the raw data correspond to signal troughs physiologically, and vice versa. Both `red_filtered` and `ir_filtered` are multiplied by −1 after bandpass filtering to restore the conventional waveform orientation (systolic peaks pointing upward).


## Derived Quantities

### Heart Rate

Computed from inter-peak intervals of the filtered Red channel:

```
BPM = 60 / mean(Δt_peaks)
```

### SpO₂ (Ratio-of-Ratios)

```
R = (AC_red / DC_red) / (AC_ir / DC_ir)
SpO₂ ≈ 110 − 25 × R       # empirical approximation
```

- `DC` = mean of the **raw** channel (slow-varying component)
- `AC` = peak-to-peak amplitude of the **filtered** channel (pulsatile component)

> **NOTE:** `110 − 25R` is a commonly cited empirical approximation. It is **not calibrated** to this specific sensor. For clinically meaningful SpO₂ values, a sensor-specific calibration curve derived from reference oximeter measurements is required.

### SNR

Signal-to-noise ratio is estimated as:

```
SNR = 10 × log₁₀( Var(filtered) / Var(raw − filtered) )   [dB]
```

This treats the filtered signal as "signal" and the residual (raw minus filtered) as "noise".


## Reproducing the Analysis
You can reproduce the analysis by typing the following command. 
```bash
python ppg.py
```

Expected console output:

```
Average BPM: <value>
R (ratio of ratios): <value>
Estimated SpO2: <value>
SNR (Red): <value> dB
SNR (IR): <value> dB
Heart Rate Variability (std of intervals): <value> s
```