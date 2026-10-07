# V3.4-N-CORR-04-R2-R1 — Comprehensive Signal Path & Hardware Metrology Reconciliation

**Document Identifier:** `outputs/v3_4_n_corr_04_r2_r1/signal_path_reconciliation_v3.md`  
**Milestone:** `V3.4-N-CORR-04-R2-R1`  
**Classification:** Metrological Hardware Audit, Termination Metrology & Filter Domain Reconciliation  
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

This document reconciles three hardware metrology controversies identified in earlier milestone audits:
1. **Probe Range Traceability:** The contradiction between the historical report claim ($10\,\text{A/V}$) and Tektronix manufacturer specifications ($5\,\text{A/V}$ or $50\,\text{A/V}$).
2. **Termination Voltage Scaling:** Auditing the unverified claim that omitting a $50\,\Omega$ termination feedthrough produces "an exact 2x (100%) scale error."
3. **Hardware Anti-Aliasing Filter Verification:** Formally classifying the status of the purported $20\,\text{kHz}$ hardware low-pass filter on the Keysight DSOX1204G.

---

## 2. Current Measurement Chain Audit & Historical Scale Status

### 2.1 Tektronix TCPA300 + TCP303 Range Audit
According to Tektronix User Manual 071-1183-XX (*TCPA300 & TCPA400 Amplifiers and TCP300 & TCP400 Series Current Probes*):
- Probe Model: **Tektronix TCP303** ($15\,\text{MHz}$ bandwidth, $150\,\text{A}$ continuous / $500\,\text{A}$ peak).
- Amplifier: **Tektronix TCPA300** with automatic TEKPROBE probe interface detection.
- Supported Deflection Settings:
  1. Low Range: **$5\,\text{A/V}$** ($0.2\,\text{V/A}$ or $200\,\text{mV/A}$ into $50\,\Omega$). Maximum linear range: $25\,\text{A}$.
  2. High Range: **$50\,\text{A/V}$** ($0.02\,\text{V/A}$ or $20\,\text{mV/A}$ into $50\,\Omega$). Maximum linear range: $150\,\text{A}$ continuous ($500\,\text{A}$ peak).
- **Non-Existent Setting:** The setting **$10\,\text{A/V}$** does **NOT exist** on the TCPA300 when mated to a TCP303 probe.

### 2.2 Preservation of Unresolved Scale Status
Per Section 9 of the mandate:
$$\mathbf{HISTORICAL\_CURRENT\_SCALE = UNRESOLVED}$$

**Audit Directive:**  
We do **NOT** attempt to infer the historical hardware range by reverse-engineering the reported current numbers. Until original bench instrument configuration logs, calibration certificates, or physical laboratory bench photos establish the exact switch position used during the historical 10 trials, the historical current scale factor remains formally unresolved. The historical trials cannot serve as traceable quantitative evidence.

---

## 3. Metrological Audit of the 50-Ohm Termination Claim

In Milestone V3.4-N-CORR-04-R2 (`signal_path_audit_v2.md`), Section 4.2 asserted:
$$\text{"Operating into an open 1 MOhm input causes a 100% voltage doubling error (2x scale error)."}$$

### 3.1 Forensic Metrological Evaluation
1. **The Theoretical Ideal:** The TCPA300 amplifier output stage has a nominal source impedance of $Z_0 = 50\,\Omega$. When connected via a $50\,\Omega$ characteristic impedance coaxial cable (RG-58) to an oscilloscope:
   - Terminated Load ($R_L = 50\,\Omega$): Voltage division ratio is $\frac{R_L}{Z_0 + R_L} = \frac{50}{50 + 50} = 0.500$.
   - Unterminated High-Impedance Load ($R_L = 1.0\,\text{M}\Omega$): DC voltage division ratio is $\frac{10^6}{50 + 10^6} \approx 0.99995 \approx 1.000$.
   At pure DC ($0\,\text{Hz}$), the unloaded terminal voltage is indeed approximately double ($2.0\times$) the matched $50\,\Omega$ voltage.
2. **The High-Frequency Reality:** Current collapse during E-Stop is a transient containing spectral components from DC up to hundreds of kilohertz (switching harmonics, diode turn-off edges). Coaxial transmission lines operating without matched termination suffer from:
   - Impedance mismatch reflections ($|\Gamma| \approx 1.0$ at DSO end).
   - Frequency-dependent standing waves.
   - Cable capacitance ($C_{\text{cable}} \approx 100\,\text{pF/m}$) forming a resonant tank with the DSO input capacitance ($16\,\text{pF}$) and amplifier output inductance.
   This induces ringing, edge overshoot, and variable attenuation that deviates substantially from an exact flat $2.0\times$ multiplier.

### 3.2 Formal Status Downgrade
Per Section 10 of the mandate, the assertion of an exact 100% scaling error is **DOWNGRADED**:

$$\mathbf{UNTERMINATED\_OUTPUT\_SCALING = NOT\_QUANTITATIVELY\_RECONSTRUCTABLE}$$

Without physical bench measurements of the specific cabling setup, the exact quantitative distortion resulting from improper termination cannot be reconstructed retrospectively.

---

## 4. Keysight DSOX1204G Filter Architecture Audit

In early milestone drafts, an "analog hardware 4th-order low-pass filter at $20\,\text{kHz}$" was asserted as a physical barrier against aliasing.

### 4.1 Forensic Architecture Audit
An inspection of the Keysight DSOX1204G Service and Operating Manuals reveals:
1. **Hardware Analog Bandwidth Limits:** The DSOX1204G analog front-end ASIC provides only two selectable hardware bandwidth limits:
   - Full Bandwidth: $70\,\text{MHz}$ (-3 dB).
   - Analog Bandwidth Limit: $20\,\text{MHz}$ (-3 dB, 2-pole analog filter).
2. **Status of the 20 kHz Setting:** A $20\,\text{kHz}$ low-pass filter is **NOT** present in the analog hardware signal path before the ADC. On this instrument family, a $20\,\text{kHz}$ filter is implemented exclusively in scope DSP firmware as a digital display Math Channel filter.

### 4.2 Conservative Metrological Classification
Per Section 11 of the mandate:

$$\mathbf{20\_KHZ\_ANALOG\_FILTER = NOT\_VERIFIED}$$

### 4.3 Signal Path Isolation Rule
The frozen digital signal processing pipeline `RMS-PROC-V1.0` must process raw digitized samples from the ADC channel directly. **Inserting the oscilloscope's math display filter into the frozen verification chain is strictly PROHIBITED.**

---

## 5. Summary Matrix of Signal Path Metrology

```text
========================================================================================
CURRENT PROBE MODEL               : Tektronix TCP303 (Serial: B020194)
PROBE AMPLIFIER MODEL             : Tektronix TCPA300 (Serial: B010482)
SUPPORTED AMPLIFIER RANGES        : 5 A/V and 50 A/V ONLY
HISTORICAL TRIAL RANGE STATUS     : HISTORICAL_CURRENT_SCALE = UNRESOLVED
UNTERMINATED OUTPUT SCALING       : NOT_QUANTITATIVELY_RECONSTRUCTABLE
ANALOG FRONT-END HARDWARE BW      : 20 MHz / 70 MHz
20 KHZ ANALOG HARDWARE FILTER     : 20_KHZ_ANALOG_FILTER = NOT_VERIFIED
SCOPE MATH CHANNEL FILTER         : EXCLUDED FROM FROZEN PIPELINE
DIGITIZER ADC SAMPLE RATE         : 1.0 MSa/s (Delta_t_s = 1.0 us)
FROZEN PIPELINE                   : RMS-PROC-V1.0 (2.0 ms Rectangular Window, 0.1 ms Step)
INSTRUMENT CHAIN STATUS           : BLOCKED
========================================================================================
```
