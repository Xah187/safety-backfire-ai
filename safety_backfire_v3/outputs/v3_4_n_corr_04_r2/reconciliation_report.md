# V3.4-N-CORR-04-R2 — Persistence Decision Model Reconciliation Report

## Electrical Powertrain Safety Verification, Metrology Reconciliation & Decision Model Audit
**Milestone:** `V3.4-N-CORR-04-R2`  
**Classification:** Engineering Audit, Decision Model Reconciliation & Blocker Verification  
**Vehicle Platform:** `AGV-RES-TRUCK-01` (48V PMSM Electric Industrial Truck)  
**Author:** Senior Electrical Powertrain Safety Verification Engineer, Measurement/Metrology Engineer & Evidence Governance Auditor  
**Date:** 2026-10-04  

---

## Executive Audit Summary

Milestone **V3.4-N-CORR-04-R2** performs a rigorous second-level engineering audit and metrological reconciliation of the persistence decision model for electrical traction de-energization (`ELECTRICAL_TRACTION_DEENERGIZED`).

### Core Objective & Mandate:
The objective of this revision is **NOT** to prove or force approval of $T_{\text{persist}} = 10.0\,\text{ms}$. Rather, it is to rigorously evaluate whether $10.0\,\text{ms}$ is defensible at all under physical principles, and to resolve the remaining circular, ungrounded, or heuristic assertions in Milestone R1.

**Authoritative Finding:**  
Milestone V3.4-N-CORR-04-R2 determines that $T_{\text{persist}} = 10.0\,\text{ms}$ **CANNOT be formally defended or approved as a certified safety parameter at this time**. Multiple critical blockers—including unresolved current probe scaling ($5\,\text{A/V}$ vs $50\,\text{A/V}$), unevidenced motor-inverter firmware compatibility (Curtis AC Induction vs 48V PMSM), circular historical timing derivations, and missing raw digitized oscillograms—preclude closure.

In accordance with Section 1 and Section 18 of the mandate, the milestone **MUST REMAIN BLOCKED**:

```text
========================================================================================
V3_4_N_CORR_04_R2_STATUS              = BLOCKED_PENDING_RECONCILIATION
BLK_00_PERSIST                        = OPEN
TRACTION_CURRENT_ENDPOINT_PERSISTENCE = PROVISIONAL_CHARACTERIZATION_ONLY
T_persist = 10.0 ms                   = CANDIDATE_ONLY
PHYSICAL_CAPTURE_AUTHORIZATION        = NOT_GRANTED
MODEL_H                               = FROZEN
PRODUCTION_MODEL                      = UNCHANGED
FIELD_DATA                            = ZERO
========================================================================================
```

---

## 1. Hard Invariants & Production Code Immutability

The following hard invariants remain strictly frozen:

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

## 2. Removal of Unsupported Decay Lower Bound

Refer to [rms_decay_model.md](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r2/rms_decay_model.md).

In prior milestones, persistence was justified using the heuristic:
$$T_{\text{persist\_min}} = 3 \times \tau_{\text{eff}} = 3 \times 2.8\,\text{ms} = 8.4\,\text{ms}$$
and described as "settlement into the noise floor" or "complete decay."

### 2.1 Audit Findings & Deletions:
1. **Rule Revocation:** The criterion $T_{\text{persist\_min}} = 3\tau_{\text{eff}}$ is **EXPUNGED AND DELETED** as an approval condition.
2. **Physical Parameter Role:**
   - $\tau_e = L_s / R_s = 4.94\,\text{ms}$: Theoretical unforced stator coil time constant into open circuit. Descriptive only.
   - $\tau_{\text{eff}} \approx 2.8\,\text{ms}$: Empirical single-exponential envelope fit during inverter freewheeling diode conduction. Descriptive only.
3. **Decoupling from Persistence:** Neither time constant automatically dictates persistence duration. Current decay determines the time to reach threshold ($t_{\text{threshold}}$); persistence is an independent temporal hold that begins *after* threshold crossing to detect rebounds.

---

## 3. Closed-Form Moving RMS Response Model

Refer to [rms_closed_form.md](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r2/rms_closed_form.md).

For an exponential current decay $i(t) = I_0 \exp\left(-\frac{t - t_0}{\tau_{\text{eff}}}\right)$ initiated at $t_0$, the moving RMS response $I_{\text{RMS}}^2(t) = \frac{1}{T_w} \int_{t - T_w}^{t} i^2(\tau) d\tau$ is derived in exact closed form across three piecewise regions:

1. **Region 1: Pre-Event Window ($t < t_0$):**
   $$I_{\text{RMS}}(t) = I_0$$
2. **Region 2: Window Overlaps Decay Onset ($t_0 \le t < t_0 + T_w$):**
   $$I_{\text{RMS}}^2(t) = I_0^2 \left[ 1 - \frac{t - t_0}{T_w} + \frac{\tau_{\text{eff}}}{2 T_w} \left( 1 - \exp\left(-\frac{2(t - t_0)}{\tau_{\text{eff}}}\right) \right) \right]$$
3. **Region 3: Window Entirely Post-Event ($t \ge t_0 + T_w$):**
   $$I_{\text{RMS}}(t) = I_0 \cdot C(T_w, \tau_{\text{eff}}) \cdot \exp\left(-\frac{t - t_0}{\tau_{\text{eff}}}\right)$$
   where the window amplification factor is:
   $$C(T_w, \tau_{\text{eff}}) = \sqrt{ \frac{\tau_{\text{eff}}}{2 T_w} \left( \exp\left(\frac{2 T_w}{\tau_{\text{eff}}}\right) - 1 \right) }$$

For $T_w = 2.0\,\text{ms}$ and $\tau_{\text{eff}} = 2.8\,\text{ms}$:
$$C(2.0, 2.8) \approx 1.4903$$

### 3.1 Exact Analytical RMS Flush Lag ($\Delta_{\text{flush}}$)
In Region 3, the delay between instantaneous physical envelope threshold crossing ($t_{\text{phys\_envelope\_cross}}$) and moving RMS threshold crossing ($t_{\text{rms\_threshold\_cross}}$) is constant and independent of $I_0$ and $I_{\text{guarded}}$:

$$\mathbf{\Delta_{\text{flush}} = t_{\text{rms\_threshold\_cross}} - t_{\text{phys\_envelope\_cross}} = \tau_{\text{eff}} \ln C(T_w, \tau_{\text{eff}}) \approx 1.117\,ms \approx 1.12\,ms}$$

---

## 4. Decoupling Physical Envelope Crossing from RMS Crossing

Refer to [rms_decay_model.md](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r2/rms_decay_model.md).

Prior reports committed a serious physical error by equating:
$$\text{Legacy Report: } t_{\text{phys\_cross}} \in [21.2, 25.8]\,\text{ms}, \quad t_{\text{rms}} \in [21.2, 25.8]\,\text{ms}$$
Because $\Delta_{\text{flush}} = 1.12\,\text{ms} > 0$, the physical envelope crossing and RMS crossing can **never** be equal.

The variables are formally decoupled into:
- $t_{\text{phys\_envelope\_cross}}$: Instantaneous physical phase current envelope falls below $I_{\text{guarded}}$.
- $t_{\text{rms\_threshold\_cross}}$: First sliding RMS evaluation frame satisfying $I_{\text{RMS}}[k] \le I_{\text{guarded}}$ ($t_{\text{rms}} = t_{\text{phys}} + 1.12\,\text{ms}$).
- $t_{\text{persist\_start}}$: Evaluation grid timestamp where the persistence counter arms ($t_{\text{persist\_start}} \ge t_{\text{rms}}$).
- $t_{\text{endpoint\_declaration}}$: Final qualification frame where de-energization is asserted.

---

## 5. Elimination of Circular Timing Derivations

Refer to [timing_reconciliation_v3.json](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r2/timing_reconciliation_v3.json).

### 5.1 Historical Circularity Audit
In the historical 10-trial dataset:
$$\forall \text{trial } j: \quad t_{\text{stable}}[j] - t_{\text{threshold}}[j] = 10.0\,\text{ms} \quad \text{identically}$$
The reported start time $t_{\text{persist\_start}} = 25.8\,\text{ms}$ in Trial 8 was derived circularly by subtracting $10.0\,\text{ms}$ from a reported $35.8\,\text{ms}$ endpoint (or vice versa), without independent trigger cursors from raw oscillograms.

Per Section 5 of the mandate:
$$\mathbf{TIMING\_EVIDENCE = REPORT\_BASED}$$
The timing budget cannot be signed off as formally closed until raw digitized oscillograms validate $t_{\text{persist\_start}}$ independently.

---

## 6. Resolution of 100-Frame / 10-ms Discrete Timer Semantics

Refer to [persistence_state_machine_v3.md](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r2/persistence_state_machine_v3.md).

With an evaluation step size of $\Delta t_{\text{step}} = 0.1\,\text{ms}$, two distinct timer semantics exist:
- **Mode A (Sample-point evaluations):** 100 evaluations spanning $99$ intervals:
  $$\Delta t_{\text{Mode\_A}} = (100 - 1) \times 0.1\,\text{ms} = \mathbf{9.9\,ms}$$
- **Mode B (Elapsed timer intervals):** 100 elapsed intervals requiring $101$ evaluation points:
  $$\Delta t_{\text{Mode\_B}} = 100 \times 0.1\,\text{ms} = \mathbf{10.0\,ms}$$

### Implementation Ruling:
The frozen verification pipeline is formally defined as **Mode B (100 Elapsed Step Intervals = Exactly 10.0 ms)**. The ambiguous phrase "100 frames = exactly 10.0 ms" is prohibited without interval qualification.

---

## 7. The True Purpose of Persistence: Rebound & Chatter Defense

Refer to [persistence_state_machine_v3.md](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r2/persistence_state_machine_v3.md).

Persistence exists to protect against five specific dynamic failure modes:
1. **Contactor Micro-Bounce ($0.5 - 2.5\,\text{ms}$):** Mechanical contact chatter causing momentary gate cutoff followed by re-closure.
2. **Inductive Snubber Kickback:** Transient LC ringing during freewheeling diode turn-off knee.
3. **Regenerative Back-EMF Rebound:** In-motion PMSM rotor generating voltage exceeding DC bus during vehicle roll-out.
4. **STO Watchdog Fault Latch Race:** Controller gate-drive supervisor retry glitches.
5. **EMI / Noise Chatter:** Low-torque crawl noise spikes momentarily dipping below threshold.

A 4-state deterministic finite state machine (`ACTIVE`, `ARMED`, `PERSISTING`, `QUALIFIED`) enforces that any single-frame excursion ($I_{\text{RMS}}[k] > I_{\text{guarded}}$) during the 100-interval hold resets the timer immediately to zero.

---

## 8. Transient Detectability Bounds

Refer to [transient_detectability_bounds.csv](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r2/transient_detectability_bounds.csv).

For a rectangular pulse transient of amplitude $A$ and duration $\delta t$ inside window $T_w = 2.0\,\text{ms}$:
$$I_{\text{RMS}} = A \sqrt{\frac{\delta t}{T_w}}$$
To cause a threshold violation ($I_{\text{RMS}} > I_{\text{guarded}} = 0.410\,\text{A}$), the pulse amplitude must satisfy:
$$A > I_{\text{guarded}} \sqrt{\frac{T_w}{\delta t}}$$

| Pulse Duration $\delta t$ | Duration Ratio $\delta t / T_w$ | Amplitude Multiplier $\sqrt{T_w / \delta t}$ | Required Amplitude for RMS Trip | Detectability Classification |
| :---: | :---: | :---: | :---: | :--- |
| **$10\,\mu\text{s}$** | $0.005$ | $14.14$ | **$A > 5.80\,\text{A}$** | High-Amplitude Pulse Only |
| **$20\,\mu\text{s}$** | $0.010$ | $10.00$ | **$A > 4.10\,\text{A}$** | High-Amplitude Pulse Only |
| **$50\,\mu\text{s}$** | $0.025$ | $6.32$ | **$A > 2.59\,\text{A}$** | Moderate-Amplitude Spike |
| **$100\,\mu\text{s}$** | $0.050$ | $4.47$ | **$A > 1.83\,\text{A}$** | Single-Step Transient |
| **$200\,\mu\text{s}$** | $0.100$ | $3.16$ | **$A > 1.30\,\text{A}$** | Multi-Step Transient |
| **$500\,\mu\text{s}$** | $0.250$ | $2.00$ | **$A > 0.82\,\text{A}$** | Sub-Millisecond Burst |
| **$1.0\,\text{ms}$** | $0.500$ | $1.41$ | **$A > 0.58\,\text{A}$** | Half-Window Modulation |
| **$2.0\,\text{ms}$** | $1.000$ | $1.00$ | **$A > 0.41\,\text{A}$** | Full-Window Step |

### Behavioral Separation:
The analysis proves that while **every** transient $\ge 1\,\mu\text{s}$ is `SAMPLED_BY_ADC` and `CONTRIBUTES_TO_RMS`, it only `CROSSES_RMS_THRESHOLD` and `RESETS_PERSISTENCE` if its amplitude exceeds the bounds above. The claim that "every transient is detected as a threshold violation" is mathematically false.

---

## 9. Revocation of Continuous-Time Guarantees

The claim in prior drafts of "complete mathematical coverage of continuous analog dynamics" is **EXPUNGED**.  
The physical measurement system is a sampled digital pipeline ($f_s = 1\,\text{MSa/s}$, $f_{\text{eval}} = 10\,\text{kHz}$). Per Section 9 of the mandate:

$$\mathbf{DECISION\_DOMAIN = DISCRETE\_SAMPLED\_RMS}$$

No continuous analog guarantee ($\forall t$) is asserted.

---

## 10. Rebuilt Signal Path & Filter Differentiation

Refer to [signal_path_audit_v2.md](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r2/signal_path_audit_v2.md).

- **Rebuttal of the "20 kHz Hardware Filter":** The Keysight DSOX1204G contains only $70\,\text{MHz}$ and $20\,\text{MHz}$ analog hardware filters. A $20\,\text{kHz}$ filter exists only as a digital Math Channel software feature in the scope display firmware.
- **Filter Domain Separation:**
  1. *Instrument Analog:* $20\,\text{MHz}$ hardware bandwidth limit.
  2. *Scope Math Filter:* Not part of the DAQ pipeline; prohibited from insertion.
  3. *RMS Processing:* Frozen discrete rectangular moving-average engine (`RMS-PROC-V1.0`).

---

## 11. Controller Reconciliation & Motor Compatibility Block

Refer to [controller_baseline_audit.md](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r2/controller_baseline_audit.md) and [motor_controller_compatibility.md](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r2/motor_controller_compatibility.md).

1. **Curtis 1238E-5421 Authenticity:** Confirmed as an authentic Curtis controller family ($36-48\,\text{V}$, $350\,\text{A}$ RMS continuous / $450\,\text{A}$ peak).
2. **Motor Incompatibility Discrepancy:** Vehicle documentation cites a $5.5\,\text{kW}$ PMSM, but standard Curtis 1238E documentation specifies AC Induction control. The repository lacks a validated Curtis PMSM software license, resolver/encoder commutation alignment report, and motor dynamometer commissioning file.

Consequently, per Section 11:
$$\mathbf{MOTOR\_CONTROLLER\_COMPATIBILITY = BLOCKED}$$

---

## 12. Expunging Unsupported SIL / PL Claims

Refer to [controller_baseline_audit.md](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r2/controller_baseline_audit.md).

All prior assertions of `SIL 3` and `PL e` are **EXPUNGED**.  
Curtis 1238E manufacturer documentation supports up to EN ISO 13849-1 Category 2/3 PL d and IEC 61508 SIL 2 for specific drive-inhibit sub-functions. No component certificate substitutes for vehicle-level machine safety architecture.

---

## 13. Rebuilt Uncertainty Model & Threshold Reassessment

Refer to [uncertainty_budget_v3.json](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r2/uncertainty_budget_v3.json) and [guarded_threshold_v3.json](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r2/guarded_threshold_v3.json).

### 13.1 Critique of Prior Seven Components:
The legacy values ($u_{\text{cal}} = 0.015\,\text{A}$, $u_{\text{offset}} = 0.020\,\text{A}$, $u_{\text{noise}} = 0.025\,\text{A}$, $u_{\text{quant}} = 0.010\,\text{A}$, $u_{\text{rms}} = 0.018\,\text{A}$, $u_{\text{temp}} = 0.012\,\text{A}$, $u_{\text{filter}} = 0.015\,\text{A}$) were arbitrary heuristic estimates that assumed an impossible $10\,\text{A/V}$ probe range.

### 13.2 Hardware-Traceable Rebuild ($5\,\text{A/V}$ Range):
Derived from Tektronix TCPA300 and Keysight DSO datasheets on the intended low range ($5\,\text{A/V}$ into $50\,\Omega$):
- $u_{\text{gain}} = 0.00750\,\text{A}$ (Probe + Amp + DSO vertical gain, $3.0\%$)
- $u_{\text{offset}} = 0.00289\,\text{A}$ ($1.0\,\text{mV}$ drift on $5\,\text{A/V}$ range)
- $u_{\text{noise}} = 0.01680\,\text{A}$ ($1.5\,\text{mV RMS}$ probe noise + bench pickup)
- $u_{\text{quant}} = 0.00451\,\text{A}$ (8-bit ADC over $800\,\text{mV}$ vertical span)
- $u_{\text{RMS}} = 0.00500\,\text{A}$ (Numerical discrete sum)
- $u_{\text{temp}} = 0.00058\,\text{A}$ (Thermal sensitivity over $\Delta T = 10^\circ\text{C}$)
- $u_{\text{flatness}} = 0.00125\,\text{A}$ (Analog front-end passband flatness)

$$\mathbf{u_c(I) = 0.01985\,A \approx 0.020\,A}$$
$$\mathbf{U(I) = 2.00 \times u_c = 0.0397\,A \approx 0.040\,A}$$
$$\mathbf{I_{\text{guarded}} = 0.500\,A - 0.0397\,A = 0.4603\,A \approx 0.460\,A\;RMS}$$

### 13.3 Threshold Status Determination:
Because the historical 10 characterization trials failed to log the physical range switch position, the actual operating scale remains ungrounded. Therefore:
$$\mathbf{GUARDED\_THRESHOLD\_STATUS = UNRESOLVED\_PENDING\_BENCH\_SCALE\_CONFIRMATION}$$
The historical $0.410\,\text{A RMS}$ (and older $0.413\,\text{A}$) is **NOT PRESERVED**.

---

## 14. Current Probe Range & Calibration Traceability

Refer to [signal_path_audit_v2.md](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r2/signal_path_audit_v2.md).

- Probe: Tektronix TCP303 (Serial: `B020194`)
- Amplifier: Tektronix TCPA300 (Serial: `B010482`)
- Supported Ranges: $5\,\text{A/V}$ ($0.2\,\text{V/A}$) and $50\,\text{A/V}$ ($0.02\,\text{V/A}$) only. Setting $10\,\text{A/V}$ is invalid.
- Calibration Status: ISO/IEC 17025 certificate is `MISSING`.
- Finding:
  $$\mathbf{HISTORICAL\_CURRENT\_SCALE = UNRESOLVED}$$

---

## 15. Raw Evidence & Manifest

Refer to [evidence_manifest_v3.csv](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r2/evidence_manifest_v3.csv).

All 10 characterization trials are audited. Raw oscillograms (`.bin`/`.csv`), scope configuration files, and calibration certificates remain **`MISSING`**. Evidence is classified as **`REPORT_BASED`**.

---

## 16. Timing Budget Reconciliation

Refer to [timing_reconciliation_v3.json](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r2/timing_reconciliation_v3.json).

Under direct observed timestamp semantics:
$$t_{\text{endpoint}} = t_{\text{persist\_start}} + T_{\text{persist}}$$
Because $\max(t_{\text{persist\_start}}) = 25.8\,\text{ms}$ cannot be independently validated from raw waveform data, the timing budget remains **`OPEN_UNVERIFIED`**.

---

## 17. DC Bus Semantics Decoupling

Refer to [instrument_chain_audit.md](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r1/instrument_chain_audit.md).

The three DC bus states are decoupled:
1. `DC_BUS_ISOLATED`: Main contactor physically open ($R_{\text{open}} > 1\,\text{M}\Omega$). Verified via auxiliary microswitch.
2. `DC_BUS_DISCHARGED`: Link capacitors bled to touch-safe residual voltage ($V_{\text{bus}} < 5.0\,\text{V}$). Bleeder time: $180 - 300\,\text{s}$ (offline maintenance state only).
3. `DC_BUS_VOLTAGE_BELOW_ACCEPTANCE_LIMIT`: Specific to high-voltage platforms ($>60\,\text{V}$); not applicable to $48\,\text{V}$ nominal systems. The $<50\,\text{V}$ criterion is rejected.

---

## 18. Final Decision & Status Determination

Per Section 18 of the mandate, because the measurement chain, motor compatibility, and raw trial evidence remain unclosed:

$$\mathbf{V3\_4\_N\_CORR\_04\_R2\_STATUS = BLOCKED\_PENDING\_RECONCILIATION}$$

Transition to `READY_FOR_V3_4_N_CORR_03_REAUDIT` is withheld until all eight criteria in [release_blockers.md](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r2/release_blockers.md) are satisfied.

---

## 19. Required Outputs Manifest

All 15 required milestone artifacts are created and cross-verified in `outputs/v3_4_n_corr_04_r2/`:
1. [reconciliation_report.md](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r2/reconciliation_report.md) — Master synthesis report covering all 20 sections.
2. [rms_decay_model.md](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r2/rms_decay_model.md) — Deletion of $3\tau$ lower bound and decoupling of physical vs RMS crossing.
3. [rms_closed_form.md](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r2/rms_closed_form.md) — Exact closed-form piecewise RMS model and proof of $\Delta_{\text{flush}} = 1.12\,\text{ms}$.
4. [persistence_state_machine_v3.md](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r2/persistence_state_machine_v3.md) — Mode B interval semantics, rebound failure model, and discrete domain restriction.
5. [transient_detectability_bounds.csv](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r2/transient_detectability_bounds.csv) — Pulse detectability boundaries from $10\,\mu\text{s}$ to $2\,\text{ms}$.
6. [timing_reconciliation_v3.json](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r2/timing_reconciliation_v3.json) — Non-circular timing model and historical circularity audit.
7. [signal_path_audit_v2.md](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r2/signal_path_audit_v2.md) — Metrological signal path audit and scale indeterminacy.
8. [controller_baseline_audit.md](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r2/controller_baseline_audit.md) — Curtis 1238E baseline audit and expunging of SIL/PL claims.
9. [motor_controller_compatibility.md](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r2/motor_controller_compatibility.md) — Curtis AC Induction vs 48V PMSM compatibility block.
10. [uncertainty_budget_v3.json](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r2/uncertainty_budget_v3.json) — Hardware range-dependent uncertainty budget ($5\,\text{A/V}$ vs $50\,\text{A/V}$).
11. [guarded_threshold_v3.json](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r2/guarded_threshold_v3.json) — Guarded threshold marked UNRESOLVED; $0.410\,\text{A}$ rejected.
12. [evidence_manifest_v3.csv](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r2/evidence_manifest_v3.csv) — 10-trial evidence ledger with missing artifacts and indeterminate range.
13. [decision_rule_v3.json](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r2/decision_rule_v3.json) — Reconciled decision rule holding $10.0\,\text{ms}$ at CANDIDATE_ONLY.
14. [release_blockers.md](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r2/release_blockers.md) — Ledger of 6 active release blockers and unblocking criteria.
15. [audit_v3_4_n_corr_04_r2.py](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r2/audit_v3_4_n_corr_04_r2.py) — Comprehensive automated verification script passing 15/15 checks.

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

BLK_00_PERSIST = OPEN

V3_4_N_CORR_04_R2_STATUS =
    BLOCKED_PENDING_RECONCILIATION
```
