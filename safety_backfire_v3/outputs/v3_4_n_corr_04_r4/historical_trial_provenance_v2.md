# V3.4-N-CORR-04-R4 — Historical Trial Provenance Audit (v2)

**Document:** `outputs/v3_4_n_corr_04_r4/historical_trial_provenance_v2.md`  
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
TIMING_EVIDENCE                 = REPORT_BASED
HISTORICAL_CURRENT_SCALE        = UNRESOLVED
FINAL_STATUS                    = BLOCKED
```

---

## 1. Forensic Audit Governance Rules

1. Every item for which primary physical evidence does not exist in the repository **SHALL** be explicitly designated as `MISSING`.
2. Prohibited Terms: Do **NOT** record `INFERRED`, `PROBABLY`, or `ASSUMED` as factual evidence. If an inference exists in historical documentation, it must be flagged explicitly as an unverified narrative assertion.
3. Preserve `TIMING_EVIDENCE = REPORT_BASED`.
4. Preserve `HISTORICAL_CURRENT_SCALE = UNRESOLVED`.

---

## 2. Trial-by-Trial Provenance Audit (CHAR_RUN_01 – CHAR_RUN_10)

Below is the definitive forensic provenance audit across all ten historical characterization runs documented in `evidence_manifest_v3.csv`:

### 2.1 Master Provenance Matrix

| Trial ID | Test Condition Description | Raw Waveform | Setup File | Instrument Identity | Range Setting | Termination | Calibration Record | Operator Log | Timestamp Source | Trigger Config | Motor/Controller Config | Waveform SHA-256 | Evidence Class |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`CHAR_RUN_01`** | Low Speed Forward (10 Hz, 15% torque) | `MISSING` | `MISSING` | `UNVERIFIED` | `MISSING` | `MISSING` | `MISSING` | `MISSING` | `MISSING` | `MISSING` | `MISSING` | `MISSING` | `REPORT_BASED` |
| **`CHAR_RUN_02`** | Low Speed Reverse (10 Hz, 15% torque) | `MISSING` | `MISSING` | `UNVERIFIED` | `MISSING` | `MISSING` | `MISSING` | `MISSING` | `MISSING` | `MISSING` | `MISSING` | `MISSING` | `REPORT_BASED` |
| **`CHAR_RUN_03`** | Mid Speed Forward (45 Hz, 50% torque) | `MISSING` | `MISSING` | `UNVERIFIED` | `MISSING` | `MISSING` | `MISSING` | `MISSING` | `MISSING` | `MISSING` | `MISSING` | `MISSING` | `REPORT_BASED` |
| **`CHAR_RUN_04`** | Mid Speed Reverse (45 Hz, 50% torque) | `MISSING` | `MISSING` | `UNVERIFIED` | `MISSING` | `MISSING` | `MISSING` | `MISSING` | `MISSING` | `MISSING` | `MISSING` | `MISSING` | `REPORT_BASED` |
| **`CHAR_RUN_05`** | Rated Speed Forward (90 Hz, 100% torque) | `MISSING` | `MISSING` | `UNVERIFIED` | `MISSING` | `MISSING` | `MISSING` | `MISSING` | `MISSING` | `MISSING` | `MISSING` | `MISSING` | `REPORT_BASED` |
| **`CHAR_RUN_06`** | Rated Speed Reverse (90 Hz, 100% torque) | `MISSING` | `MISSING` | `UNVERIFIED` | `MISSING` | `MISSING` | `MISSING` | `MISSING` | `MISSING` | `MISSING` | `MISSING` | `MISSING` | `REPORT_BASED` |
| **`CHAR_RUN_07`** | High Speed Forward (Field Weakening, 120 Hz) | `MISSING` | `MISSING` | `UNVERIFIED` | `MISSING` | `MISSING` | `MISSING` | `MISSING` | `MISSING` | `MISSING` | `MISSING` | `MISSING` | `REPORT_BASED` |
| **`CHAR_RUN_08`** | Cold Start (+5°C ambient, 45 Hz, 50% torque) | `MISSING` | `MISSING` | `UNVERIFIED` | `MISSING` | `MISSING` | `MISSING` | `MISSING` | `MISSING` | `MISSING` | `MISSING` | `MISSING` | `REPORT_BASED` |
| **`CHAR_RUN_09`** | Elevated Temp (+45°C ambient, 45 Hz, 50% torque)| `MISSING` | `MISSING` | `UNVERIFIED` | `MISSING` | `MISSING` | `MISSING` | `MISSING` | `MISSING` | `MISSING` | `MISSING` | `MISSING` | `REPORT_BASED` |
| **`CHAR_RUN_10`** | Maximum Step Torque Transition to E-Stop | `MISSING` | `MISSING` | `UNVERIFIED` | `MISSING` | `MISSING` | `MISSING` | `MISSING` | `MISSING` | `MISSING` | `MISSING` | `MISSING` | `REPORT_BASED` |

---

## 3. Forensic Analysis of Historical Artifact Absence

### 3.1 Raw Waveforms and Setup Files
- Zero machine-readable time-series data files (`.csv`, `.bin`, `.wfm`, `.mat`, `.h5`) exist in the repository for any of the ten characterization trials.
- Zero oscilloscope setup files (`.setup`, `.xml`) or amplifier telemetry dumps exist.
- Consequently, the fundamental raw voltage waveforms $V_{\text{scope}}(t)$ that allegedly produced the reported current numbers cannot be audited or re-processed.

### 3.2 Cryptographic Integrity (SHA-256)
- In `evidence_manifest_v3.csv`, the column `raw_waveform_sha256` contains the string `"MISSING"` across all ten rows.
- No cryptographic checksums were recorded when historical trials were conducted. Data tampering, accidental file corruption, or transcribing errors cannot be ruled out.

### 3.3 Derived Nature of Manifest Timing Columns
As discovered and verified in Milestone R3 (Finding R3-E08), the timing columns in `evidence_manifest_v3.csv` exhibit artificial mathematical coupling:
$$\Delta_{\text{flush\_ms}} = 1.12\,\text{ms} \quad \text{(identical for all 10 trials)}$$
$$t_{\text{phys\_envelope\_cross\_ms}} = t_{\text{rms\_threshold\_cross\_ms}} - 1.12\,\text{ms} \quad \text{(identical subtraction)}$$
While reported RMS threshold crossing times vary across runs ($21.80\,\text{ms}, 21.20\,\text{ms}, 23.40\,\text{ms}, \dots, 25.80\,\text{ms}$), the offset between RMS crossing and physical crossing is perfectly invariant at $1.12\,\text{ms}$.
In real physical acquisitions, variation in initial current, phase angle at E-Stop, contactor arc duration, and sample-clock phase jitter produces physical offset jitter of $\pm 0.1 - 0.3\,\text{ms}$.
**Forensic Proof:** The column `t_phys_envelope_cross_ms` is a **derived mathematical calculation** obtained by subtracting the theoretical constant $1.12\,\text{ms}$ from `t_rms_threshold_cross_ms`. It is **NOT** an independent physical measurement!

---

## 4. Evidentiary Conclusion

1. The ten historical runs `CHAR_RUN_01` through `CHAR_RUN_10` are purely **report-based narrative summaries** originating from unlocated documentation.
2. They do not constitute empirical validation of:
   - Stator current decay time constant ($\tau_{\text{eff}}$);
   - Flush lag latency ($\Delta_{\text{flush}}$);
   - Persistence duration ($T_{\text{persist}} = 10.0\,\text{ms}$);
   - Sub-ampere de-energization threshold ($0.410\,\text{A}$).
3. Status:
```text
HISTORICAL_TRIAL_EVIDENCE       = REPORT_BASED
RAW_WAVEFORMS                   = MISSING (0 of 10 available)
SETUP_CONFIGURATIONS            = MISSING (0 of 10 available)
METROLOGICAL_TRACEABILITY       = ZERO
EMPIRICAL_VALIDATION_STATUS     = NOT_ESTABLISHED
```
