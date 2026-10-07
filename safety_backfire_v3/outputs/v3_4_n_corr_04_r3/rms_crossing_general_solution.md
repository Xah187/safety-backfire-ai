# V3.4-N-CORR-04-R3 — General RMS Crossing Solution (Region 2 and Region 3)

**Document:** `outputs/v3_4_n_corr_04_r3/rms_crossing_general_solution.md`
**Supersedes:** `r2_r1/rms_crossing_reconciliation.md` (contains a numerical error, see Section 7)
**Domain:** `CONTINUOUS-TIME MODEL RESULT` — exponential envelope / RMS-equivalent scalar.

```text
MODEL_H = FROZEN | PRODUCTION_MODEL = UNCHANGED | FIELD_DATA = ZERO
PHYSICAL_CAPTURE_AUTHORIZATION = NOT_GRANTED | RESEARCH_DAQ_ACTUATION_AUTHORITY = ZERO
```

---

## 1. Definitions

```text
t_phys : envelope crossing          i(t_phys)    = I_guarded      →  t_phys = t0 + tau·ln(I0/I_guarded)      (I0 > I_guarded)
t_rms  : running-RMS crossing       I_RMS(t_rms) = I_guarded
Delta_flush = t_rms − t_phys
x = t − t0
```

## 2. Region-2 crossing: the transcendental equation

For `I0 < I0crit` the crossing satisfies `0 < x < Tw` and

```text
g(x) = 1 − x/Tw + tau/(2·Tw) · ( 1 − exp(−2x/tau) )  =  (I_guarded / I0)²
```

* `g(0) = 1`, `g(Tw) = B²`, and `g'(x) = (exp(−2x/tau) − 1)/Tw < 0` for `x > 0`.
* `g` is **strictly decreasing**, so there is **exactly one** root in `(0, Tw]` iff `(I_guarded/I0)² ≥ B²` (Region 2 or boundary).
* The root has no closed form (it mixes `x` and `exp(−2x/tau)`); in particular it **cannot** be reduced to `tau·ln C`.

## 3. Robust numerical root procedure (deterministic)

```text
Input : I0, I_guarded, Tw, tau          with  I_guarded < I0 < I0crit
target = (I_guarded/I0)²
lo = 0 ; hi = Tw                        # bracket: g(lo)=1 > target >= g(hi)=B²
repeat (max 200):
    mid = (lo + hi)/2
    if g(mid) > target: lo = mid  else: hi = mid
    stop when hi − lo <= 4·eps·max(1, hi)
x = (lo + hi)/2 ;  t_rms = t0 + x
```

Why bisection: the bracket is guaranteed by monotonicity, no derivative or initial guess is needed, and it cannot diverge. Use `expm1` for `1 − exp(−2x/tau)` to avoid cancellation at small `x`. Each iteration halves the bracket; ~51 iterations reach binary64 resolution for `Tw = 2.0 ms`. A Newton polish step using `g'` is optional and not required. Reference implementation: `solve_region2_root()` in `discrete_rms_verification.py`.

## 4. Region-3 crossing

For `I0 > I0crit`:

```text
t_rms = t0 + tau · ln( I0·C / I_guarded )
Delta_flush = t_rms − t_phys = tau · ln(C)      (independent of I0 and of I_guarded)
```

`Delta_flush = tau·ln(C)` applies **only when the threshold crossing lies in Region 3** (and, by continuity, at the boundary). It is **not** a general formula and is **not** valid in Region 2.

## 5. Verification (`Tw = 2.0 ms`, `tau = 2.8 ms`, `t0 = 13.0 ms`, `I_guarded = 0.410 A`)

| Case | Region | `t_phys` [ms] | `t_rms` [ms] | `Delta_flush` [ms] | Method |
| :--- | :--- | ---: | ---: | ---: | :--- |
| `I0 = 0.500 A` | **Region 2** | 13.555663 | 14.612791549 | **1.057129** | bisection, 51 iterations, residual 2.2·10⁻¹⁶ |
| `I0 = 0.800 A` | **Region 3** | 14.871673 | 15.988758965 | **1.117086** | closed form |

Expected values given in the task (`13.556 / 14.613 / 1.057` and `14.872 / 15.989 / 1.117`) are **reproduced to the stated precision**; they were recomputed independently, not hard-coded. For `I0 = 0.5 A`: `x = 1.612791549 ms`, and `I_RMS(t0+Tw) = 0.364775 A < 0.410 A`, confirming Region 2. For `I0 = 0.8 A`: `I_RMS(15.0 ms) = 0.583641 A > 0.410 A`, confirming Region 3.

### 5.1 Dependence of `Delta_flush` on `I0` (Region 2)

| `I0` [A] | Region | `Delta_flush` [ms] |
| ---: | :--- | ---: |
| 0.450 | 2 | 0.842360 |
| 0.500 | 2 | 1.057129 |
| 0.550 | 2 | 1.115324 |
| 0.561990 (`I0crit`) | boundary | 1.117086 |
| ≥ 0.600 | 3 | 1.117086 (constant) |

As `I0 → I_guarded⁺`, both crossings tend to `t0`, so `Delta_flush → 0`. These are the tabulated values only; no monotonicity claim beyond the table is made.

## 6. Status of the decimal value 1.117 ms

`1.117 ms` is **not physically exact**. It equals `tau_eff · ln C` with `tau_eff = 2.8 ms`, and `tau_eff` is an **EMPIRICAL_DESCRIPTIVE_FIT** with report-based provenance (no raw trace). The decimals shown are exact **only as arithmetic on the stated model parameters** (`1.1170861746 ms`). Replacement wording: *"exact conditional analytical result under the continuous exponential-envelope model"*. It is also a continuous-time result; the discrete implementation adds a frame-time quantization of up to 0.1 ms (`discrete_rms_specification.md`).

## 7. Correction of an R2-R1 numerical error

R2-R1 (`master_audit` §4.2, `rms_crossing_reconciliation.md`) reported for `I0 = 0.5 A`: `x ≈ 1.608 ms`, `t_rms ≈ 14.608 ms`, `Delta_flush ≈ 1.053 ms`. Substituting `x = 1.608` into the R2-R1 equation gives `g = 0.674037`, not the required `0.672400`; i.e. the R2-R1 values do not satisfy R2-R1's own equation. Correct values: `x = 1.612792 ms`, `t_rms = 14.612792 ms`, `Delta_flush = 1.057129 ms`.

## 8. Prohibited uses

* No use of `1.117 ms` as an acceptance target, a pass/fail criterion, or a "confirmation" target for future captures (see `release_blockers_v3.md`, Section 4).
* No transfer to any physical signal without establishing the model domain and `tau_eff` applicability.
