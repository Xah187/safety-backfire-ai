# V3.4-N-CORR-04-R4 — Current Measurement Traceability & Transducer Forensics

**Document:** `outputs/v3_4_n_corr_04_r4/current_measurement_traceability.md`  
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
HISTORICAL_CURRENT_SCALE        = UNRESOLVED
HISTORICAL_TERMINATION_STATE    = UNRESOLVED
FINAL_STATUS                    = BLOCKED
```

---

## 1. Scope & Metrological Mandate

Metrological traceability requires an unbroken chain of calibrations relating an instrument's readings to international standards (SI units). For current measurements in the de-energization characterization pipeline, this requires full auditability of the Tektronix TCP303 current probe, TCPA300 amplifier, range selection, termination impedance, degauss/autobalance procedure, and uncertainty contributions.

**Audit Governance Rules:**
1. Use strictly manufacturer-supported terminology and ratings from Tektronix technical specifications.
2. For each historical trial, `RANGE = UNKNOWN` unless direct primary evidence exists.
3. Preserve `HISTORICAL_CURRENT_SCALE = UNRESOLVED`.
4. Do **NOT** reverse-engineer range or termination settings from reported numerical current values.

---

## 2. Manufacturer Specifications: Tektronix TCP303 on TCPA300

The Tektronix TCPA300 amplifier operates with the TCP303 AC/DC current probe to provide two selectable hardware range settings: $5\,\text{A/V}$ and $50\,\text{A/V}$. 

*(Note: There is no $10\,\text{A/V}$ range on the TCPA300 amplifier; historical mentions of $10\,\text{A/V}$ were erroneous).*

### 2.1 Authoritative Product Ratings (Terminated into $50\,\Omega$)

| Specification / Parameter | Range Setting: **5 A/V** | Range Setting: **50 A/V** | Units & Conditions |
| :--- | :---: | :---: | :--- |
| **Output Transfer Factor (Nominal)** | $0.200$ | $0.020$ | $\text{V/A}$ (into $50\,\Omega$ load) |
| **Continuous Maximum DC Current** | $25.0$ | $150.0$ | $\text{A DC}$ (thermal limit) |
| **Continuous Maximum RMS Current** | $17.7$ | $150.0$ | $\text{A RMS}$ (sinusoidal waveform) |
| **Peak Pulse Current** | $500.0$ | $500.0$ | $\text{A peak}$ (non-continuous pulse) |
| **Maximum Amp-Second Product** | $0.010$ ($10$) | $0.030$ ($30$) | $\text{A}\cdot\text{s}$ ($\text{A}\cdot\text{ms}$) (core saturation limit) |
| **Analog Bandwidth ($-3\,\text{dB}$)** | $\text{DC} - 15$ | $\text{DC} - 15$ | $\text{MHz}$ |
| **Rise Time ($10\% - 90\%$)** | $\le 23$ | $\le 23$ | $\text{ns}$ |
| **DC Accuracy (Calibrated)** | $\pm 1.0\%$ | $\pm 1.0\%$ | of reading (with TCPA300 calibrated) |
| **Insertion Impedance at 1 MHz** | $0.08$ | $0.08$ | $\Omega$ |

### 2.2 Reconciling Continuous vs. Pulse Ratings
- On the **$5\,\text{A/V}$ setting**:
  - The continuous thermal limit is **$25.0\,\text{A DC}$** or **$17.7\,\text{A RMS}$** ($25/\sqrt{2}\,\text{A}$).
  - Currents exceeding $25\,\text{A}$ are permitted **only as transient pulses** whose integral does not exceed the core saturation Amp-Second rating ($0.010\,\text{A}\cdot\text{s}$). A $100\,\text{A}$ transient, for instance, saturates the core if sustained longer than $100\,\mu\text{s}$.
- On the **$50\,\text{A/V}$ setting**:
  - The probe supports **$150.0\,\text{A DC}$** and **$150.0\,\text{A RMS}$** continuous current.
  - The core saturation limit allows pulses up to $500.0\,\text{A}$ peak ($0.030\,\text{A}\cdot\text{s}$).

---

## 3. The "~115 A" Historical Trial Conflict

Historical reports and earlier audit text cited an operating stator current of $\sim 115\,\text{A}$ prior to E-Stop de-energization.

### 3.1 The Engineering Dilemma
1. **If the probe was set to $5\,\text{A/V}$:**  
   A current of $\sim 115\,\text{A}$ exceeds the continuous DC ($25\,\text{A}$) and RMS ($17.7\,\text{A}$) ratings by a factor of 4.6 to 6.5. Unless the $\sim 115\,\text{A}$ occurred as a very short transient pulse ($< 87\,\mu\text{s}$), operating at $\sim 115\,\text{A}$ on $5\,\text{A/V}$ would induce core saturation, severe non-linear clipping, and overheating.
2. **If the probe was set to $50\,\text{A/V}$:**  
   A current of $\sim 115\,\text{A}$ is within the $150\,\text{A}$ continuous rating. However, at $50\,\text{A/V}$, the de-energization threshold of $0.410\,\text{A RMS}$ produces an output voltage of only:
   $$V_{\text{out}} = 0.410\,\text{A} \times 0.020\,\text{V/A} = 8.20\,\text{mV}$$
   On an 8-bit oscilloscope (Keysight DSOX1204G) operating on a typical vertical scale to capture $\sim 115\,\text{A}$ ($2.3\,\text{V}$ peak $\implies 500\,\text{mV/div}$ across 8 divisions = $4\,\text{V}$ full scale), the ADC quantization step is:
   $$\text{LSB} = \frac{4.0\,\text{V}}{256} \approx 15.6\,\text{mV}$$
   At $\text{LSB} \approx 15.6\,\text{mV}$, an $8.2\,\text{mV}$ threshold lies **below 1 LSB**, making sub-ampere threshold detection physically impossible without severe quantization distortion!

### 3.2 Forensic Verdict: No Reverse-Engineering
It is tempting to deduce that operators either changed ranges mid-test or used $50\,\text{A/V}$ with dual-channel scaling. However, **reverse-engineering hardware settings from numerical values is strictly prohibited**. 

No oscilloscope setup file, range switch log, or amplifier telemetry exists in the repository. Therefore:
```text
HISTORICAL_RANGE_SETTING = UNKNOWN (for all 10 trials)
HISTORICAL_CURRENT_SCALE = UNRESOLVED
```

---

## 4. Termination & Signal Path Integrity

The Tektronix TCPA300 amplifier is designed strictly to drive a **$50\,\Omega$ load**.

### 4.1 Termination Requirements
- The oscilloscope channel input impedance must be set to $50\,\Omega$ (or a precision external $50\,\Omega$ BNC feedthrough terminator must be installed at the scope input).
- If the oscilloscope channel is set to high impedance ($1\,\text{M}\Omega$):
  - At DC and low frequencies, the open-circuit voltage doubles:
    $$V_{\text{open}} = 2 \times V_{\text{matched}}$$
    This produces a factor-of-2 scaling error (e.g. $0.4\,\text{V/A}$ instead of $0.2\,\text{V/A}$ on $5\,\text{A/V}$).
  - At higher frequencies, transmission-line reflections between the cable and the high-impedance scope input create frequency-dependent standing waves, ringing, and phase distortion.

### 4.2 Historical Evidence Status
- Keysight DSOX1204G oscilloscopes feature standard $1\,\text{M}\Omega$ inputs; $50\,\Omega$ internal termination is not available on this economy tier (requires an external $50\,\Omega$ feedthrough terminator).
- There is zero record of whether external $50\,\Omega$ terminators were installed during historical trials.
- Consequently:
```text
HISTORICAL_TERMINATION_STATE    = UNRESOLVED
UNTERMINATED_OUTPUT_SCALING     = NOT_QUANTITATIVELY_RECONSTRUCTABLE
```

---

## 5. Calibration Status & Metrological Traceability

| Equipment Model | Asserted Serial Number | Repository Asset Record | Calibration Certificate | Status |
| :--- | :--- | :---: | :---: | :---: |
| **Tektronix TCP303** | `B020194` | `MISSING` | `MISSING` | `UNVERIFIED_PROVENANCE` |
| **Tektronix TCPA300** | `B010482` | `MISSING` | `MISSING` | `UNVERIFIED_PROVENANCE` |
| **Keysight DSOX1204G**| `MY58491024` | `MISSING` | `MISSING` | `UNVERIFIED_PROVENANCE` |

- **Degauss and AutoBalance:** The TCPA300 requires a mandatory Degauss/AutoBalance routine prior to capture to eliminate residual core magnetization and DC offset. No laboratory record, operator checklist, or baseline voltage offset log exists.
- **Uncertainty Contributions:** With calibration missing, transducer gain error, DC offset drift, core hysteresis, and vertical digitizer error cannot be bounded.

---

## 6. Formal Traceability Conclusion

1. The current measurement scale used in historical characterization runs (`CHAR_RUN_01` – `CHAR_RUN_10`) cannot be established from repository evidence.
2. The sub-ampere threshold ($0.410\,\text{A}$) cannot be quantitatively linked to physical stator Amperes.
3. Therefore:
```text
CURRENT_MEASUREMENT_TRACEABILITY = BLOCKED
HISTORICAL_CURRENT_SCALE        = UNRESOLVED
CALIBRATION_EVIDENCE            = MISSING
SERIAL_NUMBERS                  = UNVERIFIED_PROVENANCE
```
