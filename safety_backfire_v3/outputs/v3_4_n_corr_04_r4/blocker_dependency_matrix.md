# V3.4-N-CORR-04-R4 — Blocker Dependency Matrix & Root Cause Topology

**Document:** `outputs/v3_4_n_corr_04_r4/blocker_dependency_matrix.md`  
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
BLOCKERS_OPEN                   = 13
BLOCKERS_CLOSED                 = 0
FINAL_STATUS                    = BLOCKED
```

---

## 1. Upstream Causal Hierarchy

Blockers in this milestone are not isolated documentation tickets; they form a strict, directed causal dependency network. Attempting to close downstream blockers (such as timing validation or safety claims) without first providing the physical root evidence for upstream blockers is logically invalid.

```text
========================================================================================
SIGNAL PROCESSING & METROLOGICAL CHAIN
========================================================================================

[BLK_R3_09 Instrument Identity]
       │
       ▼
[BLK_R3_04 Current Scale & Termination]
       │
       ├─────────────────────────────────────────┐
       ▼                                         ▼
[BLK_R3_03 Anti-Aliasing & Decimation]   [BLK_R3_08 Signal Domain (Phase vs RMS)]
       │                                         │
       └────────────────────┬────────────────────┘
                            │
                            ▼
               [BLK_R3_01 RMS-PROC Implementation]
                            │
                            ▼
               [BLK_R3_02 Discrete vs Continuous Model Equivalence]
                            │
                            ▼
               [BLK_R3_10 Guarded Threshold Authority]
                            │
                            ▼
               [BLK_R3_07 Timestamp Semantics & Trigger Jitter]
                            │
                            ▼
               [BLK_R3_06 Independent Timing Traceability]

========================================================================================
POWERTRAIN IDENTITY & PHYSICAL MECHANISMS CHAIN
========================================================================================

[BLK_R3_05 Exact Powertrain Identity & Config]
       │
       ├─────────────────────────────────────────┐
       ▼                                         ▼
[BLK_R3_11 Rebound & Back-EMF Mechanisms]   [BLK_R3_12 tau_eff Fit Provenance]
       │                                         │
       └────────────────────┬────────────────────┘
                            │
                            ▼
               [Physical Decay Relevance]
                            │
                            ▼
               [BLK_R3_13 Vehicle Functional Safety Claims]
```

---

## 2. Comprehensive Blocker Ledger (BLK_R3_01 – BLK_R3_13)

Below is the complete mapping of all thirteen open blockers to their root physical evidence, dependent downstream claims, what can be verified without closure, and what remains unverifiable:

### BLK_R3_01: RMS-PROC-V1.0 Not Executable or Hashed
- **Severity:** `CRITICAL` (Upstream Root Blocker)
- **Root Evidence Required:** An executable Python/C DSP script or binary committed to the repository with a recorded SHA-256 hash, implementing the exact contract in `discrete_rms_index_contract.md`.
- **Dependent Claims:** BLK_R3_02, BLK_R3_06, BLK_R3_07, BLK_R3_10.
- **What CAN be Verified Without Closure:** Mathematical self-consistency of a synthetic reference model (`discrete_rms_verification.py`) against continuous exponential formulas on synthetic arrays.
- **What CANNOT be Verified:** Processing of any historical or future physical oscillogram; historical threshold crossing times.
- **Status:** `OPEN`

### BLK_R3_02: Discrete vs. Continuous Model Equivalence Unverified
- **Severity:** `CRITICAL`
- **Root Evidence Required:** Proof that the frozen discrete implementation matches the continuous boundary factor $B \approx 0.72955$ and Region 2/3 crossing equations across real physical current waveforms with noise and discretization jitter.
- **Dependent Claims:** BLK_R3_06, BLK_R3_10.
- **What CAN be Verified Without Closure:** Sub-sample agreement between continuous formulas and the pure-software reference model on idealized noiseless exponential test vectors.
- **What CANNOT be Verified:** Continuous equivalence on real digitized waveforms containing quantization steps, phase jitter, and PWM harmonics.
- **Status:** `OPEN`

### BLK_R3_03: Anti-Aliasing Chain Unjustified
- **Severity:** `CRITICAL` (Upstream Root Blocker)
- **Root Evidence Required:** Primary oscilloscope manuals; recorded acquisition mode (`Normal`, `High-Res`); spectral scan of inverter current showing out-of-band energy bounded below noise floor; or hardware anti-alias filter specification.
- **Dependent Claims:** BLK_R3_01, BLK_R3_02, BLK_R3_10.
- **What CAN be Verified Without Closure:** Theoretical Nyquist bandwidth ($500\,\text{kHz}$) of an ideal $1.0\,\text{MSa/s}$ digitizer.
- **What CANNOT be Verified:** Freedom from aliasing of $1 - 15\,\text{MHz}$ switching edge ringing; integrity of sub-ampere RMS calculations.
- **Status:** `OPEN`

### BLK_R3_04: Current Measurement Scale and Termination Untraceable
- **Severity:** `CRITICAL` (Upstream Root Blocker)
- **Root Evidence Required:** Primary laboratory setup records documenting TCPA300 range ($5\,\text{A/V}$ vs $50\,\text{A/V}$), scope termination ($50\,\Omega$ vs $1\,\text{M}\Omega$), degauss checklist, and calibration certificates.
- **Dependent Claims:** BLK_R3_10, BLK_R3_12, BLK_R3_28.
- **What CAN be Verified Without Closure:** Theoretical transfer factors ($0.2\,\text{V/A}$ vs $0.02\,\text{V/A}$) from Tektronix product catalogs.
- **What CANNOT be Verified:** Absolute physical current scale of historical trials; validity of $0.410\,\text{A}$ threshold in physical Amperes.
- **Status:** `OPEN`

### BLK_R3_05: Exact Powertrain Identity & Configuration Unreconciled
- **Severity:** `CRITICAL` (Upstream Root Blocker)
- **Root Evidence Required:** Motor nameplate photograph, motor electrical datasheet ($R_s, L_d, L_q, k_e$), controller parameter file (`.cpf`), VCL program source, and commutation alignment logs.
- **Dependent Claims:** BLK_R3_11, BLK_R3_12, BLK_R3_13.
- **What CAN be Verified Without Closure:** Catalog statements regarding standard Curtis 1238E models and general PMSM/Induction motor theory.
- **What CANNOT be Verified:** Active control mode (PMAC vs Induction); shutdown interlock mechanism; physical validity of passive exponential decay.
- **Status:** `OPEN`

### BLK_R3_06: Timing Data Not Independently Traceable
- **Severity:** `CRITICAL`
- **Root Evidence Required:** Raw time-series oscillograms (`.csv`/`.bin`) with cryptographic SHA-256 hashes, mapped 1-to-1 to test conditions.
- **Dependent Claims:** Empirical validation of Model H; empirical validation of $\Delta_{\text{flush}}$.
- **What CAN be Verified Without Closure:** Text strings and numbers in historical narrative tables.
- **What CANNOT be Verified:** Empirical truth of reported crossing times; independence of $t_{\text{phys}}$ from $t_{\text{RMS}}$.
- **Status:** `OPEN`

### BLK_R3_07: Timestamp Semantics Not Verified
- **Severity:** `CRITICAL`
- **Root Evidence Required:** Documentation of oscilloscope clock stability, trigger source pick-off circuit, contactor contact bounce duration, and cross-channel propagation delay.
- **Dependent Claims:** BLK_R3_06.
- **What CAN be Verified Without Closure:** Software right-edge timestamp definition for discrete RMS frames.
- **What CANNOT be Verified:** Timebase synchronization between physical E-Stop button press and $t=0.0\,\text{s}$.
- **Status:** `OPEN`

### BLK_R3_08: Signal-Domain Applicability Unresolved
- **Severity:** `MAJOR`
- **Root Evidence Required:** Formal proof and derivation establishing whether the moving RMS window is applied to a single-phase current ($i_U(t)$) or a 3-phase scalar magnitude ($i_{\text{mag}} = \sqrt{i_u^2 + i_v^2 + i_w^2}$).
- **Dependent Claims:** BLK_R3_01, BLK_R3_10.
- **What CAN be Verified Without Closure:** Mathematical moving RMS of an arbitrary 1D scalar array.
- **What CANNOT be Verified:** Physical meaning of a $2.0\,\text{ms}$ window on a $10 - 90\,\text{Hz}$ sinusoidal phase trace (which spans only a small fraction of a fundamental period).
- **Status:** `OPEN`

### BLK_R3_09: Instrument Identity Provenance Missing
- **Severity:** `MAJOR`
- **Root Evidence Required:** Laboratory asset register, calibration certificates, and physical serial number photographs.
- **Dependent Claims:** BLK_R3_04, BLK_R3_15.
- **What CAN be Verified Without Closure:** Serial number strings cited in narrative markdown text.
- **What CANNOT be Verified:** Metrological chain of custody.
- **Status:** `OPEN`

### BLK_R3_10: Guarded-Threshold Authority Ungrounded
- **Severity:** `MAJOR`
- **Root Evidence Required:** A certified, complete uncertainty budget linking traceable sensor calibration, noise floors, and decision rules to a single governed threshold.
- **Dependent Claims:** BLK_R3_01, BLK_R3_13.
- **What CAN be Verified Without Closure:** Numerical comparison of candidate thresholds ($0.410\,\text{A}$ vs $0.500\,\text{A}$).
- **What CANNOT be Verified:** Legitimate de-energization decision boundary under ISO/IEC Guide 98-3.
- **Status:** `OPEN`

### BLK_R3_11: Rebound & Back-EMF Mechanisms Uncharacterized
- **Severity:** `MODERATE`
- **Root Evidence Required:** Physical spin-down back-EMF measurements, contactor bounce recordings, and inverter gate inhibit logs under maximum vehicle kinetic energy.
- **Dependent Claims:** Persistence window duration ($T_{\text{persist}} = 10.0\,\text{ms}$).
- **What CAN be Verified Without Closure:** Theoretical catalog of potential rebound failure modes.
- **What CANNOT be Verified:** Absolute upper bound on post-E-Stop transient duration or amplitude.
- **Status:** `OPEN`

### BLK_R3_12: tau_eff Provenance Untraceable
- **Severity:** `MODERATE`
- **Root Evidence Required:** Primary raw decay curves, fitting intervals, residual plots, and regression uncertainty calculations.
- **Dependent Claims:** Analytical flush lag $\Delta_{\text{flush}} = 1.117\,\text{ms}$.
- **What CAN be Verified Without Closure:** Arithmetic behavior of $e^{-t/2.8\,\text{ms}}$ in synthetic code.
- **What CANNOT be Verified:** That the physical vehicle powertrain actually decays at $2.8\,\text{ms}$.
- **Status:** `OPEN`

### BLK_R3_13: Vehicle Functional Safety Claims Not Established
- **Severity:** `STANDING`
- **Root Evidence Required:** Vehicle-level functional safety analysis (ISO 26262 / ISO 13849-1), hazard analysis and risk assessment (HARA), diagnostic coverage calculations, and independent notified body safety audit.
- **Dependent Claims:** Any claim of PL d/e, SIL, ISO compliance, or safety certification (strictly PROHIBITED and NOT_ESTABLISHED).
- **What CAN be Verified Without Closure:** Component manufacturer general product architecture statements.
- **What CANNOT be Verified:** Any functional safety or vehicle roadworthiness claim.
- **Status:** `OPEN`

---

## 3. Dependency Closure Rules

1. **Upstream Closure Prerequisite:** A downstream blocker **CANNOT** close until all of its upstream dependencies are closed with primary physical evidence.
   - For example: `BLK_R3_06` (Timing Traceability) cannot close until `BLK_R3_01` (Executable RMS), `BLK_R3_03` (Anti-Aliasing), `BLK_R3_04` (Scale), and `BLK_R3_07` (Timestamps) are closed.
2. **No Soft Closure:** Writing a document that describes how a blocker might be resolved in the future does not close the blocker. Only inspectable, hashed, traceable artifacts close blockers.
3. **Current Authoritative Summary:**
```text
TOTAL_BLOCKERS_AUDITED = 13
BLOCKERS_OPEN          = 13
BLOCKERS_CLOSED        = 0
FINAL_STATUS           = BLOCKED
```
