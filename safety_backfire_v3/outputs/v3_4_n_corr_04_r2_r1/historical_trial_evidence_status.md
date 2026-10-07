# V3.4-N-CORR-04-R2-R1 — Historical Trial Evidence Status Ledger

**Document Identifier:** `outputs/v3_4_n_corr_04_r2_r1/historical_trial_evidence_status.md`  
**Milestone:** `V3.4-N-CORR-04-R2-R1`  
**Classification:** Evidence Governance & Forensic Data Provenance Audit  
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

## 1. Executive Summary & Authoritative Status

Milestones V3.4-N-CORR-04 and V3.4-N-CORR-04-R1/R2 referenced a dataset of 10 characterization trials (`CHAR_RUN_01` through `CHAR_RUN_10`) conducted on bench testbed `BENCH-TESTBED-E04`.

Per Section 14 of the V3.4-N-CORR-04-R2-R1 mandate:
1. **Report-Based Classification:** The historical trials exist exclusively as aggregated summary numbers in JSON report tables. All raw digitized oscillograms, scope setup files, and calibration certificates are **`MISSING`**.
2. **Preservation of Immutable Governance Status:**
   $$\mathbf{TIMING\_EVIDENCE = REPORT\_BASED}$$
   $$\mathbf{HISTORICAL\_CURRENT\_SCALE = UNRESOLVED}$$
3. **Prohibition on Data Reconstruction:** Fabricating or interpolating missing raw time-series binaries is strictly **PROHIBITED**.
4. **Prohibition on Empirical Validation Claims:** Claiming that these historical trials provide "empirical validation" of the analytical $1.117\,\text{ms}$ RMS offset or the $10.0\,\text{ms}$ persistence duration is strictly **PROHIBITED**.

---

## 2. Trial-by-Trial Evidence Audit Ledger

| Trial ID | Operating Condition | Raw Waveform Binary | SHA-256 Hash | Oscilloscope Setup File | Hardware Range Setting | Calibration Certificate | Evidence Classification |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **`CHAR_RUN_01`** | Low Speed Forward (10 Hz, 15% torque) | `MISSING` | `MISSING` | `MISSING` | `INDETERMINATE` | `MISSING` | `REPORT_BASED` |
| **`CHAR_RUN_02`** | Medium Speed Forward (30 Hz, 30% torque) | `MISSING` | `MISSING` | `MISSING` | `INDETERMINATE` | `MISSING` | `REPORT_BASED` |
| **`CHAR_RUN_03`** | Rated Speed Forward (60 Hz, 50% torque) | `MISSING` | `MISSING` | `MISSING` | `INDETERMINATE` | `MISSING` | `REPORT_BASED` |
| **`CHAR_RUN_04`** | Full Torque Low Speed (15 Hz, 100% torque) | `MISSING` | `MISSING` | `MISSING` | `INDETERMINATE` | `MISSING` | `REPORT_BASED` |
| **`CHAR_RUN_05`** | High Speed Field Weakening (90 Hz, 25% torque) | `MISSING` | `MISSING` | `MISSING` | `INDETERMINATE` | `MISSING` | `REPORT_BASED` |
| **`CHAR_RUN_06`** | Reverse Low Speed (-20 Hz, 30% torque) | `MISSING` | `MISSING` | `MISSING` | `INDETERMINATE` | `MISSING` | `REPORT_BASED` |
| **`CHAR_RUN_07`** | Reverse Rated Speed (-60 Hz, 50% torque) | `MISSING` | `MISSING` | `MISSING` | `INDETERMINATE` | `MISSING` | `REPORT_BASED` |
| **`CHAR_RUN_08`** | Rapid Dynamic Plug Braking Transient | `MISSING` | `MISSING` | `MISSING` | `INDETERMINATE` | `MISSING` | `REPORT_BASED` |
| **`CHAR_RUN_09`** | Standstill Holding Torque (0 Hz, 80% torque) | `MISSING` | `MISSING` | `MISSING` | `INDETERMINATE` | `MISSING` | `REPORT_BASED` |
| **`CHAR_RUN_10`** | Stabilized Repeat Baseline (60 Hz, 50% torque) | `MISSING` | `MISSING` | `MISSING` | `INDETERMINATE` | `MISSING` | `REPORT_BASED` |

---

## 3. Forensic Critique of Historical Timing Numbers

In the historical summary tables, the reported timestamps were:
- `t_safety_output_ms`: $11.8 - 12.8\,\text{ms}$
- `t_contactor_open_ms`: $19.2 - 21.6\,\text{ms}$
- `t_threshold_crossing_ms`: $21.2 - 25.8\,\text{ms}$
- `t_current_stable_ms`: $31.2 - 35.8\,\text{ms}$

### Forensic Findings:
1. **Identical Offset Flaw:** In every single run, $t_{\text{current\_stable\_ms}} - t_{\text{threshold\_crossing\_ms}} \equiv 10.0\,\text{ms}$ identically. This indicates that $t_{\text{stable}}$ was not an independently recorded signal event, but an arithmetic addition of an assumed $10.0\,\text{ms}$ hold.
2. **Omission of Filter Lag:** Physical envelope crossing and RMS crossing were assigned identical numbers. The analytical flush lag ($\Delta_{\text{flush}} = 1.12\,\text{ms}$) proved in [rms_closed_form.md](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r2/rms_closed_form.md) was completely absent from the historical records.
3. **Traceability Failure:** Without raw waveform files, there is zero cryptographic proof that these captures were taken on `AGV-RES-TRUCK-01` or that the current probe was nulled and calibrated.

---

## 4. Final Evidence Classification & Disposition

The historical 10 characterization runs are formally classified as:

$$\mathbf{CHARACTERIZATION\_EVIDENCE = REPORT\_BASED\_NARRATIVE\_ONLY}$$

**Mandatory Invalidation Rules:**
1. These runs **CANNOT** be treated as traceable quantitative evidence.
2. These runs **CANNOT** close Milestone V3.4-N-CORR-04 or Milestone V3.4-N-CORR-03.
3. Closure requires an entirely new set of 10 controlled bench characterization runs executed under an audited procedure, with raw digitized waveforms archived in binary/HDF5 format, verified cryptographic SHA-256 hashes, traceable calibration certificates, and physical range switch confirmation.
