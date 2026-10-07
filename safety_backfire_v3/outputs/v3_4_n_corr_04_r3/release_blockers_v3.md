# V3.4-N-CORR-04-R3 — Release Blockers Ledger (v3)

**Document:** `outputs/v3_4_n_corr_04_r3/release_blockers_v3.md`
**Supersedes:** `r2_r1/release_blockers.md` (see Section 5 for the disposition of each R2-R1 item)

```text
V3_4_N_CORR_04_R3_STATUS          = BLOCKED
BLOCKERS_OPEN                     = 13
BLOCKERS_CLOSED                   = 0
PHYSICAL_CAPTURE_AUTHORIZATION    = NOT_GRANTED
RESEARCH_DAQ_ACTUATION_AUTHORITY  = ZERO
MODEL_H                           = FROZEN (k0=2.40, beta_d=0.08, beta_l=0.12, beta_pitch=0.22)
PRODUCTION_MODEL                  = UNCHANGED
FIELD_DATA                        = ZERO | GROUND_TRUTH = NOT_ESTABLISHED | REAL_WORLD_VALIDATION = NOT_ESTABLISHED
```

**Closure rule.** A blocker closes **only when the underlying evidence exists** (an artifact that can be inspected, hashed and traced). A document that *describes* the evidence, a model that *simulates* it, or a script that *self-checks* does not close anything. This milestone produced documents, a reference model and an audit script; therefore **no blocker is closed**.

---

## 1. Ledger

| ID | Severity | Blocker | Evidence required to close | Evidence present | Status |
| :--- | :---: | :--- | :--- | :--- | :---: |
| **BLK_R3_01** | CRITICAL | **RMS-PROC-V1.0 not defined unambiguously and not implemented.** Documents conflict (20 kHz filter stage vs raw input; `<=0.413` vs `<=0.410` vs `<0.410`); no executable or hash exists | One normative definition (filter question settled), an executable committed with recorded hash, test vectors reproduced by *that* executable | reference model of the documented parameters only | `OPEN` |
| **BLK_R3_02** | CRITICAL | **Continuous boundary not verified for the frozen discrete implementation** (frame-grid quantization up to 0.1 ms; sub-frame agreement to < 1 sample in the *reference* model only) | Frozen implementation verified against the continuous equations on the vectors in `discrete_rms_specification.md` | reference-model comparison only | `OPEN` |
| **BLK_R3_03** | CRITICAL | **Anti-alias chain not justified** (acquisition mode/decimation undocumented; out-of-band content unknown; 20 kHz filter not verified) | Archived instrument manuals; recorded acquisition mode/decimation; spectral or higher-rate reference evidence; filter specification if one is intended | none | `OPEN` |
| **BLK_R3_04** | CRITICAL | **Current measurement scale and termination not traceable** (`HISTORICAL_CURRENT_SCALE = UNRESOLVED`; historical termination unknown) | Original setup evidence for historical trials, **or** a new traceable acquisition with recorded range/termination/autobalance and calibration evidence | none | `OPEN` |
| **BLK_R3_05** | CRITICAL | **Exact controller / firmware / motor configuration not reconciled** (`MOTOR_CONTROLLER_COMPATIBILITY = BLOCKED`) | Evidence for each row of the dimension table in `controller_motor_compatibility_reconciliation_v3.md` | none | `OPEN` |
| **BLK_R3_06** | CRITICAL | **Timing data not independently traceable** (`TIMING_EVIDENCE = REPORT_BASED`; manifest `t_phys` and `Delta_flush` are derived) | Raw time-series with hashes and acquisition metadata, mapped to trials | none | `OPEN` |
| **BLK_R3_07** | CRITICAL | **Timestamp semantics not verified** (clock source, accuracy, sample-rate tolerance, jitter, trigger latency, cross-channel skew) | Items T1–T8 of `timing_timestamp_governance.md` | none | `OPEN` |
| **BLK_R3_08** | MAJOR | **Signal-domain applicability unresolved** (is the processed quantity an RMS-equivalent scalar or a single-phase trace? a 2.0 ms window is a fraction of a fundamental period at 10–90 Hz) | A defined measured quantity and a derivation/justification that the moving RMS on it is the intended RMS-equivalent | none | `OPEN` |
| **BLK_R3_09** | MAJOR | **Instrument identity provenance** (serial numbers asserted from an inventory that is not in the repository; no calibration evidence) | Label photographs / inventory record / calibration evidence | none | `OPEN` |
| **BLK_R3_10** | MAJOR | **Guarded-threshold authority** (0.410 / 0.413 / 0.460 A all non-authoritative; each tied to an unresolved scale) | A single threshold derived from traceable scale and uncertainty, via a governed decision | none | `OPEN` |
| **BLK_R3_11** | MODERATE | **Rebound mechanisms uncharacterized** (all candidates; no measured duration or amplitude bound) | Direct measurement or OEM documentation per mechanism, for the exact unit | none | `OPEN` |
| **BLK_R3_12** | MODERATE | **`tau_eff` provenance** (no raw trace, no fit window/residual; generalization prohibited) | A traceable fit with stated window, residual and conditions; dependence evidence if generalization is ever sought | none | `OPEN` |
| **BLK_R3_13** | STANDING | **Safety claims not established** (`VEHICLE_FUNCTIONAL_SAFETY_CLAIM = NOT_ESTABLISHED`; no PL/SIL/ISO claim for any unit or function) | Exact-unit manufacturer safety documentation applicable to the exact function **and** a vehicle-level analysis; not pursued here | none | `OPEN` |

## 2. Conditions under which this milestone could be re-classified

`BLOCKED` may change **only if all of the following are actually evidenced** (not merely documented):

1. exact discrete RMS implementation defined **and verified** (BLK_R3_01, 02);
2. anti-aliasing chain justified (BLK_R3_03);
3. physical/current measurement scale traceable (BLK_R3_04, 09);
4. exact controller/firmware/motor configuration reconciled (BLK_R3_05);
5. historical or new timing data independently traceable (BLK_R3_06);
6. timestamp semantics verified (BLK_R3_07).

None holds today. Even then, `PHYSICAL_CAPTURE_AUTHORIZATION` remains a separate governed decision and no readiness, validation, safety or compliance claim follows.

## 3. Evidence classification of everything produced by R3

| Artifact | Class |
| :--- | :--- |
| Closed-form equations, boundary, general solution | analytical, continuous-time model |
| `discrete_rms_verification.py` results | self-consistency of a **reference model** with synthetic data |
| `persistence_modeb_reference.py` vectors | logic verification of a **specification** |
| Manufacturer figures | `MFR_VIA_SEARCH_SUMMARY` (primary manuals not archived) |
| Everything else | audit findings |

None of these is field data, ground truth, or validation.

## 4. Circular closure criteria removed

Removed from R2-R1 (`BLK_PERSIST_04` remediation and "Pathway to READY_FOR_REAUDIT" item 4): *"verifying `Delta_flush ≈ 1.12 ms` in Region 3"* / *"confirming `Delta_flush ≈ 1.12 ms`"*. Future raw captures must **not** be required to confirm 1.117 ms. Required instead, for any future *authorised* acquisition analysis:

1. an **independently measured physical/envelope crossing** (method and threshold stated, not derived from the RMS result);
2. an **independently measured RMS crossing** (by the frozen implementation, frame-grid timestamp);
3. the **observed offset** (item 2 minus item 1) with its uncertainty or an explicit `UNCERTAINTY_UNKNOWN`;
4. **comparison against the analytical prediction** for the actual conditions (the Region-2 or Region-3 solution, and the discrete-model prediction including frame-grid phase);
5. a **documented explanation of any deviation** (model domain, `tau_eff` applicability, filtering, scale, timing);
6. **no presupposition of a pass/fail numerical outcome**: agreement and disagreement are both reported findings; neither is a closure criterion.

These criteria describe how results must be analysed; they **do not authorise** any capture.

## 5. Disposition of R2-R1 / R2 items

| Prior item | Disposition |
| :--- | :--- |
| `BLK_PERSIST_01` (scale; "lock to 5 A/V", "ISO/IEC 17025 certificate", DMM check) | → `BLK_R3_04`, `BLK_R3_09`; "lock to 5 A/V" **withdrawn** (range chosen from the expected envelope); a specific certificate scheme is not presumed |
| `BLK_PERSIST_02` (PMSM vs AC induction; encoder alignment, licence) | → `BLK_R3_05`; feedback-type and licence presumptions **withdrawn** |
| `BLK_PERSIST_03` (raw oscillograms missing) | → `BLK_R3_06` |
| `BLK_PERSIST_04` (timing; "verify 1.12 ms") | → `BLK_R3_06/07`; circular clause **removed** (§4) |
| `BLK_PERSIST_05` (safety classification) | → `BLK_R3_13` |
| `BLK_PERSIST_06` (rebound mechanics) | → `BLK_R3_11`; "worst-case contactor bounce" presumes a contactor in the path — unproven |
| R2 `BLK_00_PERSIST` | remains `OPEN` (subsumed by the above) |

## 6. Prohibited output notice

No statement in this milestone constitutes physical validation, safety certification, ISO compliance, PL d/e, SIL, vehicle-level functional safety, or production readiness.
