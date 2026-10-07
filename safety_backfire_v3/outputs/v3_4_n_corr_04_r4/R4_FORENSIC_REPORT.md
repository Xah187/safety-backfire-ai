# V3.4-N-CORR-04-R4 — Evidence Readiness, Dependency Closure & Traceability Forensic Report

**Document:** `outputs/v3_4_n_corr_04_r4/R4_FORENSIC_REPORT.md`  
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
REFERENCE_MODEL_VERIFIED        = TRUE
FROZEN_RMS_IMPLEMENTATION_VERIFIED = FALSE
FINAL_STATUS                    = BLOCKED
```

---

## 1. Executive Summary & Epistemic Boundary

Milestone **V3.4-N-CORR-04-R4** continues directly from R3. This milestone is **NOT** a mathematical expansion or model-tuning exercise. Its explicit purpose is to conduct an uncompromising, dependency-aware forensic metrology audit of the entire traction current persistence characterization pipeline.

The audit establishes:
1. What evidence is required to transition persistence characterization from an internally consistent reference/analytical model into auditable physical measurement evidence;
2. Why zero blockers can be closed today despite extensive documentary progress;
3. Why the milestone status remains strictly **`BLOCKED`**.

---

## 2. Master Forensic Audit Findings Across Pipelines

### 2.1 Frozen RMS Implementation Forensic Search
- A comprehensive, automated search of the repository for `RMS-PROC-V1.0` and sixteen related digital signal processing terms revealed that **no operational, executable script or binary ever existed in the repository prior to R3**.
- The script `discrete_rms_verification.py` created in R3 is a **synthetic reference model** designed to check the internal mathematical consistency of documented parameters ($N=2000, M=100$) against closed-form exponential equations. It is not an operational pipeline that processed historical waveforms.
- Crucial distinction preserved:
  $$\text{REFERENCE\_MODEL\_VERIFIED} = \text{TRUE}$$
  $$\text{FROZEN\_RMS\_IMPLEMENTATION\_VERIFIED} = \text{FALSE}$$
- Status: **`RMS_IMPLEMENTATION_MISSING`**.

### 2.2 Discrete RMS Index Contract
- Historical ambiguity between a "2000-sample window" and "2001 timestamped points spanning 2.0 ms" was formally resolved in `discrete_rms_index_contract.md`.
- In discrete DSP, a uniform moving average of order $N=2000$ consumes exactly **2000 sample values** ($\mathcal{W}[k] = x[k-N+1 : k+1]$), spanning an elapsed time of $1.999\,\text{ms}$ between first and last sample, with $N \cdot T_s = 2.000\,\text{ms}$ of Riemann integration support.
- Right-edge timestamping ($t_k = k \cdot T_s$) is established as the causal contract for discrete outputs.

### 2.3 Anti-Aliasing Chain Forensics
- Technical specifications for the Keysight DSOX1204G and Tektronix TCP303/TCPA300 reveal that the analog front-end has flat frequency response up to $15\,\text{MHz}$ (TCP303) and $20\,\text{MHz}$ or $70\,\text{MHz}$ (scope).
- **The purported "hardware 4th-order 20 kHz low-pass filter" does not exist in instrument hardware.**
- Scope decimation mode (`Normal` vs `High-Res`) during historical runs is completely undocumented.
- Inverter switching ringing and edge transitions between $500\,\text{kHz}$ and $15\,\text{MHz}$ fold unattenuated into the $1.0\,\text{MSa/s}$ baseband.
- Status: **`ANTI_ALIAS_VALIDATION = BLOCKED`**.

### 2.4 Current Transducer & Scale Traceability
- Tektronix TCPA300 supports only $5\,\text{A/V}$ and $50\,\text{A/V}$ ranges.
- At $5\,\text{A/V}$, continuous thermal rating is $25\,\text{A DC}$ / $17.7\,\text{A RMS}$. A reported pre-event operating current of $\sim 115\,\text{A}$ violates this limit.
- At $50\,\text{A/V}$, the $0.410\,\text{A}$ threshold produces only $8.2\,\text{mV}$, which is less than 1 LSB of an 8-bit digitizer scaled for $\sim 115\,\text{A}$ ($15.6\,\text{mV/LSB}$).
- Historical range settings and channel termination ($50\,\Omega$ vs $1\,\text{M}\Omega$) are unrecorded. Reverse-engineering range from reported values is prohibited.
- Status: **`HISTORICAL_CURRENT_SCALE = UNRESOLVED`**.

### 2.5 Powertrain Identity & Motor Compatibility
- Curtis official catalog classifies the standard 1238E model as an AC Induction motor controller, while vehicle documentation claims a 5.5 kW PMSM.
- 18 of 18 powertrain identity dimensions (motor nameplate, electrical parameters $R_s, L_d, L_q$, controller firmware, VCL script, `Motor_Type` parameter) are missing or unverified.
- Spinning PMSMs generate continuous back-EMF ($V = k_e \cdot \omega$), invalidating passive $L/R$ decay models if antiparallel diodes conduct.
- Status: **`MOTOR_CONTROLLER_COMPATIBILITY = BLOCKED`**.

### 2.6 Effective Time Constant ($\tau_{\text{eff}} = 2.8\,\text{ms}$)
- All thirteen required regression artifacts (raw decay oscillogram, fitting interval, baseline offset, residuals vector, $R^2$, and parameter uncertainty) are completely missing.
- Applying an invariant $\tau_{\text{eff}} = 2.8\,\text{ms}$ across divergent speeds ($10 - 90\,\text{Hz}$), loads, and temperatures violates physical machine behavior.
- Status: **`TAU_EFF_STATUS = DESCRIPTIVE_UNTRACEABLE_FIT`**.

### 2.7 Historical Trial Provenance
- All ten historical characterization runs (`CHAR_RUN_01` through `CHAR_RUN_10`) lack raw oscillograms, setup files, and cryptographic hashes.
- Manifest timing values $t_{\text{phys}}$ were calculated by formula subtraction ($t_{\text{RMS}} - 1.12\,\text{ms}$) rather than physically measured.
- Status: **`TIMING_EVIDENCE = REPORT_BASED`**.

### 2.8 Measurement Acceptance Contract
- All circular clauses requiring future experimental data to "confirm $\Delta_{\text{flush}} \approx 1.12\,\text{ms}$" have been expunged.
- The contract establishes a non-circular 7-parameter evaluation protocol ($t_{\text{phys}}^{\text{obs}}, t_{\text{RMS}}^{\text{obs}}, \Delta^{\text{obs}}, \Delta^{\text{pred}}, \epsilon, U_{\Delta}, \text{EXPLANATION}$), explicitly permitting observed data to disagree with analytical predictions.

### 2.9 Measurement Uncertainty & Decision Rules
- Uncertainty is decomposed into six separate domains: Measurement, Model, Implementation, Timestamp, Calibration, and Aliasing.
- Naive Root-Sum-Square (RSS) combination is refuted due to multiplicative parameter correlation.
- Five of the six domains are indeterminate.
- Status: **`UNCERTAINTY_BUDGET = INCOMPLETE`**.

---

## 3. Mandatory Governance Declarations

The following six fundamental epistemic declarations are formally affirmed:

1. **Documentation quality improved $\ne$ physical validation.**  
   Generating rigorous, highly structured audit reports does not close physical evidence gaps.
2. **Reference-model verification $\ne$ historical pipeline verification.**  
   Proving that synthetic Python code matches continuous equations does not prove that historical bench trials executed that pipeline.
3. **Manufacturer capability $\ne$ historical instrument configuration.**  
   An oscilloscope's published datasheet specifications do not prove that a feature was enabled during a specific acquisition.
4. **Analytical prediction $\ne$ physical observation.**  
   A closed-form mathematical curve is a hypothesis; it is not physical observation.
5. **Current-threshold persistence $\ne$ direct proof of vehicle traction de-energization.**  
   Qualifying that stator current is below $0.410\,\text{A}$ does not prove that vehicle kinetic energy has ceased or that dangerous back-EMF is absent.
6. **Component documentation $\ne$ vehicle functional-safety certification.**  
   Component-level product brochures cannot substitute for ISO 26262 / ISO 13849-1 vehicle-level hazard analysis and safety certification.

---

## 4. Required Concluding Sections

### ERRORS_FOUND
1. **Fictitious Hardware Filter:** Historical documentation falsely asserted the presence of a "hardware 4th-order 20 kHz low-pass filter" in the acquisition front-end; instrument specifications prove Keysight DSOX1204G has no such hardware filter.
2. **Derived Manifest Timing Presented as Observation:** In `evidence_manifest_v3.csv`, the column `t_phys_envelope_cross_ms` was computed via formula subtraction ($t_{\text{RMS}} - 1.12\,\text{ms}$) across all 10 trials rather than observed from raw oscillograms.
3. **Circular Acceptance Criteria:** Prior milestones contained circular clauses requiring future experimental captures to "confirm $\Delta_{\text{flush}} \approx 1.12\,\text{ms}$".
4. **Invalid Naive RSS Uncertainty:** Earlier milestones computed a draft uncertainty $U = 0.087\,\text{A}$ using naive RSS quadrature, violating GUM independence requirements across correlated multiplicative transfer factors.
5. **Universal Application of Invariant $\tau_{\text{eff}}$:** Applying $\tau_{\text{eff}} = 2.8\,\text{ms}$ across divergent speeds, loads, and motor operating points without accounting for temperature or magnetic saturation.

### CORRECTIONS_APPLIED
1. **Created 29-Node Evidence Dependency Graph:** Formally mapped all measurement, signal-processing, and powertrain identity dependencies with explicit evidentiary classifications (`outputs/v3_4_n_corr_04_r4/evidence_dependency_graph.md`).
2. **Forensic Search Completed:** Exhaustively proved that `RMS-PROC-V1.0` was never implemented as executable code in the repository; formally declared `RMS_IMPLEMENTATION_MISSING`.
3. **Normative Index Contract Established:** Defined exact 0-indexed slicing semantics ($N=2000, M=100$, right-edge timestamping), resolving the 2000-sample vs 2001-point fencepost ambiguity (`discrete_rms_index_contract.md`).
4. **Anti-Aliasing Evidence Matrix Authored:** Categorized all signal path stages into Hardware/Digital and Pre-ADC/Post-ADC; declared `ANTI_ALIAS_VALIDATION = BLOCKED`.
5. **Expunged Circular Acceptance Clauses:** Replaced "confirm 1.12 ms" with the non-circular 7-parameter acceptance protocol in `measurement_acceptance_contract.md`.
6. **Uncertainty Framework Formulated:** Decomposed uncertainty into six separate domains, rejecting naive RSS combination and declaring `UNCERTAINTY_BUDGET = INCOMPLETE`.
7. **Readiness Gate Architecture Defined:** Established three objective gates (`NOT_READY`, `READY_FOR_ENGINEERING_REVIEW`, `READY_FOR_AUDITED_CAPTURE`) while preserving `PHYSICAL_CAPTURE_AUTHORIZATION = NOT_GRANTED`.

### EVIDENCE_VERIFIED
1. **Model H Invariants:** $k_0 = 2.40, \beta_d = 0.08, \beta_l = 0.12, \beta_{\text{pitch}} = 0.22$ verified unchanged.
2. **Production Script Hashes:** `scripts/v3_4/discover_event_candidates.py` and `scripts/v3_4/automated_evidence_screening.py` verified identical to recorded baseline.
3. **Reference Model Self-Consistency:** Synthetic reference model (`discrete_rms_verification.py`) verified self-consistent with continuous Region 1/2/3 closed forms.
4. **Discrete Index Contract:** Mathematical formulation of $N=2000, M=100$ causal right-edge window verified.
5. **Automated Audit Pass:** All 49 automated checks in `audit_r4.py` passed without failure.

### EVIDENCE_REMAINING_MISSING
1. Raw machine waveform files (`.csv`, `.bin`, `.wfm`) for historical runs `CHAR_RUN_01` – `CHAR_RUN_10`.
2. Machine-readable oscilloscope setup files (`.setup`) and acquisition mode records.
3. Accredited calibration certificates for probe (TCP303), amplifier (TCPA300), and oscilloscope (DSOX1204G).
4. Physical amplifier range switch logs ($5\,\text{A/V}$ vs $50\,\text{A/V}$) and termination impedance verification ($50\,\Omega$).
5. Motor nameplate photograph and certified electrical parameter datasheet ($R_s, L_d, L_q, k_e$).
6. Controller parameter dump (`.cpf`) and application VCL program source.
7. Primary regression oscillograms and residual plots for $\tau_{\text{eff}} = 2.8\,\text{ms}$.
8. High-frequency spectral scan of stator inverter switching harmonics.
9. Contactor auxiliary contact bounce and trigger latency measurements.

### UPSTREAM_BLOCKERS
- **`BLK_R3_01`:** RMS-PROC-V1.0 executable and hash missing.
- **`BLK_R3_03`:** Anti-aliasing chain unjustified.
- **`BLK_R3_04`:** Current measurement scale and termination untraceable.
- **`BLK_R3_05`:** Exact powertrain identity and controller configuration unreconciled.
- **`BLK_R3_09`:** Instrument identity provenance unverified.

### DOWNSTREAM_BLOCKERS
- **`BLK_R3_02`:** Discrete vs continuous model equivalence on real waveforms (depends on 01, 03).
- **`BLK_R3_06`:** Timing data independent traceability (depends on 01, 03, 04, 07).
- **`BLK_R3_07`:** Timestamp semantics and trigger jitter (depends on 04, 09).
- **`BLK_R3_08`:** Signal-domain applicability (phase vs 3-phase scalar) (depends on 04, 05).
- **`BLK_R3_10`:** Guarded-threshold authority (depends on 01, 03, 04).
- **`BLK_R3_11`:** Rebound and back-EMF characterization (depends on 05).
- **`BLK_R3_12`:** $\tau_{\text{eff}}$ fit provenance and generalization (depends on 05, 06).
- **`BLK_R3_13`:** Vehicle functional safety claims (depends on all prior blockers).

### BLOCKERS_OPEN
All thirteen R3 blockers remain strictly **`OPEN`**:
- `BLK_R3_01`, `BLK_R3_02`, `BLK_R3_03`, `BLK_R3_04`, `BLK_R3_05`, `BLK_R3_06`, `BLK_R3_07`, `BLK_R3_08`, `BLK_R3_09`, `BLK_R3_10`, `BLK_R3_11`, `BLK_R3_12`, `BLK_R3_13`.

### BLOCKERS_CLOSED
**`ZERO`** (0). No blocker was closed.

### CLAIMS_WITHHELD
The following claims are formally withheld, unestablished, and prohibited from being asserted:
- Performance Level d / e (`PL d`, `PL e`) under ISO 13849-1;
- Safety Integrity Level 2 / 3 (`SIL 2`, `SIL 3`) under IEC 61508;
- ISO Compliance (`ISO_COMPLIANT`);
- Safety Certification (`SAFETY_CERTIFIED`);
- Vehicle Functional Safety Established (`VEHICLE_FUNCTIONAL_SAFETY_ESTABLISHED`);
- Production Readiness (`PRODUCTION_READY`);
- Real-World Backfire Validation (`REAL_WORLD_VALIDATION`);
- Physical Capture Readiness / Authorization (`PHYSICAL_CAPTURE_AUTHORIZATION`).

### NEXT_EVIDENCE_REQUIRED
To progress from `NOT_READY` toward Gate 2 (`READY_FOR_ENGINEERING_REVIEW`), the next required physical actions are:
1. Retrieve and archive primary PDF manuals for TCP303, TCPA300, and Keysight DSOX1204G into the repository.
2. Photograph physical asset nameplates for the bench oscilloscope, amplifier, probe, motor, and controller.
3. Commit an executable, versioned Python implementation of the discrete RMS pipeline to `scripts/` with full unit tests and recorded SHA-256 hash.
4. Obtain accredited calibration certificates for all three measurement instruments.
5. Export and archive the Curtis controller parameter archive (`.cpf`) and application VCL program.

---

### FINAL_STATUS
```text
FINAL_STATUS = BLOCKED
```
