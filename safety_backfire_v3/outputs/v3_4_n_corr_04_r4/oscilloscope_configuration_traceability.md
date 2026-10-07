# V3.4-N-CORR-04-R4 — Oscilloscope Configuration Traceability & Capability Forensics

**Document:** `outputs/v3_4_n_corr_04_r4/oscilloscope_configuration_traceability.md`  
**Milestone:** V3.4-N-CORR-04-R4 (Evidence Readiness, Dependency Closure & Traceability Audit)  
**Governance Invariants:**
```text
MODEL_H                         = FROZEN (k0=2.40, beta_d=0.08, beta_l=0.12, beta_pitch=0.22)
PRODUCTION_MODEL                = UNCHANGED
FIELD_DATA                      = ZERO
GROUND_TRUTH                    = NOT_ESTABLISHED
REAL_WORLD_VALIDATION           = NOT_ESTABLISHED
PHYSICAL_CAPTURE_AUTHORIZATION  = NOT_GRANTED
RESEARCH_DAQ_ACTUATION_AUTHORITY = ZERO
FINAL_STATUS                    = BLOCKED
```

---

## 1. Governance Principle: Instrument Capability vs. Historical Configuration

A critical flaw in early milestone evaluations was conflating what an instrument is **capable** of doing with what was **actually configured** during a specific test run.

**Authoritative Governance Rule:**  
The capability of an oscilloscope (as published in manufacturer datasheets) **SHALL NOT** be accepted as evidence that a feature was enabled, calibrated, or active during historical trials. Historical configuration requires primary machine-readable setup files (`.setup`, `.xml`), unedited oscillogram headers, or sworn laboratory operator logs.

---

## 2. Configuration Audit Matrix (Keysight DSOX1204G)

Below is the exhaustive forensic audit of fourteen oscilloscope configuration parameters, separating manufacturer hardware capabilities from verified repository evidence:

| # | Configuration Parameter | Keysight DSOX1204G Manufacturer Capability | Historical Bench Evidence (CHAR_RUN_01–10) | Evidence Status | Metrological Impact of Missing Evidence |
| :-: | :--- | :--- | :--- | :---: | :--- |
| **1** | **Exact Model & Serial** | Keysight InfiniiVision DSOX1204G (4 channels, $70\,\text{MHz}$ standard). | Asserted as `"Keysight DSOX1204G s/n MY58491024"`. Zero physical inventory logs, photos, or purchase records exist. | `UNVERIFIED_PROVENANCE` | Instrument identity cannot be audited. |
| **2** | **Hardware Bandwidth Option** | Base: $70\,\text{MHz}$. Optional software licenses: DSOX1B100 ($100\,\text{MHz}$), DSOX1B200 ($200\,\text{MHz}$). | Unrecorded. Unknown whether base unit or upgraded option was present. | `MISSING` | True analog channel front-end cutoff frequency is unverified. |
| **3** | **Sample Rate** | Up to $2.0\,\text{GSa/s}$ interleaved ($1.0\,\text{GSa/s}$ all channels). | Asserted as $1.0\,\text{MSa/s}$ in documentation. Timebase setting ($\text{s/div}$) that produced this rate is unrecorded. | `UNVERIFIED` | Native ADC rate and sample-clock stability cannot be established. |
| **4** | **Memory Depth** | Up to $2\,\text{Mpts}$ interleaved ($1\,\text{Mpts}$ per channel). | Unrecorded. Total acquisition buffer length is unknown. | `MISSING` | Prevents verification of total capture duration and buffer rollover behavior. |
| **5** | **Acquisition Mode** | Selectable: Normal, Peak Detect, Averaging, High Resolution (ERES). | Unrecorded. Completely absent from historical files. | `MISSING` | Peak Detect would distort RMS; High-Res would act as an unmodeled digital filter; Normal would cause aliasing. |
| **6** | **Averaging Factor** | Selectable: 2 to 65,536 averages (requires repetitive triggers). | Unrecorded. | `MISSING` | If averaging was used, transient decay would be corrupted across multi-shot cycles. |
| **7** | **Interpolation** | Selectable: $\sin(x)/x$ or Linear interpolation. | Unrecorded. | `MISSING` | Unknown whether sub-sample points were reconstructed via $\sin(x)/x$. |
| **8** | **Digital Filters** | Math channel digital low-pass / high-pass filter available in UI. | CORR-04 claimed filter; R2-R1 refuted it. Actual Math menu state unrecorded. | `MISSING` | Cannot determine whether raw channel or filtered math trace was exported. |
| **9** | **Analog Bandwidth Limit** | Selectable hardware $20\,\text{MHz}$ ($-3\,\text{dB}$) low-pass filter. | Unrecorded. Unknown whether $20\,\text{MHz}$ limit was toggled ON or OFF. | `MISSING` | Signal path bandwidth above $20\,\text{MHz}$ is unconstrained. |
| **10** | **Channel Termination** | Native: $1\,\text{M}\Omega \pm 1\%$ ($16\,\text{pF}$). **No internal $50\,\Omega$ termination exists.** | Unrecorded. No record of external $50\,\Omega$ feedthrough terminator exists. | `MISSING` | Unterminated $1\,\text{M}\Omega$ load causes reflection ringing and $\times 2$ DC scaling error. |
| **11** | **Vertical Scale** | $500\,\mu\text{V/div}$ to $10\,\text{V/div}$ in 1-2-5 sequence (at $1\,\text{M}\Omega$). | Unrecorded for all 10 trials (`MISSING`). | `MISSING` | Quantization step ($\text{LSB}$) and dynamic range are completely unknown. |
| **12** | **Probe Attenuation / Scale** | Selectable: 0.1X to 10,000X, or custom Current-per-Volt ratio. | Unrecorded whether scope was set to 1X, 5 A/V, 50 A/V, or custom. | `MISSING` | Voltage-to-current conversion factor is unverifiable. |
| **13** | **Trigger Mode & Type** | Auto, Normal, Single. Types: Edge, Pulse Width, Pattern. | Unrecorded. Trigger slope and coupling (DC, AC, LF Reject) unrecorded. | `MISSING` | Retriggering conditions and trigger arming latency are unknown. |
| **14** | **Trigger Position / Delay** | Horizontal delay adjustable from $-1\,\text{div}$ to $+500\,\text{s}$. | Manifest asserts `0.0 ms`, but trigger position relative to grid center is unrecorded. | `MISSING` | Time alignment between physical E-Stop switch contact and $t=0$ is unanchored. |

---

## 3. Analysis of Critical Missing Settings

### 3.1 The Acquisition Mode Ambiguity
The DSOX1204G acquisition mode dictates the fundamental signal integrity of downsampled waveforms:
- **Normal Mode:** The digitizer samples at its native high rate ($1 - 2\,\text{GSa/s}$) and decimates to the target sample depth by decimation (dropping intermediate samples). This creates severe aliasing if high-frequency inverter ringing ($1 - 15\,\text{MHz}$) is present.
- **High Resolution (ERES) Mode:** The digitizer boxcar-averages consecutive high-speed samples within each sample interval. This provides digital anti-aliasing and increases vertical resolution (up to 12 bits), but introduces an uncharacterized moving-average group delay that shifts threshold crossing times.
- **Peak Detect Mode:** The digitizer preserves the maximum and minimum peaks within each decimation interval to catch narrow glitches. This artificially inflates the envelope, preventing current from decaying below threshold.

Because no setup file was archived, it is impossible to determine which mode generated the historical data.

### 3.2 The Vertical Scaling & Quantization Noise Floor
The DSOX1204G utilizes an 8-bit analog-to-digital converter ($256$ discrete quantization levels). 
- If an acquisition was scaled to capture the full operating current envelope ($\sim 115\,\text{A}$ on $50\,\text{A/V} = 2.3\,\text{V}$ peak), the vertical scale would be configured to $500\,\text{mV/div}$ ($4.0\,\text{V}$ full vertical window across 8 divisions).
- The quantization resolution is:
  $$\Delta V = \frac{4.0\,\text{V}}{256} = 15.625\,\text{mV}$$
- Converted through the $50\,\text{A/V}$ transfer factor ($0.02\,\text{V/A}$):
  $$\Delta I = \frac{15.625\,\text{mV}}{0.02\,\text{V/A}} = 0.781\,\text{A per LSB}$$
- **Critical Finding:** Under this configuration, the entire guarded threshold ($0.410\,\text{A}$) represents **roughly half of a single LSB** ($\sim 0.52\,\text{LSB}$). The digitizer cannot resolve $0.410\,\text{A}$; the reading toggles between $0.0\,\text{A}$ and $0.781\,\text{A}$ with severe quantization noise!
- Without knowing the vertical scale setting, the metrological validity of sub-ampere measurements is void.

---

## 4. Oscilloscope Traceability Verdict

```text
OSCILLOSCOPE_MODEL_PROVENANCE        = UNVERIFIED
OSCILLOSCOPE_CONFIGURATION_EVIDENCE = MISSING (All 14 parameters)
ACQUISITION_MODE                    = UNDOCUMENTED
VERTICAL_SCALE_LSB_RESOLUTION       = INDETERMINATE
OSCILLOSCOPE_TRACEABILITY_STATUS    = BLOCKED
```
