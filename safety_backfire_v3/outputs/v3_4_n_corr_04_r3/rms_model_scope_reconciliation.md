# V3.4-N-CORR-04-R3 — RMS Model Scope Reconciliation

**Document:** `outputs/v3_4_n_corr_04_r3/rms_model_scope_reconciliation.md`
**Supersedes (scope wording only):** `r2_r1/rms_model_domain.md`, `r2_r1/rms_crossing_reconciliation.md`, `r2/rms_closed_form.md`
**Status:** `ANALYTICAL_MODEL_SCOPED` — continuous-time model only. Not a measurement result.

```text
MODEL_H                          = FROZEN (k0=2.40, beta_d=0.08, beta_l=0.12, beta_pitch=0.22)
PRODUCTION_MODEL                 = UNCHANGED
FIELD_DATA                       = ZERO
GROUND_TRUTH                     = NOT_ESTABLISHED
REAL_WORLD_VALIDATION            = NOT_ESTABLISHED
PHYSICAL_CAPTURE_AUTHORIZATION   = NOT_GRANTED
RESEARCH_DAQ_ACTUATION_AUTHORITY = ZERO
```

---

## 1. Signal definition (explicit, single choice)

```text
MODEL_DOMAIN = CONTINUOUS EXPONENTIAL ENVELOPE / RMS-EQUIVALENT SCALAR SIGNAL
```

`i(t)` in this document is a **non-negative scalar function of time, in amperes**, defined piecewise by

```text
i(t) = I0                              for t <  t0
i(t) = I0 * exp(-(t - t0)/tau_eff)     for t >= t0          (continuous at t0)
```

and interpreted as the **RMS-equivalent magnitude (envelope)** of the motor current, i.e. a quantity that is already "RMS-like" and slowly varying.

**What `i(t)` is NOT:**

| Prohibited reading | Reason |
| :--- | :--- |
| Instantaneous single-phase current `i_U(t)` | Contains a carrier (fundamental and PWM ripple) that this model does not have. |
| Instantaneous 3-phase phase-current waveform set `(i_U, i_V, i_W)` | No carrier, no phase relationship, no unbalance. |
| A measured quantity | `FIELD_DATA = ZERO`; nothing here was acquired. |

The model **must not** be applied to, or compared with, an instantaneous AC waveform unless a carrier model is explicitly added and re-derived (not done here).

### 1.1 Why the carrier matters (quantified, model-based, NOT evidence)

The closed forms below integrate `i²` over a **2.0 ms** window. If the quantity actually processed were a single phase current with a fundamental of electrical frequency `f_e`, a 2.0 ms window is only a fraction of a fundamental period. Small-angle estimate for a window centred on a zero crossing of `i = Î·sin(ωt)`:

```text
I_RMS(window centred on zero crossing) ≈ Î · ω · Tw / sqrt(12)        (valid for ω·Tw << 1)
steady RMS                              = Î / sqrt(2)
```

Illustration (arithmetic only): `f_e = 60 Hz → ω·Tw = 0.754 → ratio ≈ 0.218·Î` versus `0.707·Î`. A 2.0 ms moving RMS of a single phase current at tens of Hz is therefore **not** an RMS-equivalent; it can dip periodically far below the steady RMS. The R2 manifest lists electrical frequencies of 10–90 Hz. Whether the project actually applies RMS-PROC-V1.0 to a single phase trace (the CORR-04 protocol says "Phase U current trace") or to an RMS-equivalent scalar is **not established**. This is tracked as blocker `BLK_R3_08` (signal-domain applicability). It is *one more reason* the continuous model must stay scoped.

---

## 2. dq-vector language (only if retained)

No `i_dq` language appears in the R2-R1 documents; `d-q` language appears in R2 `motor_controller_compatibility.md`. If dq language is retained anywhere, the following relationships are the **only** permitted ones, and each holds **only for balanced, sinusoidal, steady-state** conditions:

| Clarke/Park scaling convention | `‖i_dq‖` in terms of peak phase amplitude `Î` | `‖i_dq‖` in terms of phase RMS `I_rms,ph = Î/√2` |
| :--- | :---: | :---: |
| Amplitude-invariant (factor 2/3) | `Î` | `√2 · I_rms,ph` |
| Power-invariant (factor √(2/3)) | `√(3/2) · Î` | `√3 · I_rms,ph` |

Rules:

1. `‖i_dq‖` is **not universally identical** to phase RMS, and the factor depends on the scaling convention (which is not established for any Curtis-reported or probe-measured quantity in this project).
2. During transients (the very regime of the E-Stop decay), under unbalance, or with ripple, the table does **not** apply.
3. Any RMS-equivalent scalar used by this model must be declared as `I_eq = ‖i_dq‖ / κ` with `κ` stated. Until `κ` and the convention are stated, dq language **may not** be used to justify `i(t)` as "RMS".

---

## 3. Retained continuous-time equations (unchanged, re-verified)

Running RMS over the **causal window `[t − Tw, t]`** (lower endpoint `t − Tw`, upper endpoint `t`):

`I_RMS²(t) = (1/Tw) ∫_{t−Tw}^{t} i²(τ) dτ`.

**Region 1 — `t < t0`** (both window endpoints before the onset):
`I_RMS(t) = I0`.

**Region 2 — `t0 ≤ t < t0 + Tw`** (lower endpoint `t − Tw < t0`, upper endpoint `t ≥ t0`; window straddles the onset):

```text
I_RMS²(t) = I0² · [ 1 − (t−t0)/Tw + tau_eff/(2Tw) · ( 1 − exp(−2(t−t0)/tau_eff) ) ]
```

**Region 3 — `t ≥ t0 + Tw`** (lower endpoint `t − Tw ≥ t0`; window entirely inside the decay):

```text
I_RMS(t) = I0 · C(Tw, tau_eff) · exp(−(t−t0)/tau_eff)
C(Tw, tau_eff) = sqrt( tau_eff/(2Tw) · ( exp(2Tw/tau_eff) − 1 ) )
```

Continuity (re-derived and numerically re-checked by `discrete_rms_verification.py`):

* at `t0`: Region 1 and Region 2 both give `I0`;
* at `t0 + Tw`: Region 2 and Region 3 both give `I0·B`, with `B = sqrt( tau_eff/(2Tw) · (1 − exp(−2Tw/tau_eff)) )`.

Numerical values for `Tw = 2.0 ms`, `tau_eff = 2.8 ms`: `B = 0.7295507347`, `C = 1.4902730349`, `tau_eff·ln C = 1.1170861746 ms`.

**Verification status:** `VERIFIED_CONDITIONALLY` — verified algebraically and numerically **as a continuous-time result under the model domain of Section 1**. Not verified for the discrete implementation (see `discrete_rms_specification.md`) and not verified against any physical signal.

---

## 4. Mandatory wording replacements

| Unconditional wording (R2 / R2-R1 and earlier) | Replacement |
| :--- | :--- |
| "exact physical delay" | "exact conditional analytical result under the continuous exponential-envelope model" |
| "exact analytical delay" | "exact conditional analytical result under the continuous exponential-envelope model" |
| "the RMS lags the current by 1.12 ms" | "in the continuous model, **when the crossing lies in Region 3**, `t_rms − t_phys = tau_eff·ln C` (conditional analytical result)" |
| "the moving RMS window adds 2.0 ms" | "the RMS crossing time follows the Region-2 or Region-3 equation; no fixed window delay is implied" |
| "frozen RMS-PROC-V1.0 verified" | "reference model of the *documented* parameters self-consistent with the continuous equations; frozen implementation not located" |

---

## 5. `tau_eff = 2.8 ms`

```text
TAU_EFF_CLASSIFICATION   = EMPIRICAL_DESCRIPTIVE_FIT
TAU_EFF_PROVENANCE       = REPORT_BASED_NO_RAW_TRACE
TAU_EFF_PHYSICAL_CONSTANT = NO
TAU_EFF_GENERALIZATION   = PROHIBITED
```

* It is a descriptive single-exponential parameter attributed to a report; **no raw trace, fit window, fit residual or goodness-of-fit** exists in the repository.
* It is **not** a physical constant of the vehicle, the motor, the controller or any safety system, and **no document establishes dependence or independence** of it on motor type, controller/firmware, operating current, speed, DC-link voltage, STO behaviour, or the measurement chain.
* Any decimal result derived from it (e.g. `1.117 ms`) inherits this status (see `rms_crossing_general_solution.md`, Section 6).

## 6. What this document does not claim

No physical validation, no safety certification, no ISO/PL/SIL claim, no readiness. `MODEL_H` and production code were not touched.
