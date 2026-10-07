# V3.4-N-CORR-04-R2 — Complete Signal Path & Metrological Chain Audit

**Document Identifier:** `outputs/v3_4_n_corr_04_r2/signal_path_audit_v2.md`  
**Milestone:** `V3.4-N-CORR-04-R2`  
**Classification:** Metrological Hardware Audit, Filter Differentiation & Calibration Traceability  
**Vehicle Platform:** `AGV-RES-TRUCK-01` (48V PMSM Electric Industrial Truck)  
**Governance Invariants:**
```text
MODEL_H                         = FROZEN (k0=2.40, beta_d=0.08, beta_l=0.12, beta_pitch=0.22)
PRODUCTION_MODEL                = UNCHANGED
FIELD_DATA                      = ZERO
GROUND_TRUTH                    = NOT_ESTABLISHED
REAL_WORLD_VALIDATION           = NOT_ESTABLISHED
PHYSICAL_CAPTURE_AUTHORIZATION  = NOT_GRANTED
RESEARCH_DAQ_ACTUATION_AUTHORITY = ZERO
```

---

## 1. Executive Summary & Purpose

Earlier milestone reports asserted that the current measurement chain included an "analog hardware 4th-order low-pass filter at $20\,\text{kHz}$" and cited probe sensitivity as "$0.1\,\text{V/A}$ ($10\,\text{A/V}$)".

Per Section 10 and Section 14 of the V3.4-N-CORR-04-R2 mandate, this document:
1. Rebuilds the physical signal path from motor phase winding to digital processor.
2. Differentiates instrument analog filtering, oscilloscope math filtering, and RMS processing.
3. Refutes the ungrounded assertion of a dedicated $20\,\text{kHz}$ hardware anti-aliasing filter.
4. Determines probe amplifier range compatibility, terminating impedance, and calibration status.
5. Formally declares:
   $$\mathbf{HISTORICAL\_CURRENT\_SCALE = UNRESOLVED}$$

---

## 2. Signal Path Architecture: End-to-End Breakdown

The measurement chain consists of seven distinct physical and digital stages:

```text
Stator Phase U Conductor (High Current AC/DC)
 │
 ▼ [Galvanic isolation / Fluxgate & Hall core]
Tektronix TCP303 Current Probe Head (Serial: B020194)
 │
 ▼ [Proprietary probe interface cable]
Tektronix TCPA300 Current Probe Amplifier (Serial: B010482)
 │
 ▼ [50-Ohm coaxial BNC cable, RG-58, length 1.0 m]
50-Ohm Feedthrough Coaxial Terminator (Tektronix 011-0049-02)
 │
 ▼ [1 MOhm // 16 pF DSO input shunted by 50-Ohm feedthrough]
Keysight DSOX1204G Channel 3 Analog Front-End (Serial: MY58491024)
 │
 ▼ [Pre-ADC Analog Conditioning: 20 MHz Hardware BW Limit]
8-Bit High-Speed Flash ADC (Sampling at 1.0 MSa/s)
 │
 ▼ [Unfiltered 8-bit Raw Quantized Current Stream i[n]]
Digital Signal Processor / Frozen Execution Engine (RMS-PROC-V1.0)
```

---

## 3. Metrological Filter Differentiation & Rebuttal of the "20 kHz Hardware Filter"

In Milestone V3.4-N-CORR-04, Section 2 claimed:
$$\text{"hardware 4th-order low-pass filter at 20 kHz"}$$
An exhaustive audit of the Keysight DSOX1204G oscilloscope hardware architecture reveals:
- **Keysight DSOX1204G Analog Bandwidth:** The analog front-end provides only two hardware bandwidth limit settings:
  1. **Full Bandwidth:** $70\,\text{MHz}$ (-3 dB).
  2. **Bandwidth Limit (BW Limit):** $20\,\text{MHz}$ (-3 dB analog filter).
- **The 20 kHz Filter Reality:** The DSOX1204G does **NOT** contain a $20\,\text{kHz}$ analog hardware filter. A $20\,\text{kHz}$ filter exists on this instrument only as a **digital Math Channel post-processing filter** (DSP low-pass IIR filter applied to display traces).

### 3.1 Strict Separation of the Three Filtering Domains
To preserve metrological integrity, the three distinct filter domains must never be conflated:

| Filter Domain | Physical Layer | Mechanism | Cutoff / Parameters | Status in `RMS-PROC-V1.0` Pipeline |
| :--- | :---: | :--- | :---: | :--- |
| **1. Instrument Analog Front-End** | Hardware Pre-ADC | Analog RC/LC active stage | $20\,\text{MHz}$ analog limit (or $70\,\text{MHz}$ full) | **ACTIVE IN HARDWARE** |
| **2. Scope Math Filter** | Software Post-ADC | Scope firmware digital IIR/FIR filter | $20\,\text{kHz}$ DSP low-pass filter | **NOT PART OF FROZEN PIPELINE**.<br>Must NOT be silently inserted into DAQ processing. |
| **3. Sliding RMS Processing** | Algorithm Pipeline | Rectangular moving-average sum-of-squares | $T_w = 2.0\,\text{ms}$, $\Delta t = 0.1\,\text{ms}$ | **FROZEN INVARIANT (`RMS-PROC-V1.0`)** |

**Audit Rule:** The frozen `RMS-PROC-V1.0` pipeline processes the raw digitized data stream $i[n]$ directly. No unverified oscilloscope math channel filtering may be prepended to the data.

---

## 4. Current Probe Range & Calibration Audit

### 4.1 Manufacturer Range Specifications (Tektronix TCPA300 + TCP303)
According to Tektronix User Manual 071-1183-XX:
- The TCPA300 amplifier automatically detects probe model TCP303.
- Range switch options for TCP303 are restricted to:
  1. **$5\,\text{A/V}$ Range ($0.2\,\text{V/A}$):** Maximum continuous current $25\,\text{A}$ ($5\,\text{V}$ into $50\,\Omega$).
  2. **$50\,\text{A/V}$ Range ($0.02\,\text{V/A}$):** Maximum continuous current $150\,\text{A}$ ($500\,\text{A}$ peak).
- **Non-Existent Range:** The setting **$10\,\text{A/V}$** ($0.1\,\text{V/A}$) is **NOT SUPPORTED** by the hardware.

### 4.2 Termination Integrity
- The TCPA300 amplifier requires a **$50\,\Omega \pm 1\%$ termination load**.
- The Keysight DSOX1204G has fixed $1\,\text{M}\Omega$ input impedance.
- Therefore, a calibrated external **$50\,\Omega$ feedthrough terminator** (e.g. Tektronix 011-0049-02) must be connected directly at the DSO BNC input. Operating into an open $1\,\text{M}\Omega$ input causes a $100\%$ voltage doubling error ($2\times$ scale error).

### 4.3 Calibration State Audit
An audit of testbed `BENCH-TESTBED-E04` reveals:
- Current Probe: Tektronix TCP303 (Serial: `B020194`)
- Probe Amplifier: Tektronix TCPA300 (Serial: `B010482`)
- Calibration Certificate: **`MISSING`**
- ISO/IEC 17025 Calibration Date: **`UNRECORDED`**
- Hardware Range Used in Historical 10 Trials: **`INDETERMINATE`** (Prior report claimed $10\,\text{A/V}$, which is physically impossible on this probe).

---

## 5. Formal Audit Ruling

Because the hardware range setting used during the historical 10 characterization trials cannot be determined from records, and because operating at $5\,\text{A/V}$ vs $50\,\text{A/V}$ introduces a $10\times$ difference in vertical resolution and scaling:

$$\mathbf{HISTORICAL\_CURRENT\_SCALE = UNRESOLVED}$$

$$\mathbf{INSTRUMENT\_CHAIN\_STATUS = BLOCKED}$$

**Remediation Mandate:**  
The 10 historical trials cannot be used as certified quantitative current evidence. A formal re-characterization must be performed on `BENCH-TESTBED-E04` with:
1. The TCPA300 amplifier locked to the physical **$5\,\text{A/V}$ ($0.2\,\text{V/A}$)** range.
2. Verified $50\,\Omega$ coaxial termination installed and checked with a DMM ($50.0\,\Omega \pm 0.2\,\Omega$).
3. Traceable ISO/IEC 17025 calibration certificates archived for both probe and amplifier.
