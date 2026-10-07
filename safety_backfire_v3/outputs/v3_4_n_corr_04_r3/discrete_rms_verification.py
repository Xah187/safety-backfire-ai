#!/usr/bin/env python3
"""
V3.4-N-CORR-04-R3 — Discrete RMS reference model & continuous-vs-discrete verification.

SCOPE / STATUS (read first)
---------------------------
* This file is a REFERENCE MODEL of the *documented* RMS-PROC-V1.0 parameters
  (1.0 MSa/s, N = 2000-sample rectangular window, M = 100-sample step).
  It is NOT the frozen production implementation: no executable RMS-PROC-V1.0
  source or hash exists in the repository (see discrete_rms_specification.md,
  finding R3-E01).  Agreement between this model and the continuous-time
  equations says nothing about the physical measurement chain.
* The envelope signal used here is a synthetic, analytically-defined exponential
  envelope (NOT a phase-current waveform, NOT field data).
* tau_eff = 2.8 ms is an EMPIRICAL_DESCRIPTIVE_FIT; I_guarded = 0.410 A is a
  LEGACY ILLUSTRATIVE value (guarded_threshold_v3.json: "NOT PRESERVED as an
  authoritative engineering threshold").  Both are used only to reproduce the
  prior analytical examples.
* Pure-Python (no numpy), IEEE-754 binary64, deterministic: no RNG, no clocks.

Usage:  python3 discrete_rms_verification.py [--write-json]
"""

import json
import math
import os
import sys

# --------------------------------------------------------------------------
# Documented RMS-PROC-V1.0 parameters (CORR-04 / CORR-04-R1 documents)
# --------------------------------------------------------------------------
FS_HZ = 1_000_000          # documented digitizer rate (decimation behaviour UNDOCUMENTED)
N_WINDOW = 2000            # documented N = Tw * fs  (half-open window, 2000 samples)
M_STEP = 100               # documented step = 0.1 ms = 100 samples
SAMPLE_PERIOD_MS = 1.0e-3  # 1 us expressed in ms
STEP_MS = M_STEP * SAMPLE_PERIOD_MS
TW_MS = N_WINDOW * SAMPLE_PERIOD_MS

# Illustrative parameters reproducing earlier analytical examples (NOT authoritative)
TAU_EFF_MS = 2.8           # EMPIRICAL_DESCRIPTIVE_FIT
I_GUARDED_A = 0.410        # LEGACY_ILLUSTRATIVE_VALUE
T0_MS = 13.0               # arbitrary example onset time
N_TRACE = 30000            # 30 ms synthetic record


class VerificationFailure(Exception):
    pass


# --------------------------------------------------------------------------
# 1. Continuous-time model (exponential envelope / RMS-equivalent scalar)
# --------------------------------------------------------------------------
def boundary_factor_B(tw, tau):
    """B = sqrt( tau/(2Tw) * (1 - exp(-2Tw/tau)) ) = I_RMS(t0+Tw)/I0."""
    return math.sqrt(tau / (2.0 * tw) * (-math.expm1(-2.0 * tw / tau)))


def region3_factor_C(tw, tau):
    """C = sqrt( tau/(2Tw) * (exp(2Tw/tau) - 1) )."""
    return math.sqrt(tau / (2.0 * tw) * math.expm1(2.0 * tw / tau))


def g_region2(x, tw, tau):
    """(I_RMS/I0)^2 at elapsed time x = t - t0 in [0, Tw]."""
    return 1.0 - x / tw + tau / (2.0 * tw) * (-math.expm1(-2.0 * x / tau))


def rms_continuous(t, i0, tau, tw, t0):
    x = t - t0
    if x <= 0.0:
        return i0
    if x < tw:
        return i0 * math.sqrt(g_region2(x, tw, tau))
    return i0 * region3_factor_C(tw, tau) * math.exp(-x / tau)


def i0_crit(i_guarded, tw, tau):
    return i_guarded / boundary_factor_B(tw, tau)


def classify_region(i0, i_guarded, tw, tau, rtol=1e-12):
    if i0 <= i_guarded:
        return "NO_CROSSING_I0_NOT_ABOVE_THRESHOLD"
    crit = i0_crit(i_guarded, tw, tau)
    if math.isclose(i0, crit, rel_tol=rtol, abs_tol=0.0):
        return "BOUNDARY_AT_T0_PLUS_TW"
    return "REGION_2" if i0 < crit else "REGION_3"


def solve_region2_root(i0, i_guarded, tw, tau, max_iter=200):
    """
    Solve g(x) = (I_guarded/I0)^2 for x in (0, Tw].
    g is STRICTLY DECREASING on x>0 (g'(x) = (exp(-2x/tau) - 1)/Tw < 0), g(0)=1,
    g(Tw)=B^2.  A root exists in (0, Tw] iff (I_guarded/I0)^2 >= B^2 (Region 2 or
    boundary).  Pure bisection is therefore unconditionally convergent; it halves
    the bracket every iteration (no derivative, no initial guess needed).
    """
    target = (i_guarded / i0) ** 2
    lo, hi = 0.0, tw
    if g_region2(hi, tw, tau) > target * (1.0 + 1e-15):
        raise VerificationFailure("solve_region2_root called outside Region 2/boundary")
    it = 0
    for it in range(1, max_iter + 1):
        mid = 0.5 * (lo + hi)
        if g_region2(mid, tw, tau) > target:
            lo = mid
        else:
            hi = mid
        if hi - lo <= 4.0 * sys.float_info.epsilon * max(1.0, hi):
            break
    x = 0.5 * (lo + hi)
    residual = abs(g_region2(x, tw, tau) - target)
    return x, it, residual


def continuous_crossing(i0, i_guarded, tw, tau, t0):
    region = classify_region(i0, i_guarded, tw, tau)
    out = {"I0_A": i0, "region": region}
    if region.startswith("NO_CROSSING"):
        out.update(t_phys_ms=None, t_rms_ms=None, delta_ms=None)
        return out
    t_phys = t0 + tau * math.log(i0 / i_guarded)
    if region == "REGION_3":
        t_rms = t0 + tau * math.log(i0 * region3_factor_C(tw, tau) / i_guarded)
        out["root_iterations"] = 0
    elif region == "BOUNDARY_AT_T0_PLUS_TW":
        t_rms = t0 + tw
        out["root_iterations"] = 0
    else:
        x, it, res = solve_region2_root(i0, i_guarded, tw, tau)
        t_rms = t0 + x
        out["root_iterations"] = it
        out["root_residual"] = res
    out.update(t_phys_ms=t_phys, t_rms_ms=t_rms, delta_ms=t_rms - t_phys)
    return out


# --------------------------------------------------------------------------
# 2. Discrete reference model of the DOCUMENTED RMS-PROC-V1.0 parameters
# --------------------------------------------------------------------------
def first_valid_frame_index():
    """Smallest k with k*M >= N-1 (full window available, no zero padding)."""
    return -(-(N_WINDOW - 1) // M_STEP)


def sample_envelope(i0, tau, t0, n_samples=N_TRACE):
    """i[n] = I0 for t_n <= t0, I0*exp(-(t_n - t0)/tau) afterwards; t_n = n * 1 us."""
    out = []
    for n in range(n_samples):
        t = n * SAMPLE_PERIOD_MS
        out.append(i0 if t <= t0 else i0 * math.exp(-(t - t0) / tau))
    return out


def rms_frame_normative(i, n):
    """
    NORMATIVE per-frame definition (documented N = 2000, half-open window):
        I_RMS[k] = sqrt( (1/N) * sum_{j=0}^{N-1} i[kM - j]^2 ),  n = kM
    Window = samples n-1999 .. n (2000 samples), timestamps (t_n - 2.0 ms, t_n].
    Sum uses math.fsum (correctly-rounded exact sum of the binary64 squares).
    """
    return math.sqrt(math.fsum(x * x for x in i[n - N_WINDOW + 1:n + 1]) / N_WINDOW)


def grid_frames(i):
    """Yield (k, n, rms) for every VALID frame; frames with kM < N-1 are NOT emitted."""
    k = first_valid_frame_index()
    while k * M_STEP < len(i):
        n = k * M_STEP
        yield k, n, rms_frame_normative(i, n)
        k += 1


def grid_crossing(i, i_guarded):
    """First valid frame with I_RMS[k] < I_guarded (STRICT).  Timestamp = n/FS (right edge)."""
    first = True
    for k, n, r in grid_frames(i):
        if r < i_guarded:
            return {"k": k, "n": n, "t_ms": n * SAMPLE_PERIOD_MS, "rms_A": r,
                    "below_at_first_valid_frame": first}
        first = False
    return None


def prefix_squares(i):
    sq = [x * x for x in i]
    p = [0.0]
    acc = 0.0
    for v in sq:
        acc += v
        p.append(acc)
    return sq, p


def variant_rms_sq(p, sq, n, variant):
    if variant == "A_2000_half_open":          # DOCUMENTED definition
        return (p[n + 1] - p[n + 1 - 2000]) / 2000.0
    if variant == "B_2001_closed_den2001":     # inclusive both ends, N+1 points
        return (p[n + 1] - p[n - 2000]) / 2001.0
    if variant == "C_2001_trapezoid_den2000":  # trapezoid weights on the 2001 points
        return ((p[n + 1] - p[n - 2000]) - 0.5 * (sq[n] + sq[n - 2000])) / 2000.0
    raise ValueError(variant)


def subgrid_crossing(i, i_guarded, variant, p=None, sq=None):
    """First SAMPLE n (not just 0.1 ms frames) with RMS < I_guarded, per window variant."""
    if p is None:
        sq, p = prefix_squares(i)
    start = 1999 if variant.startswith("A_") else 2000
    thr2 = i_guarded * i_guarded
    for n in range(start, len(i)):
        if variant_rms_sq(p, sq, n, variant) < thr2:
            return {"n": n, "t_ms": n * SAMPLE_PERIOD_MS}
    return None


def compare_case(i0, t0, tau=TAU_EFF_MS, ig=I_GUARDED_A, tw=TW_MS):
    cont = continuous_crossing(i0, ig, tw, tau, t0)
    sig = sample_envelope(i0, tau, t0)
    sq, p = prefix_squares(sig)
    grid = grid_crossing(sig, ig)
    subA = subgrid_crossing(sig, ig, "A_2000_half_open", p, sq)
    subB = subgrid_crossing(sig, ig, "B_2001_closed_den2001", p, sq)
    subC = subgrid_crossing(sig, ig, "C_2001_trapezoid_den2000", p, sq)
    res = {"I0_A": i0, "t0_ms": t0, "continuous": cont}
    if cont["t_rms_ms"] is None or grid is None or subA is None:
        res["note"] = "no crossing"
        return res
    tc = cont["t_rms_ms"]
    res["discrete_grid_frame"] = grid
    res["discrete_subgrid_A"] = subA
    res["discrete_subgrid_B"] = subB
    res["discrete_subgrid_C"] = subC
    res["diff_total_grid_minus_continuous_ms"] = grid["t_ms"] - tc
    res["diff_riemann_subgridA_minus_continuous_ms"] = subA["t_ms"] - tc
    res["diff_grid_quantization_ms"] = grid["t_ms"] - subA["t_ms"]
    res["diff_window_variant_B_minus_A_ms"] = subB["t_ms"] - subA["t_ms"]
    res["diff_window_variant_C_minus_A_ms"] = subC["t_ms"] - subA["t_ms"]
    # numerical-precision cross-check: prefix-sum vs fsum at the crossing frame
    k, n = grid["k"], grid["n"]
    pref = math.sqrt(variant_rms_sq(p, sq, n, "A_2000_half_open"))
    res["precision_prefix_vs_fsum_abs_A"] = abs(pref - grid["rms_A"])
    res["precision_margin_to_threshold_A"] = abs(grid["rms_A"] - ig)
    # margin of the immediately preceding frame (must be >= threshold)
    prev = rms_frame_normative(sig, (k - 1) * M_STEP) if k - 1 >= first_valid_frame_index() else None
    res["previous_frame_rms_A"] = prev
    return res


def phase_sweep(i0, tau=TAU_EFF_MS, ig=I_GUARDED_A, tw=TW_MS, steps=20):
    """Slide t0 over one 0.1 ms evaluation step to expose grid-phase dependence."""
    tot, rie = [], []
    for s in range(steps):
        t0 = T0_MS + s * (STEP_MS / steps)
        r = compare_case(i0, t0, tau, ig, tw)
        tot.append(r["diff_total_grid_minus_continuous_ms"])
        rie.append(r["diff_riemann_subgridA_minus_continuous_ms"])
    return {"I0_A": i0, "steps": steps,
            "total_min_ms": min(tot), "total_max_ms": max(tot),
            "riemann_min_ms": min(rie), "riemann_max_ms": max(rie)}


# --------------------------------------------------------------------------
# 3. Verification driver
# --------------------------------------------------------------------------
def _check(cond, msg):
    if not cond:
        raise VerificationFailure(msg)


def run_verification():
    tw, tau, ig = TW_MS, TAU_EFF_MS, I_GUARDED_A
    out = {"status_label": "REFERENCE_MODEL_OF_DOCUMENTED_SPEC_NOT_FROZEN_IMPLEMENTATION"}

    # --- window / timing definition checks -------------------------------
    _check(N_WINDOW == round(tw * FS_HZ / 1000.0), "N != Tw*fs")
    _check(M_STEP == round(STEP_MS * FS_HZ / 1000.0), "M != step*fs")
    kf = first_valid_frame_index()
    out["definition"] = {
        "N_samples": N_WINDOW, "M_samples": M_STEP, "fs_Hz": FS_HZ,
        "first_valid_frame_k": kf, "first_valid_sample_index_n": kf * M_STEP,
        "first_valid_timestamp_ms": kf * M_STEP * SAMPLE_PERIOD_MS,
        "earliest_possible_full_window_sample_n": N_WINDOW - 1,
        "window_at_first_valid_frame_samples": [kf * M_STEP - N_WINDOW + 1, kf * M_STEP],
    }
    _check(kf == 20, "first valid frame must be k=20")

    # --- continuous model self-checks -----------------------------------
    B, C = boundary_factor_B(tw, tau), region3_factor_C(tw, tau)
    out["continuous"] = {"B": B, "C": C,
                         "I0crit_A_at_Iguarded": i0_crit(ig, tw, tau),
                         "delta_flush_region3_ms": tau * math.log(C)}
    t0 = T0_MS
    i0 = 0.8
    _check(math.isclose(rms_continuous(t0 + tw, i0, tau, tw, t0),
                        i0 * B, rel_tol=1e-12), "continuity at t0+Tw (Region 2 side)")
    r3_at_boundary = i0 * C * math.exp(-tw / tau)
    _check(math.isclose(r3_at_boundary, i0 * B, rel_tol=1e-12), "continuity at t0+Tw (Region 3 side)")
    _check(math.isclose(rms_continuous(t0, i0, tau, tw, t0), i0, rel_tol=0.0, abs_tol=1e-15),
           "continuity at t0")

    # --- boundary vectors -------------------------------------------------
    crit = i0_crit(ig, tw, tau)
    bvec = []
    for label, val in (("below_crit_1e-6", crit * (1 - 1e-6)),
                       ("equal_crit", crit),
                       ("above_crit_1e-6", crit * (1 + 1e-6))):
        c = continuous_crossing(val, ig, tw, tau, t0)
        c["label"] = label
        bvec.append(c)
    _check(bvec[0]["region"] == "REGION_2", "below crit must be Region 2")
    _check(bvec[1]["region"] == "BOUNDARY_AT_T0_PLUS_TW", "equal crit must be boundary")
    _check(bvec[2]["region"] == "REGION_3", "above crit must be Region 3")
    for c in bvec:
        _check(abs(c["t_rms_ms"] - (t0 + tw)) < 1e-4, "t_rms must be continuous across boundary")
    out["boundary_vectors"] = bvec

    # --- required analytical examples (continuous) ------------------------
    ex = {}
    for i0v in (0.5, 0.8):
        ex[f"{i0v:.3f}"] = continuous_crossing(i0v, ig, tw, tau, t0)
    _check(ex["0.500"]["region"] == "REGION_2", "0.5 A must be Region 2")
    _check(ex["0.800"]["region"] == "REGION_3", "0.8 A must be Region 3")
    _check(ex["0.500"]["root_residual"] < 1e-13, "Region-2 root residual too large")
    # Region-2 delta must differ from tau*ln(C)
    _check(abs(ex["0.500"]["delta_ms"] - tau * math.log(C)) > 1e-3,
           "Region-2 delta must NOT equal tau*ln(C)")
    _check(math.isclose(ex["0.800"]["delta_ms"], tau * math.log(C), rel_tol=1e-12),
           "Region-3 delta must equal tau*ln(C)")
    out["continuous_examples"] = ex

    # --- continuous vs discrete comparisons --------------------------------
    cases = []
    for i0v in (0.5, 0.55, 0.6, 0.8, 1.0):
        cases.append(compare_case(i0v, T0_MS))
    cases.append(compare_case(crit, T0_MS))
    out["comparisons_on_grid_t0_13p0ms"] = cases
    out["phase_sweeps"] = [phase_sweep(0.5), phase_sweep(0.8)]

    for c in cases:
        _check(c["discrete_grid_frame"]["rms_A"] < ig, "grid crossing frame must be < threshold")
        if c["previous_frame_rms_A"] is not None:
            _check(c["previous_frame_rms_A"] >= ig, "previous frame must be >= threshold")
        _check(0.0 <= c["diff_grid_quantization_ms"] < STEP_MS + 1e-12,
               "grid quantization must lie in [0, 0.1 ms)")
        _check(abs(c["diff_riemann_subgridA_minus_continuous_ms"]) < 0.01,
               "Riemann-sum bias exceeded 10 samples (investigate)")
        _check(c["precision_prefix_vs_fsum_abs_A"] < 1e-9, "prefix-sum precision check failed")

    for s in out["phase_sweeps"]:
        _check(s["total_min_ms"] > -0.01 and s["total_max_ms"] < STEP_MS + 0.01,
               "total grid-vs-continuous difference outside expected envelope")

    out["verification"] = "ALL_INTERNAL_SELF_CONSISTENCY_CHECKS_PASSED"
    out["scope_statement"] = ("Self-consistency of a reference model against closed-form equations. "
                              "Not validation of RMS-PROC-V1.0, hardware, or any physical measurement.")
    return out


def main(argv):
    res = run_verification()
    txt = json.dumps(res, indent=2, sort_keys=True)
    if "--write-json" in argv:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "discrete_rms_verification_results.json")
        with open(path, "w") as f:
            f.write(txt + "\n")
        print(f"wrote {path}")
    else:
        print(txt)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except VerificationFailure as e:
        print(f"[FATAL] {e}")
        sys.exit(1)
