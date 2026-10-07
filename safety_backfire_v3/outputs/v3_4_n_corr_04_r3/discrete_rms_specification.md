# V3.4-N-CORR-04-R3 — Discrete RMS Specification (documented RMS-PROC-V1.0 parameters)

**Document:** `outputs/v3_4_n_corr_04_r3/discrete_rms_specification.md`
**Companion script:** `discrete_rms_verification.py` (results: `discrete_rms_verification_results.json`)
**Status:** `PRIMARY_BLOCKER` — `BLK_R3_01` / `BLK_R3_02` OPEN.

```text
MODEL_H = FROZEN | PRODUCTION_MODEL = UNCHANGED | FIELD_DATA = ZERO
PHYSICAL_CAPTURE_AUTHORIZATION = NOT_GRANTED | RESEARCH_DAQ_ACTUATION_AUTHORITY = ZERO
```

---

## 1. Finding R3-E01 / R3-E02 — "frozen" is not an implementation

1. **No executable `RMS-PROC-V1.0` exists in the repository.** A search of `scripts/` finds only references to the *name* (parameter checks in audit scripts); no RMS function, no hash. "Frozen" is a documentary label on a parameter set.
2. **The documents disagree on what V1.0 is.**

| Item | CORR-04 protocol (`V3_4_N_CORR_04_MEASUREMENT_PROTOCOL.md`) | R2 / R2-R1 documents |
| :--- | :--- | :--- |
| Input to the RMS | after a **"Hardware 4th-Order Low-Pass Filter (fc = 20 kHz)"** | "raw digitized stream `i[n]`, no filter" |
| Comparator / threshold | `I_RMS[k] <= 0.413 A` | `<= 0.410` (R2 FSM) and `< 0.410` (R2-R1 pseudocode) |
| Window | N = 2000 samples, M = 100 | "2.0 ms, 0.1 ms"; R2-R1 master audit also says "N_w = 20 samples, fs = 10 kHz" (an error: 10 kHz is the *frame* rate, 20 is *frames per window*) |

3. A 20 kHz hardware filter is **not verified** to exist (`anti_aliasing_audit.md`). Whether V1.0 includes a filter stage, of what type, is **undefined**.

Therefore the exact frozen digital RMS implementation **cannot be declared**. What follows defines the **documented parameter set** exactly (what the CORR-04 formula says, with every ambiguity resolved explicitly) and provides a **reference model** to quantify its behaviour. It is not "the" implementation.

## 2. Normative definition of the documented parameter set

| Item | Definition adopted | Basis |
| :--- | :--- | :--- |
| Sample rate `fs` | 1 000 000 Sa/s, `Δts = 1 µs` | CORR-04 protocol §3.1 |
| Decimation behaviour | **None inside the RMS stage.** The input is the stored 1.0 MSa/s sequence; frame skipping (M = 100) is *output* thinning, not data decimation. Any decimation by the instrument upstream is **UNDOCUMENTED** (see `anti_aliasing_audit.md`) | spec silent; stated to prevent hidden assumptions |
| Window length `N` | **2000 samples** (not 2001) | CORR-04 formula `Σ_{m=0}^{N−1}` with `N = 2000` |
| Sample timestamps | `t_n = n / fs`, `n = 0,1,2,…`, `n = 0` = first stored sample (logical time; mapping to physical time undefined, see `timing_timestamp_governance.md`) | definition |
| Window membership | frame at index `n = kM` uses samples `n−1999 … n` | `i[kM − j]`, `j = 0…N−1` |
| Window inclusivity | **right-closed, left-open** in timestamps: `(t_n − 2.0 ms, t_n]`; spans 2000 samples = 2000 sample intervals; timestamp range covered = 1.999 ms | consequence of N = 2000 |
| Normalization | `1/N = 1/2000` (not `1/2001`) | formula |
| Evaluation step | `M = 100` samples = 0.1 ms; frames at `n = 100·k` | CORR-04 |
| Evaluation timestamp | `t_k = k·M / fs = k·0.1 ms` = **right edge** of the window (causal) | definition |
| First valid RMS output | **`k = 20`, `n = 2000`, `t = 2.0 ms`**, window = samples 1…2000. Frames `k < 20` would need `n−1999 < 0`; they are **not emitted** (no zero padding, no partial windows). The earliest full-window *sample* is `n = 1999`, but it is off the 0.1 ms frame grid | derived |
| Threshold comparator | **strict**: a frame qualifies iff `I_RMS[k] < I_guarded` (declared parameter; legacy `<=` documents are in conflict, see `persistence_semantics_v5.md` §2) | choice, labelled |
| Threshold-crossing timestamp | `t_k` of the **first valid frame** with `I_RMS[k] < I_guarded`. It is a **frame-grid timestamp** (no interpolation), always ≥ the underlying sub-frame crossing. If the first valid frame (`k = 20`) is already below threshold it is reported as `BELOW_AT_FIRST_VALID_FRAME`, **not** as a crossing | definition |
| Edge handling (end of record) | frames with `kM` beyond the last stored sample are not emitted; a record shorter than 2000 samples yields no output | definition |
| Numerical precision | IEEE-754 binary64; window sum = `math.fsum` (exactly rounded) of binary64 squares; `sqrt`; comparison in binary64. ADC-code → ampere conversion is **not defined** (current scale unresolved), so the stage is specified on already-scaled floats | reference model |

### 2.1 Resolution: 2000 samples or 2001 timestamped points?

The documented formula has `N = 2000` terms, so **2000 samples**. A window of 2001 timestamped points arises only if *both* endpoints `t−2.0 ms` and `t` are included (denominator 2001, or trapezoid weights); that is a **different, non-frozen definition**. Its numerical effect was quantified (Section 4.3): **≤ 1 µs** on the crossing time. The ambiguity is immaterial numerically for these vectors but is **definitionally material** (reproducibility), so it is fixed above.

## 3. Reference model

`discrete_rms_verification.py`: synthetic exponential-envelope samples `i[n]` (not phase current, not field data), the normative per-frame function `rms_frame_normative()`, a prefix-sum sub-frame analysis (for isolating error sources), and the continuous-time solver from `rms_crossing_general_solution.md`. All checks are deterministic (no RNG/clock).

## 4. Deterministic test vectors: continuous vs discrete

`Tw = 2.0 ms`, `tau = 2.8 ms`, `I_guarded = 0.410 A` (legacy illustrative), `t0 = 13.0 ms` (on the frame grid). Differences in ms; `riemann` = first *sample* below threshold (sub-frame, window-A) minus continuous `t_rms`; `grid` = frame time minus first sample below threshold; `total` = frame time minus continuous `t_rms`.

| `I0` [A] | Region | `t_rms` continuous [ms] | frame time [ms] | `riemann` [ms] | `grid` [ms] | `total` [ms] |
| ---: | :--- | ---: | ---: | ---: | ---: | ---: |
| 0.500 | 2 | 14.612792 | 14.700 | +0.000208 | 0.087 | +0.087208 |
| 0.550 | 2 | 14.937855 | 15.000 | +0.000145 | 0.062 | +0.062145 |
| 0.562 (`I0crit`) | boundary | 15.000000 | 15.000 | 0.000000 | 0.000 | 0.000000 |
| 0.600 | 3 | 15.183249 | 15.200 | −0.000249 | 0.017 | +0.016751 |
| 0.800 | 3 | 15.988759 | 16.000 | +0.000241 | 0.011 | +0.011241 |
| 1.000 | 3 | 16.613561 | 16.700 | +0.000439 | 0.086 | +0.086439 |

### 4.1 Grid-phase sweep (t0 slid across one 0.1 ms step, 20 phases)

| `I0` [A] | `total` min [ms] | `total` max [ms] |
| ---: | ---: | ---: |
| 0.500 | +0.002208 | +0.097208 |
| 0.800 | +0.001241 | +0.096241 |

### 4.2 Interpretation

* **Sub-frame (Riemann/sample) difference**: |difference| ≤ 0.44 µs across all vectors (< one 1 µs sample); the sign is dominated by sample-time quantization. The discrete moving-average and the continuous integral agree to well below the sample period.
* **Frame-grid quantization** dominates: the reported crossing is the *next* frame at or after the sub-frame crossing, hence **up to 0.1 ms late** and dependent on the (physically unknown) phase between the event and the frame grid.
* In these vectors the frame time was **never earlier** than the continuous crossing (`total ≥ +0.0012 ms`).
* **Consequence for `Delta_flush`**: an *observed* offset in frame-time terms is `Delta_cont + [0, 0.1) ms` (plus all physical effects not modelled). This is why future captures must not be asked to "confirm 1.117 ms" (`release_blockers_v3.md`).

### 4.3 Window-definition variants (sub-frame crossing, difference to documented window A)

| Variant | Definition | max |Δ| over vectors |
| :--- | :--- | ---: |
| A (documented) | 2000 samples, denominator 2000 | — |
| B | 2001 points, denominator 2001 | 0.001 ms |
| C | 2001 points, trapezoid weights, denominator 2000 | 0.001 ms |

### 4.4 Numerical precision

At the crossing frames, prefix-sum vs `fsum` RMS differ by ≤ 8.2·10⁻¹⁵ A. The smallest margin between a crossing frame's RMS and the threshold in these vectors is 7.3·10⁻⁵ A (boundary vector) and ≥ 1.7·10⁻³ A otherwise, i.e. ≥ 10⁹ times the numerical error: the comparator outcome is numerically robust **in this synthetic setting**. (Real data have noise, quantization and scale uncertainty not modelled.)

## 5. Status — what is and is not claimed

```text
CONTINUOUS_BOUNDARY_EXACT_FOR_RMS_PROC_V1_0 = NOT_DECLARED   (frozen implementation not located; definition conflicts)
REFERENCE_MODEL_VS_CONTINUOUS_EQUATIONS     = SELF_CONSISTENT (synthetic envelope; quantified above)
RMS_PROC_V1_0_IMPLEMENTATION                = NOT_LOCATED
RMS_PROC_V1_0_DEFINITION                    = INCONSISTENT_ACROSS_MILESTONES (filter stage, threshold, comparator)
```

Closure of `BLK_R3_01/02` requires: one normative definition (incl. the filter question), an executable implementation committed with a recorded hash, and test vectors reproduced by *that* implementation. Writing this document does not close them.
