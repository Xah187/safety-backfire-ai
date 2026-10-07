# V3.4-N-CORR-04-R3 — RMS Region Boundary (v2)

**Document:** `outputs/v3_4_n_corr_04_r3/rms_boundary_v2.md`
**Supersedes:** `r2_r1/rms_region_boundary.md`
**Domain:** `CONTINUOUS-TIME MODEL RESULT` — exponential envelope / RMS-equivalent scalar (see `rms_model_scope_reconciliation.md`).

```text
MODEL_H = FROZEN | PRODUCTION_MODEL = UNCHANGED | FIELD_DATA = ZERO
PHYSICAL_CAPTURE_AUTHORIZATION = NOT_GRANTED | RESEARCH_DAQ_ACTUATION_AUTHORITY = ZERO
```

> **Scope label.** Everything below is a **CONTINUOUS-TIME MODEL** result. It is **not** asserted to be exact for `RMS-PROC-V1.0` until the discrete RMS implementation is reconciled and verified (`discrete_rms_specification.md`, blockers `BLK_R3_01/02`).

---

## 1. Preserved definitions

```text
B(Tw, tau)   = sqrt[ tau/(2·Tw) · (1 − exp(−2·Tw/tau)) ]          = I_RMS(t0+Tw) / I0
I0crit       = I_guarded / B(Tw, tau)
```

`I_RMS(t)` is strictly decreasing for `t ≥ t0`:

* Region 2: `d(I_RMS²)/dt = (I0²/Tw)·(exp(−2(t−t0)/tau) − 1) < 0`;
* Region 3: `I_RMS ∝ exp(−t/tau)`, decreasing.

Hence the threshold crossing is unique, and *which region contains it* is decided solely by comparing `I_RMS(t0+Tw) = I0·B` with `I_guarded`.

## 2. Three-way classification (including the equality case)

| Condition | Equivalent statement | Crossing location |
| :--- | :--- | :--- |
| `I0 < I0crit` | `I0·B < I_guarded` | **Region 2** — `t0 < t_rms < t0+Tw` (solve the transcendental equation) |
| `I0 = I0crit` | `I0·B = I_guarded` | **Boundary** — `t_rms = t0 + Tw` exactly; Region-2 and Region-3 formulas coincide |
| `I0 > I0crit` | `I0·B > I_guarded` | **Region 3** — `t_rms > t0+Tw`, `t_rms = t0 + tau·ln(I0·C/I_guarded)` |
| `I0 ≤ I_guarded` | — | No crossing: `I_RMS = I0` is already not above the threshold |

(R2-R1 wrote `I0 ≤ I0crit → Region 2`, which silently assigned the equality case to Region 2. R3 lists it separately.)

At the boundary the Region-3 formula gives `t0 + tau·ln(C/B) = t0 + Tw` because `C/B = exp(Tw/tau)`; this is verified numerically in the table below.

## 3. Moving-window endpoint wording (corrected)

The RMS at time `t` uses the **causal window `[t − Tw, t]`**: lower endpoint `t − Tw`, upper endpoint `t`.

| Region | Lower endpoint `t−Tw` | Upper endpoint `t` | Consequence |
| :--- | :--- | :--- | :--- |
| 1 | `< t0` | `< t0` | window all pre-onset: `I_RMS = I0` |
| 2 | `< t0` | `≥ t0` | window contains the step **and** the decay |
| 3 | `≥ t0` | `> t0` | window entirely in the decay: single exponential |

Correction of an R2-R1 slip: R2-R1 (`master_audit` Section 7.1) described the window at `k_start` as `[t0, t0+Tw]`. The window of an evaluation at time `t_k` is `(t_k − Tw, t_k]`; it equals `[t0, t0+Tw]` only for `t_k = t0 + Tw`.

## 4. Frozen analytical examples (recalculated)

Parameters: `Tw = 2.0 ms`, `tau = 2.8 ms`, `t0 = 13.0 ms`, `I_guarded = 0.410 A`.

> `tau = 2.8 ms` is an **EMPIRICAL_DESCRIPTIVE_FIT**; `I_guarded = 0.410 A` is a **LEGACY ILLUSTRATIVE VALUE** (`r2/guarded_threshold_v3.json`: *"NOT PRESERVED as an authoritative engineering threshold"*). They are used only to reproduce the earlier examples. The symbolic boundary does not depend on them.

```text
B           = 0.7295507347
C           = 1.4902730349
I0crit      = 0.410 / 0.7295507347 = 0.5619897020 A
tau·ln(C)   = 1.1170861746 ms
```

| `I0` [A] | Class | `I0·B` = `I_RMS(15.0 ms)` [A] | `t_phys` [ms] | `t_rms` [ms] | `t_rms − t_phys` [ms] |
| ---: | :--- | ---: | ---: | ---: | ---: |
| 0.450 | Region 2 | 0.328298 | 13.260653 | 14.103014 | 0.842360 |
| 0.500 | Region 2 | 0.364775 | 13.555663 | 14.612792 | 1.057129 |
| 0.550 | Region 2 | 0.401253 | 13.822531 | 14.937855 | 1.115324 |
| 0.561990 | **Boundary** | 0.410000 | 13.882914 | 15.000000 | 1.117086 |
| 0.600 | Region 3 | 0.437730 | 14.066163 | 15.183249 | 1.117086 |
| 0.800 | Region 3 | 0.583641 | 14.871673 | 15.988759 | 1.117086 |
| 1.000 | Region 3 | 0.729551 | 15.496475 | 16.613561 | 1.117086 |

Reproduced by `discrete_rms_verification.py` (continuous section) and re-checked by `audit_r3.py`.

Boundary continuity check (from the script): `I0 = I0crit·(1−10⁻⁶)` → Region 2, `t_rms = 14.9999972 ms`; `I0 = I0crit` → Boundary, `t_rms = 15.0 ms`; `I0 = I0crit·(1+10⁻⁶)` → Region 3, `t_rms = 15.0000028 ms`.

## 5. Sensitivity of `I0crit` to the threshold (parametric only, none authoritative)

The threshold is itself unresolved (documents carry 0.410, 0.413 and, under an *unsupported* 5 A/V assumption, 0.460):

| `I_guarded` [A] (label) | `I0crit` [A] |
| ---: | ---: |
| 0.410 (legacy R1/R2 value) | 0.561990 |
| 0.413 (CORR-04 protocol value) | 0.566102 |
| 0.460 (R2 value derived under an unsupported 5 A/V assumption) | 0.630525 |

This table selects nothing and tunes nothing; it shows only that `I0crit` scales linearly with the (unresolved) threshold.

## 6. Status

```text
REGION_BOUNDARY_SYMBOLIC          = VERIFIED (continuous-time model)
REGION_BOUNDARY_FOR_RMS_PROC_V1_0 = NOT_VERIFIED (discrete implementation not reconciled with frozen implementation)
```
