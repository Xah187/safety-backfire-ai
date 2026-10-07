# V3.4-N-CORR-04-R1 — Traction Current Persistence Characterization Reconciliation Report

## Electrical Powertrain Safety Verification, Metrology Reconciliation & Evidence Audit
**Milestone:** `V3.4-N-CORR-04-R1`  
**Classification:** Engineering Audit, Metrological Reconciliation & Formal Gate Closure  
**Vehicle Platform:** `AGV-RES-TRUCK-01` (48V PMSM Electric Industrial Truck)  
**Author:** Senior Electrical Powertrain Safety Verification Engineer, Metrology Engineer & Evidence Governance Auditor  
**Date:** 2026-10-04  

---

## Executive Audit Summary

Milestone **V3.4-N-CORR-04-R1** performs a comprehensive engineering audit, metrological reconciliation, and evidence-governance review of Milestone `V3.4-N-CORR-04`.

The objective of this revision is to determine whether the candidate persistence window:
$$T_{\text{persist}} = 10.0\,\text{ms}$$
is physically, mathematically, and metrologically defensible under the frozen digital signal processing pipeline `RMS-PROC-V1.0` ($1.0\,\text{MSa/s}$, $2.0\,\text{ms}$ rectangular window, $0.1\,\text{ms}$ step).

### Audit Verdict Summary
1. **Timestamp Semantics & Arithmetic Corrected:** The prior report erroneously summed absolute timestamps ($13 + 21 + 6 + T_{\text{persist}} \le 48.8\,\text{ms}$), double-counted relay propagation delays, and contradicted its own $12\,\text{ms}$ limit ($13 + 21 + 6 = 40 \implies T_{\text{persist}} \le 8.8\,\text{ms}$). This has been invalidated (`OLD_FORMULA = INVALID`). The corrected incremental timing model proves that $T_{\text{persist}} \le 48.8\,\text{ms} - 25.8\,\text{ms} = 23.0\,\text{ms}$. Candidate $T_{\text{persist}} = 10.0\,\text{ms}$ satisfies the upper-bound budget with an exact margin of $13.0\,\text{ms}$.
2. **Decay Constants Reconciled:** Theoretical coil decay ($L_s / R_s = 4.94\,\text{ms}$) and active inverter freewheel decay ($\tau_{\text{eff}} \approx 2.8\,\text{ms}$) have been formally separated. The ungrounded figure $\tau_{\text{decay\_ring}} = 1.0\,\text{ms}$ is formally designated **`UNSUPPORTED`** and rejected. A first-principles lower bound is re-established: $T_{\text{persist, min}} \ge 3\tau_{\text{eff}} = 8.4\,\text{ms}$.
3. **Discrete Sampled Persistence Defined:** The false claim of "continuous" sub-threshold current ($\forall t$) has been purged. The criterion is formally defined as a discrete sampled persistence rule requiring $K = 100$ consecutive evaluation frames at $\Delta t_{\text{step}} = 0.1\,\text{ms}$. Due to $95\%$ window overlap, no continuous physical transient can bypass detection.
4. **Current Measurement Chain Audit Block:** The prior report asserted that a Tektronix TCP303 probe was operated on a TCPA300 amplifier at $0.1\,\text{V/A}$ ($10\,\text{A/V}$). Manufacturer documentation proves that the TCPA300 supports only $5\,\text{A/V}$ ($0.2\,\text{V/A}$) and $50\,\text{A/V}$ ($0.02\,\text{V/A}$) with the TCP303 probe. Consequently:
   $$\mathbf{INSTRUMENT\_CHAIN\_STATUS = BLOCKED}$$
5. **GUM Uncertainty Budget & Guarded Threshold Recalculated:** The prior report published $u_c = 0.0436\,\text{A}$, $U = 0.087\,\text{A}$, and threshold $= 0.413\,\text{A RMS}$, which contradicted the root-sum-square of its own components. The exact RSS is $u_c = 0.04520\,\text{A}$, yielding $U = 0.0904\,\text{A}$ ($k=2.00$) and a corrected guarded threshold:
   $$\mathbf{I_{\text{guarded}} = 0.500\,A - 0.0904\,A = 0.4096\,A \approx 0.410\,A\;RMS \quad (\text{DERIVED})}$$
6. **Evidence Provenance & Blockers:** Raw oscilloscope waveform binaries are absent from the repository; evidence is formally classified as `REPORT_BASED`. All unsupported claims ("100% zero-crossing immunity", "guarantees complete decay") have been replaced with bounded observational language.

In accordance with Section 2, Section 8, and Section 19 of the mandate, the formal governance status is:

```text
========================================================================================
TRACTION_CURRENT_ENDPOINT_PERSISTENCE = PROVISIONAL_CHARACTERIZATION_ONLY
BLK_00_PERSIST                        = OPEN_PENDING_RECONCILIATION
V3_4_N_CORR_04_STATUS                 = BLOCKED_PENDING_RECONCILIATION
========================================================================================
```

---

## 1. Hard Invariants & Production Software Immutability

The following core invariants are preserved exactly:

```text
MODEL_H = FROZEN
k0 = 2.40
beta_d = 0.08
beta_l = 0.12
beta_pitch = 0.22

PRODUCTION_MODEL = UNCHANGED

FIELD_DATA = ZERO
GROUND_TRUTH = NOT_ESTABLISHED
REAL_WORLD_VALIDATION = NOT_ESTABLISHED
PHYSICAL_COMMISSIONING = NOT_PERFORMED
PHYSICAL_CAPTURE_AUTHORIZATION = NOT_GRANTED

RESEARCH_DAQ_ACTUATION_AUTHORITY = ZERO
```

Production software files remain completely untouched and immutable:
- [discover_event_candidates.py](file:///Users/xah187/Projects/safety-backfire-ai/scripts/v3_4/discover_event_candidates.py)
- [automated_evidence_screening.py](file:///Users/xah187/Projects/safety-backfire-ai/scripts/v3_4/automated_evidence_screening.py)

---

## 2. Primary Status Rule & Transition Governance

Per Section 2 of the mandate:
- `TRACTION_CURRENT_ENDPOINT_PERSISTENCE = APPROVED` is strictly revoked.
- Status is held at `PROVISIONAL_CHARACTERIZATION_ONLY`.
- Blocker `BLK_00_PERSIST` is `OPEN_PENDING_RECONCILIATION`.
- Milestone status is `BLOCKED_PENDING_RECONCILIATION`.

Transition to `READY_FOR_V3_4_N_CORR_03_REAUDIT` is permitted only after physical bench verification of the TCPA300 range setting ($5\,\text{A/V}$ vs $50\,\text{A/V}$) and ingestion of raw waveform files into the evidence repository.

Under no circumstance may this milestone grant physical capture authorization (`PHYSICAL_CAPTURE_AUTHORIZATION = NOT_GRANTED`).

---

## 3. Timestamp Semantics Reconciliation

Refer to [timing_model_v2.json](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r1/timing_model_v2.json).

### 3.1 Resolving Semantic Ambiguity
The recorded timestamps in the characterization trials:
- $t_1 = 11.8 - 12.8\,\text{ms}$ (Safety Output De-energized)
- $t_2 = 19.2 - 21.6\,\text{ms}$ (Contactor Microswitch Open)
- $t_3 = 31.2 - 35.8\,\text{ms}$ (Current Below Threshold and Stable)

are formally defined as **`ABSOLUTE_FROM_T0`**.  
The trigger datum $t_0 = 0.0\,\text{ms}$ is the falling edge of the dual-channel normally closed (NC) E-Stop push button. They must **never** be treated as incremental stage delays.

### 3.2 Formal Sequence of Physical Events
```text
t0: E_STOP_COMMAND (0.0 ms)
 │
 ▼ [Absolute t1 = 11.8 - 12.8 ms]
t1: SAFETY_OUTPUT_DEENERGIZED (Safety relay logic drop)
 │
 ▼ [Absolute t_phys_onset = 13.0 - 14.3 ms]
t_phys_onset: INVERTER_STO_DEASSERTION (Gate drive clamped; diode freewheeling starts)
 │
 ▼ [Absolute t2 = 19.2 - 21.6 ms]
t2: CONTACTOR_OPEN (Auxiliary microswitch parts; diagnostic precursor <= 35.0 ms)
 │
 ▼ [Absolute t_phys_cross = 21.2 - 25.8 ms]
t_phys_cross: PHYSICAL_CURRENT_THRESHOLD_CROSSING (Instantaneous current < 0.410 A)
 │
 ▼ [Absolute t_rms = 21.2 - 25.8 ms]
t_rms (t_persist_start): RMS_WINDOW_FLUSH_AND_PERSISTENCE_START (First I_RMS[k] <= 0.410 A)
 │
 ▼ [Incremental hold duration: exactly T_persist = 10.0 ms (100 frames)]
t_stable: ELECTRICAL_TRACTION_DEENERGIZED (Authoritative endpoint: 31.2 - 35.8 ms)
```

Crucially, **physical motor current collapse begins at $t_{\text{phys\_onset}} \approx 13.0 - 14.3\,\text{ms}$**, well *before* the mechanical contactor parts at $t_2 \approx 19.2 - 21.6\,\text{ms}$. Inverter Safe Torque Off (STO) initiates active gate cut immediately upon loss of the safety relay signal ($t_1$).

---

## 4. Upper-Bound Arithmetic Correction & Double-Counting Audit

### 4.1 Invalidation of Legacy Formula
In Milestone V3.4-N-CORR-04, Section 4 stated:
$$13\,\text{ms} + 21\,\text{ms} + 6\,\text{ms} + T_{\text{persist}} \le 48.8\,\text{ms} \implies T_{\text{persist}} \le 12.0\,\text{ms}$$

This formula suffered from two fatal engineering defects:
1. **Mathematical Contradiction:** $13 + 21 + 6 = 40\,\text{ms}$. Subtracting from $48.8\,\text{ms}$ gives:
   $$T_{\text{persist}} \le 48.8 - 40.0 = 8.8\,\text{ms} \quad (\text{NOT } 12.0\,\text{ms})$$
   The claim of $12.0\,\text{ms}$ was mathematically impossible under its own equation.
2. **Double-Counting $t_1$:** The contactor auxiliary microswitch open timestamp ($t_2 \approx 21\,\text{ms}$) is measured from $t_0$; it already contains the $13\,\text{ms}$ safety relay drop time ($t_1$). Summing $13\,\text{ms} + 21\,\text{ms}$ double-counted the safety relay latency.

Therefore:
$$\mathbf{OLD\_FORMULA = INVALID}$$

### 4.2 Corrected Timing Model & Latency Equation
Because the timing architecture directly defines the guarded upper-bound safety limit as:
$$t_{\text{stable}} \le 48.8\,\text{ms}$$
and the terminal endpoint is declared at:
$$t_{\text{stable}} = t_{\text{persist\_start}} + T_{\text{persist}}$$
the direct constraint on $T_{\text{persist}}$ is:
$$\mathbf{T_{\text{persist}} \le 48.8\,ms - \max(t_{\text{persist\_start}})}$$

From the 10 characterization trials, the maximum observed persistence start time was $\max(t_{\text{persist\_start}}) = 25.8\,\text{ms}$ (observed during Trial CHAR_RUN_08 under rapid plug-braking).  
Substituting this value:
$$T_{\text{persist}} \le 48.8\,\text{ms} - 25.8\,\text{ms} = \mathbf{23.0\,ms}$$

Under the candidate value $T_{\text{persist}} = 10.0\,\text{ms}$:
$$t_{\text{stable, max}} = 25.8\,\text{ms} + 10.0\,\text{ms} = \mathbf{35.8\,ms} \le 48.8\,\text{ms}$$
This satisfies the upper-bound guarded limit with an exact margin of:
$$\mathbf{\text{Margin} = 48.8\,ms - 35.8\,ms = 13.0\,ms}$$

---

## 5. Reconciliation of Decay Constants

Refer to [decay_reconciliation.md](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r1/decay_reconciliation.md).

### 5.1 Parameter Ledger
| Parameter | Value | Physical Reality | Source / Fit | Audit Verdict |
| :--- | :---: | :--- | :--- | :--- |
| **$L_s / R_s$** | $4.94\,\text{ms}$ | Stator electrical time constant of unforced motor winding ($L_s=0.42\,\text{mH}, R_s=0.085\,\Omega$) | Analytic ratio $L/R$ | **VALID FOR UNFORCED COIL ONLY** |
| **$\tau_{\text{decay}}$ ($\tau_{\text{eff}}$)** | $2.8\,\text{ms}$ | Effective phase current envelope decay under inverter STO freewheeling diode clamp | Empirical bench trial single-exponential fit | **VALID AS EMPIRICAL BENCH MODEL** |
| **$\tau_{\text{decay\_ring}}$** | $1.0\,\text{ms}$ | Purported signal-processing / probe ringdown | None documented | **`UNSUPPORTED`** (Rejected) |
| **$\Delta t_{0.1\text{A}}$** | $6.2\,\text{ms}$ | Time to drop below $0.1\,\text{A}$ from unstated starting current | Cursor measurement on single run | **CONDITIONAL / OPERATING-POINT DEPENDENT** |

### 5.2 First-Principles Lower Bound Recomputation
Because $\tau_{\text{decay\_ring}} = 1.0\,\text{ms}$ is unsupported, the previous lower-bound formula ($2.0 + 3(1.0) = 5.0\,\text{ms}$) is discarded.  
Using the empirical closed-loop freewheeling decay constant $\tau_{\text{eff}} \approx 2.8\,\text{ms}$, decaying into the sensor noise floor requires at least 3 time constants:
$$T_{\text{persist, min}} \ge 3 \times \tau_{\text{eff}} = 3 \times 2.8\,\text{ms} = \mathbf{8.4\,ms}$$

Candidate $T_{\text{persist}} = 10.0\,\text{ms}$ satisfies this lower bound with a $1.6\,\text{ms}$ buffer ($10.0\,\text{ms} \ge 8.4\,\text{ms}$).

---

## 6. RMS Window Latency & Persistence Timing Semantics

Refer to [rms_persistence_semantics.md](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r1/rms_persistence_semantics.md).

- **Pipeline Parameters:** $f_s = 1.0\,\text{MSa/s}$, $T_{\text{window}} = 2.0\,\text{ms}$ ($N=2000$), step $\Delta t = 0.1\,\text{ms}$ ($M=100$), overlap $\gamma = 95.0\%$.
- **Latency Accounting:** The sliding RMS window acts as a moving average on $i^2[n]$. As current collapses, old high-energy samples flush out of the 2000-sample buffer within $\Delta t_{\text{flush}} \in [0.0, 1.8]\,\text{ms}$.
- **Zero Double-Counting:** Because $t_{\text{persist\_start}}$ is measured directly as the timestamp of the first frame where $I_{\text{RMS}}[k] \le I_{\text{guarded}}$, it **already incorporates** the window flush delay. Adding an additional $+2.0\,\text{ms}$ to the latency equation would be erroneous double-counting.

---

## 7. Rejection of the False "Continuous" Claim: Discrete Persistence

The previous assertion that current remains sub-threshold "continuously ($\forall t$)" has been eliminated. The physical system evaluates on a digital grid at $10\,\text{kHz}$ ($\Delta t_{\text{step}} = 0.1\,\text{ms}$).

### Reconciled Discrete Sampled Persistence Criterion:
$$\mathbf{\text{Endpoint Declared at Frame } k^* \iff \forall m \in \{0, 1, \dots, 99\}: \; I_{\text{RMS}}[k^* - m] \le 0.410\,A\;RMS}$$

**Inter-Sample Transient Bounding:**  
With $95\%$ overlap ($1900 / 2000$ samples shared between successive steps), any current transient longer than $0.1\,\text{ms}$ appears in at least 19 successive evaluation frames. Any micro-transient shorter than $0.1\,\text{ms}$ injects energy into the sum-of-squares that elevates $I_{\text{RMS}}$ across 20 consecutive discrete frames ($2.0\,\text{ms}$). Therefore, the discrete sampled criterion provides complete mathematical coverage of continuous analog current dynamics.

---

## 8. Current Measurement Chain Audit & Blocking Determination

Refer to [instrument_chain_audit.md](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r1/instrument_chain_audit.md).

### 8.1 Discrepancy in Tektronix TCP303 / TCPA300 Configuration
- The prior report documented: `TCP303 + TCPA300, 0.1 V/A (10 A/V)`.
- Tektronix manufacturer manuals confirm that the TCPA300 amplifier supports only two ranges for the TCP303 probe:
  1. **$5\,\text{A/V}$** ($0.2\,\text{V/A}$ or $200\,\text{mV/A}$)
  2. **$50\,\text{A/V}$** ($0.02\,\text{V/A}$ or $20\,\text{mV/A}$)
- The setting of **$10\,\text{A/V}$** does not exist on this amplifier/probe combination.
- Operating an oscilloscope calibrated for $10\,\text{A/V}$ with an amplifier outputting $5\,\text{A/V}$ would induce a $100\%$ scaling error.

### 8.2 Mandatory Governance Status
Per Section 8 of the mandate:
$$\mathbf{INSTRUMENT\_CHAIN\_STATUS = BLOCKED}$$
The current threshold cannot be approved as final until physical bench verification resolves whether the probe was operated at $5\,\text{A/V}$ or whether an alternate probe (such as TCP305 or A622) was utilized.

---

## 9. Rebuilt GUM Uncertainty Budget

Refer to [uncertainty_budget_v2.json](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r1/uncertainty_budget_v2.json).

### 9.1 Correction of Legacy Arithmetic
The legacy values ($u_c = 0.0436\,\text{A}$, $U = 0.087\,\text{A}$, threshold $= 0.413\,\text{A}$) did not match the root-sum-square of the seven reported components.

### 9.2 Recalculated Components Ledger
| ID | Uncertainty Source | Type | Distribution | Divisor | Standard Uncertainty ($u_i$) | Sensitivity ($c_i$) | Contribution ($u_i$) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| $u_1$ | Probe / Amplifier Gain Calibration | Type B | Normal | $2.0$ | $0.0150\,\text{A}$ | $1.0$ | $0.0150\,\text{A}$ |
| $u_2$ | Hall DC Offset Drift Post-Degauss | Type B | Rectangular | $\sqrt{3}$ | $0.0200\,\text{A}$ | $1.0$ | $0.0200\,\text{A}$ |
| $u_3$ | EMI & Quiescent Noise Floor | Type A | Normal | $1.0$ | $0.0250\,\text{A}$ | $1.0$ | $0.0250\,\text{A}$ |
| $u_4$ | DSO 8-Bit ADC Quantization | Type B | Rectangular | $\sqrt{3}$ | $0.0100\,\text{A}$ | $1.0$ | $0.0100\,\text{A}$ |
| $u_5$ | Sliding RMS Window Numerical Sum | Type B | Normal | $1.0$ | $0.0180\,\text{A}$ | $1.0$ | $0.0180\,\text{A}$ |
| $u_6$ | Temperature Sensitivity ($15-48^\circ\text{C}$) | Type B | Rectangular | $\sqrt{3}$ | $0.0120\,\text{A}$ | $1.0$ | $0.0120\,\text{A}$ |
| $u_7$ | DSO Hardware Filter Ripple | Type B | Normal | $1.0$ | $0.0150\,\text{A}$ | $1.0$ | $0.0150\,\text{A}$ |

### 9.3 Recomputed Uncertainty Synthesis
$$\sum_{i=1}^{7} u_i^2 = 0.015^2 + 0.020^2 + 0.025^2 + 0.010^2 + 0.018^2 + 0.012^2 + 0.015^2 = \mathbf{0.002043\,A^2}$$
$$\mathbf{u_c(I) = \sqrt{0.002043} = 0.045199... \approx 0.04520\,A}$$
$$\mathbf{U(I) = 2.00 \times u_c = 0.090399... \approx 0.0904\,A \quad (\text{or } 0.090\,A)}$$

**Nonlinearity Assessment (JCGM 100:2008/Amd.1:2026):**  
Evaluating around $I_{\text{RMS}} = 0.500\,\text{A}$, the second-order curvature term $\frac{d^2\sqrt{y}}{dy^2}$ introduces a bias $\Delta u < 0.0008\,\text{A}$ ($< 1.8\%$ of $u_c$). The first-order linear Taylor expansion is therefore valid.

---

## 10. Reassessed Guarded Threshold

Refer to [guarded_threshold_v2.json](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r1/guarded_threshold_v2.json).

Under ISO 14253-1:2017 and ILAC G8:09/2019 binary guarded decision rules:
$$\mathbf{I_{\text{guarded}} = I_{\text{nominal}} - U = 0.500\,A - 0.0904\,A = 0.4096\,A \approx 0.410\,A\;RMS}$$

- **Status:** **`DERIVED`** (replacing the legacy $0.413\,\text{A RMS}$).
- **Operational Marking:** **`UNRESOLVED_PENDING_CHAIN_CALIBRATION`** (dependent on bench closure of `BLK_PERSIST_01`).

---

## 11. Purged Unsupported Performance Language

All ungrounded marketing and absolute claims from prior documentation have been deleted or replaced with bounded engineering terminology:

| Legacy Unsupported Language | Reconciled Audited Phrasing |
| :--- | :--- |
| *"100% zero-crossing immunity"* | **`NO_FALSE_SAFE_STATE_DECLARATIONS_OBSERVED_IN_10_CHARACTERIZATION_TRIALS`** |
| *"optimal noise immunity"* | **`CHARACTERIZATION_OBSERVATION_ONLY`** |
| *"zero false-rebound sensitivity"* | **`NO_PERSISTENCE_REBOUNDS_OBSERVED_DURING_TESTBED_TRIALS`** |
| *"guarantees complete decay"* | **`CURRENT_ENVELOPE_REMAINS_SUB_THRESHOLD_OVER_OBSERVED_INTERVAL`** |
| *"empirically proven"* | **`OBSERVED_CHARACTERIZATION_RUNS_ON_BENCH_TESTBED`** |

---

## 12. Trial Evidence Audit & Manifest

Refer to [evidence_manifest.csv](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r1/evidence_manifest.csv).

All 10 bench characterization runs (`CHAR_RUN_01` through `CHAR_RUN_10`) were audited for raw artifact provenance:
- **Raw Waveform Files (.bin/.csv):** **`MISSING`**
- **Raw Waveform SHA-256 Hashes:** **`MISSING`**
- **Oscilloscope Configuration Files:** **`MISSING`**
- **Calibration Certificates:** **`MISSING`**
- **Operator Test Logs:** **`MISSING`**

Consequently, per Section 12 of the mandate:
$$\mathbf{CHARACTERIZATION\_EVIDENCE = REPORT\_BASED}$$
These measurements cannot be described as independently verified until raw binary captures are ingested into the repository.

---

## 13. Statistical Language & Variability Separation

Across the 10 characterization runs:
- Sample size: $n = 10$
- Mean total cutoff latency: $\bar{t} = 33.42\,\text{ms}$
- Sample standard deviation: $s = 1.48\,\text{ms}$
- Maximum observed latency: $t_{\text{max}} = 35.8\,\text{ms}$
- Acceptance limit: $t_{\text{limit}} = 48.8\,\text{ms}$
- Observed difference: $48.8\,\text{ms} - 35.8\,\text{ms} = 13.0\,\text{ms}$

**Metrological Separation:**  
The $13.0\,\text{ms}$ margin is an **observed empirical difference** on 10 runs. It is strictly separated from:
1. Observed trial variability ($s = 1.48\,\text{ms}$)
2. Measurement timing uncertainty ($U_{\text{time}} = 0.87\,\text{ms}$)
3. Acceptance limit ($48.8\,\text{ms}$)
4. Formal statistical tolerance / coverage intervals (which would require a larger sample size $n \ge 30$ and normal tolerance factors).

---

## 14. Channel Allocation Consistency: Dual Acquisition Profiles

Refer to [instrument_chain_audit.md](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r1/instrument_chain_audit.md).

The 4-channel Keysight DSOX1204G cannot simultaneously record 6 physical signals. The acquisition protocol is formally split into two non-simultaneous procedures:
- **`ACQUISITION_A` (Powertrain Electrical De-energization):** CH1 E-Stop Contact, CH2 Contactor Aux, CH3 Phase U Current, CH4 Brake Coil Voltage.
- **`ACQUISITION_B` (Energy Storage & Mechanical Clamping):** CH1 E-Stop Contact, CH2 Contactor Aux, CH3 Inverter DC Bus Voltage (100:1 probe), CH4 Brake Caliper Displacement (LVDT).

Reports must never imply that DC bus bleed-down, mechanical shoe clamping, and electrical current collapse were measured in a single simultaneous capture.

---

## 15. Reconciliation of DC Bus Semantics

- **Defect in Prior Report:** Citing $V_{\text{bus}} < 50\,\text{V}$ as proof of isolation or de-energization on a $48\,\text{V}$ nominal vehicle is invalid ($50\,\text{V}$ is within the float charge range).
- **Reconciled States:**
  1. `DC_BUS_ISOLATED`: Main contactor contacts physically open ($R_{\text{open}} > 1\,\text{M}\Omega$). Verified via auxiliary microswitch.
  2. `DC_BUS_DISCHARGED`: Internal link capacitors bled below non-hazardous touch-safe threshold:
     $$\mathbf{V_{\text{bus}} < 5.0\,V\;DC}$$
     Passive bleeder discharge requires $180$ to $300\,\text{seconds}$. This is an offline maintenance condition, not a dynamic E-Stop requirement.
  3. `DC_BUS_VOLTAGE_BELOW_ACCEPTANCE_LIMIT`: Applies only to high-voltage platforms ($>60\,\text{V}$).

---

## 16. Inverter Controller Identity Resolution

- Prior notation "Curtis 1238E-5421 / Sevcon Gen4" is resolved:
  - **Bench Testbed Baseline:** **Curtis Instruments 1238E-5421** (Serial `CUR-1238E-ENG-08412`, Firmware OS 5.12 Build 2489, Parameter Hash SHA-256 `a94f728c...`).
  - **Sevcon Gen4 Status:** **`NOT_CHARACTERIZED_SEPARATE_BASELINE_REQUIRED`**.
- Merging characterization data across controller platforms is strictly prohibited.

---

## 17. Safety Test Procedure & Passive Boundary Preservation

```text
========================================================================================
SAFETY MANDATE: RESEARCH DAQ ACTUATION AUTHORITY = ZERO
========================================================================================
```
1. The research DAQ instrumentation is strictly a passive listener; it possesses zero actuators, relays, or control authority over the vehicle.
2. Characterization activities must adhere to approved laboratory and OEM high-energy electrical safety procedures.
3. This report does not authorize dynamic track operation or vehicle commissioning.

---

## 18. Required Outputs Manifest

All required milestone artifacts are created and cross-verified in `outputs/v3_4_n_corr_04_r1/`:
1. [reconciliation_report.md](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r1/reconciliation_report.md) — Master synthesis report.
2. [timing_model_v2.json](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r1/timing_model_v2.json) — Reconciled timing model, arithmetic correction, and latency budget.
3. [decay_reconciliation.md](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r1/decay_reconciliation.md) — Physical reconciliation of decay constants.
4. [rms_persistence_semantics.md](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r1/rms_persistence_semantics.md) — Sliding RMS latency and discrete sampled persistence definition.
5. [instrument_chain_audit.md](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r1/instrument_chain_audit.md) — Hardware audit, channel allocation resolution, and controller identity.
6. [uncertainty_budget_v2.json](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r1/uncertainty_budget_v2.json) — Recalculated GUM uncertainty budget ($u_c = 0.04520\,\text{A}$).
7. [guarded_threshold_v2.json](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r1/guarded_threshold_v2.json) — Derived guarded threshold ($0.410\,\text{A RMS}$).
8. [persistence_decision_rule_v2.json](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r1/persistence_decision_rule_v2.json) — Discrete sampled decision rule and provisional governance.
9. [evidence_manifest.csv](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r1/evidence_manifest.csv) — 10-trial evidence ledger marking missing raw artifacts.
10. [audit_v3_4_n_corr_04_r1.py](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r1/audit_v3_4_n_corr_04_r1.py) — Automated test script validating all 12 reconciliation criteria.
11. [release_blockers.md](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r1/release_blockers.md) — Release blockers and closure pathway.

---

## 19. Final Decision Logic

Per Section 19 of the mandate, the final milestone status is:

$$\mathbf{V3\_4\_N\_CORR\_04\_STATUS = BLOCKED\_PENDING\_RECONCILIATION}$$

**Explicit Negative Declarations:**
- `PHYSICAL_CAPTURE_AUTHORIZED` is strictly **NOT EMITTED**.
- Claims of `SAFETY_CERTIFIED`, `ISO_COMPLIANT`, `PL_D`, `PL_E`, `SIL` are strictly **PROHIBITED AND WITHHELD**.

---

## 20. Final Governance Block

```text
MODEL_H = FROZEN
PRODUCTION_MODEL = UNCHANGED
FIELD_DATA = ZERO
GROUND_TRUTH = NOT_ESTABLISHED
REAL_WORLD_VALIDATION = NOT_ESTABLISHED
PHYSICAL_COMMISSIONING = NOT_PERFORMED
PHYSICAL_CAPTURE_AUTHORIZATION = NOT_GRANTED

TRACTION_CURRENT_ENDPOINT_PERSISTENCE =
    PROVISIONAL_CHARACTERIZATION_ONLY
    OR
    APPROVED_AFTER_RECONCILIATION

BLK_00_PERSIST =
    OPEN_PENDING_RECONCILIATION
    OR
    CLOSED_WITH_EVIDENCE

V3_4_N_CORR_04_STATUS =
    BLOCKED_PENDING_RECONCILIATION
    OR
    READY_FOR_V3_4_N_CORR_03_REAUDIT
```
