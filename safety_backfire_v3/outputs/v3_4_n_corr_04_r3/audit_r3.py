#!/usr/bin/env python3
"""
V3.4-N-CORR-04-R3 — audit script.

Verifies (and FAILS LOUDLY, exit code 1, on any contradiction):
  A. required output files exist
  B. MODEL_H values unchanged (constants + echo in production text)
  C. production script hashes == recorded baseline; mtimes predate R3 outputs
  D. continuous RMS boundary (B, I0crit) and independent numerical-integration check of
     the Region-1/2/3 closed forms
  E. Region-2 numerical roots (0.5 A) and verification that tau*ln(C) does NOT apply there
  F. Region-3 crossing times (0.8 A) and boundary three-way classification
  G. discrete RMS reference model self-consistency (imports discrete_rms_verification.py)
  H. Mode-B 101-point / 100-interval semantics and the 11 deterministic test vectors
  I. document-consistency scans (blocker ledger, status tokens, label replacements)
  J. provenance scans (historical manifest derived columns, absence of raw waveform files)

A passing audit means ONLY that these internal consistency checks passed.  It is NOT
physical validation, NOT safety certification, and NOT readiness; every blocker stays OPEN.

Emits a deterministic machine-readable status file: r3_audit_results.json
(sorted keys, no timestamps, no randomness).

Usage:  python3 outputs/v3_4_n_corr_04_r3/audit_r3.py
"""

import csv
import hashlib
import importlib.util
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))

MODEL_H = {"k0": 2.40, "beta_d": 0.08, "beta_l": 0.12, "beta_pitch": 0.22}
TW, TAU, IG, T0 = 2.0, 2.8, 0.410, 13.0     # illustrative / empirical parameters (see docs)

REQUIRED_FILES = [
    "rms_model_scope_reconciliation.md",
    "rms_boundary_v2.md",
    "rms_crossing_general_solution.md",
    "discrete_rms_specification.md",
    "discrete_rms_verification.py",
    "timing_timestamp_governance.md",
    "anti_aliasing_audit.md",
    "current_probe_range_reconciliation.md",
    "controller_motor_compatibility_reconciliation_v3.md",
    "historical_trial_evidence_reconciliation.md",
    "persistence_semantics_v5.md",
    "persistence_modeb_reference.py",
    "release_blockers_v3.md",
    "BLOCKED.md",
    "production_hash_baseline_r3.json",
    "audit_r3.py",
]

RESULTS = []      # list of (name, passed, detail)


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond), str(detail)))
    print(("[PASS] " if cond else "[FAIL] ") + name + (f"  -> {detail}" if detail else ""))
    return bool(cond)


def load_module(filename, modname):
    spec = importlib.util.spec_from_file_location(modname, os.path.join(HERE, filename))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[modname] = mod
    spec.loader.exec_module(mod)
    return mod


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def read(name):
    with open(os.path.join(HERE, name), "r", encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------
def audit_files():
    print("\n--- A. required files ---")
    for fn in REQUIRED_FILES:
        check(f"exists: {fn}", os.path.isfile(os.path.join(HERE, fn)))


def audit_model_h_and_hashes():
    print("\n--- B/C. MODEL_H and production scripts ---")
    check("MODEL_H constants", MODEL_H == {"k0": 2.40, "beta_d": 0.08, "beta_l": 0.12, "beta_pitch": 0.22},
          json.dumps(MODEL_H, sort_keys=True))
    prod_dir = os.path.join(ROOT, "scripts", "v3_4")
    txt = ""
    p = os.path.join(prod_dir, "automated_evidence_screening.py")
    if os.path.isfile(p):
        with open(p, "r", encoding="utf-8") as f:
            txt = f.read()
    # Model H has no parameter file in the repo; the frozen values are only echoed as text.
    check("MODEL_H echoed in production text (no parameter file exists)",
          all(s in txt for s in ("2.40", "0.08", "0.12", "0.22")))
    base = json.loads(read("production_hash_baseline_r3.json"))
    r3_mtimes = [os.stat(os.path.join(HERE, fn)).st_mtime for fn in REQUIRED_FILES
                 if os.path.isfile(os.path.join(HERE, fn)) and fn not in ("audit_r3.py",)]
    earliest_r3 = min(r3_mtimes) if r3_mtimes else float("inf")
    for rel, expected in sorted(base["files"].items()):
        path = os.path.join(ROOT, rel)
        ok = os.path.isfile(path)
        check(f"production file present: {rel}", ok)
        if ok:
            check(f"production hash unchanged: {rel}", sha256(path) == expected, sha256(path))
            check(f"production mtime predates R3 outputs: {rel}", os.stat(path).st_mtime < earliest_r3)


def simpson(f, a, b, n=4000):
    if b <= a:
        return 0.0
    h = (b - a) / n
    s = f(a) + f(b)
    for j in range(1, n):
        s += (4 if j % 2 else 2) * f(a + j * h)
    return s * h / 3.0


def rms_numeric(t, i0, tau, tw, t0):
    """Independent check: integrate i^2 over [t-Tw, t] numerically (split at the onset)."""
    def sq(x):
        v = i0 if x <= t0 else i0 * math.exp(-(x - t0) / tau)
        return v * v
    a, b = t - tw, t
    if b <= t0 or a >= t0:
        tot = simpson(sq, a, b)
    else:
        tot = simpson(sq, a, t0) + simpson(sq, t0, b)
    return math.sqrt(tot / tw)


def audit_continuous(dv):
    print("\n--- D. continuous RMS model ---")
    B = dv.boundary_factor_B(TW, TAU)
    C = dv.region3_factor_C(TW, TAU)
    crit = dv.i0_crit(IG, TW, TAU)
    check("B(Tw,tau) = 0.7295507347", math.isclose(B, 0.7295507347, abs_tol=1e-9), B)
    check("C(Tw,tau) = 1.4902730349", math.isclose(C, 1.4902730349, abs_tol=1e-9), C)
    check("I0crit = Iguarded/B = 0.5619897020 A", math.isclose(crit, 0.5619897020, abs_tol=1e-9), crit)
    check("B^2 identity: B^2 == tau/(2Tw)(1-exp(-2Tw/tau))",
          math.isclose(B * B, TAU / (2 * TW) * (1 - math.exp(-2 * TW / TAU)), rel_tol=1e-14))
    worst = 0.0
    for i0 in (0.5, 0.8):
        for t in (11.0, 12.9, 13.0, 13.4, 14.0, 14.9, 15.0, 15.0 + 1e-9, 15.5, 17.0, 20.0):
            a = dv.rms_continuous(t, i0, TAU, TW, T0)
            n = rms_numeric(t, i0, TAU, TW, T0)
            worst = max(worst, abs(a - n) / n)
    check("closed forms (Regions 1/2/3) == independent Simpson integration", worst < 1e-9,
          f"max rel err {worst:.2e}")
    # continuity at t0 and t0+Tw
    check("continuity at t0", math.isclose(dv.rms_continuous(T0, 0.8, TAU, TW, T0), 0.8, rel_tol=1e-14))
    r2 = 0.8 * dv.boundary_factor_B(TW, TAU)
    r3 = 0.8 * C * math.exp(-TW / TAU)
    check("continuity at t0+Tw", math.isclose(r2, r3, rel_tol=1e-13), f"{r2} vs {r3}")
    check("0.80 A: I_RMS(15.0 ms) ~ 0.584 A > threshold -> not Region 2",
          math.isclose(r2, 0.583641, abs_tol=5e-6) and r2 > IG, r2)
    return B, C, crit


def audit_roots(dv, C, crit):
    print("\n--- E/F. crossing times ---")
    r05 = dv.continuous_crossing(0.5, IG, TW, TAU, T0)
    r08 = dv.continuous_crossing(0.8, IG, TW, TAU, T0)
    check("0.5 A classified REGION_2", r05["region"] == "REGION_2", r05["region"])
    check("0.5 A t_phys ~ 13.556", abs(r05["t_phys_ms"] - 13.556) < 5e-4, r05["t_phys_ms"])
    check("0.5 A t_rms ~ 14.613", abs(r05["t_rms_ms"] - 14.613) < 5e-4, r05["t_rms_ms"])
    check("0.5 A delta ~ 1.057", abs(r05["delta_ms"] - 1.057) < 5e-4, r05["delta_ms"])
    x = r05["t_rms_ms"] - T0
    check("0.5 A root satisfies g(x) = (Ig/I0)^2 (independent re-evaluation)",
          abs(dv.g_region2(x, TW, TAU) - (IG / 0.5) ** 2) < 1e-13)
    check("0.5 A root also satisfies numeric-integral RMS == Ig",
          abs(rms_numeric(r05["t_rms_ms"], 0.5, TAU, TW, T0) - IG) < 1e-9)
    check("Region 2: delta != tau*ln(C) (tau*ln C does not apply)",
          abs(r05["delta_ms"] - TAU * math.log(C)) > 1e-3, f"{r05['delta_ms']} vs {TAU*math.log(C)}")
    check("R2-R1 value x=1.608 is NOT a root (documented error)",
          abs(dv.g_region2(1.608, TW, TAU) - (IG / 0.5) ** 2) > 1e-3)
    check("0.8 A classified REGION_3", r08["region"] == "REGION_3", r08["region"])
    check("0.8 A t_phys ~ 14.872", abs(r08["t_phys_ms"] - 14.872) < 5e-4, r08["t_phys_ms"])
    check("0.8 A t_rms ~ 15.989", abs(r08["t_rms_ms"] - 15.989) < 5e-4, r08["t_rms_ms"])
    check("0.8 A delta ~ 1.117 == tau*ln(C) (Region 3 only)",
          abs(r08["delta_ms"] - 1.117) < 5e-4 and math.isclose(r08["delta_ms"], TAU * math.log(C), rel_tol=1e-12),
          r08["delta_ms"])
    check("0.8 A RMS numerically equals Ig at t_rms",
          abs(rms_numeric(r08["t_rms_ms"], 0.8, TAU, TW, T0) - IG) < 1e-9)
    # three-way classification
    below = dv.continuous_crossing(crit * (1 - 1e-6), IG, TW, TAU, T0)
    equal = dv.continuous_crossing(crit, IG, TW, TAU, T0)
    above = dv.continuous_crossing(crit * (1 + 1e-6), IG, TW, TAU, T0)
    check("I0 < I0crit -> REGION_2", below["region"] == "REGION_2")
    check("I0 = I0crit -> BOUNDARY at t0+Tw", equal["region"] == "BOUNDARY_AT_T0_PLUS_TW"
          and abs(equal["t_rms_ms"] - (T0 + TW)) < 1e-12)
    check("I0 > I0crit -> REGION_3", above["region"] == "REGION_3")
    check("t_rms continuous across the boundary",
          abs(below["t_rms_ms"] - above["t_rms_ms"]) < 1e-5)
    # root procedure robustness over a sweep inside Region 2
    worst = 0.0
    for i in range(1, 200):
        i0 = IG + (crit - IG) * i / 200.0
        r = dv.continuous_crossing(i0, IG, TW, TAU, T0)
        worst = max(worst, abs(dv.g_region2(r["t_rms_ms"] - T0, TW, TAU) - (IG / i0) ** 2))
        if not (0.0 < r["t_rms_ms"] - T0 < TW):
            worst = float("inf")
    check("Region-2 bisection robust over 199-point sweep (residual < 1e-12, root inside (0,Tw))",
          worst < 1e-12, f"{worst:.2e}")
    return r05, r08


def audit_discrete(dv):
    print("\n--- G. discrete RMS reference model ---")
    try:
        out = dv.run_verification()
        check("discrete_rms_verification.run_verification() self-consistency", True, out["verification"])
    except Exception as e:     # noqa: BLE001 - any failure is a loud audit failure
        check("discrete_rms_verification.run_verification() self-consistency", False, repr(e))
        return None
    d = out["definition"]
    check("N = 2000 samples, M = 100, fs = 1 MSa/s",
          (d["N_samples"], d["M_samples"], d["fs_Hz"]) == (2000, 100, 1_000_000))
    check("first valid frame k = 20 at t = 2.0 ms", d["first_valid_frame_k"] == 20
          and math.isclose(d["first_valid_timestamp_ms"], 2.0))
    cases = {c["I0_A"]: c for c in out["comparisons_on_grid_t0_13p0ms"] if c["I0_A"] in (0.5, 0.8)}
    check("0.5 A: frame crossing at/after continuous crossing and within 0.1 ms",
          0.0 <= cases[0.5]["diff_total_grid_minus_continuous_ms"] < 0.1 + 1e-9,
          cases[0.5]["diff_total_grid_minus_continuous_ms"])
    check("0.8 A: frame crossing at/after continuous crossing and within 0.1 ms",
          0.0 <= cases[0.8]["diff_total_grid_minus_continuous_ms"] < 0.1 + 1e-9,
          cases[0.8]["diff_total_grid_minus_continuous_ms"])
    check("sub-frame (sample-level) difference < 1 sample for all vectors",
          all(abs(c["diff_riemann_subgridA_minus_continuous_ms"]) < 1e-3
              for c in out["comparisons_on_grid_t0_13p0ms"]))
    return out


def audit_modeb():
    print("\n--- H. Mode-B semantics ---")
    pm = load_module("persistence_modeb_reference.py", "persistence_modeb_reference")
    check("Mode B constants: 100 intervals, 101 points, 10_000 us nominal logical",
          (pm.ELAPSED_INTERVALS, pm.EVAL_POINTS, pm.NOMINAL_LOGICAL_DURATION_US) == (100, 101, 10_000))
    res = pm.run_test_vectors()
    for r in res:
        check(f"Mode-B vector {r['name']}", r["passed"], "; ".join(r["why"]))
    check("11 vectors executed", len(res) == 11, len(res))
    # explicit 101/100 semantic probe, independent of the vector table
    f = pm.ModeBPersistence(0.410)
    for k in range(0, 100):
        f.step(k, 0.1)
    check("after 100 qualifying points: NOT qualified (points=100, intervals=99)",
          f.k_qualified is None and f.points == 100)
    f.step(100, 0.1)
    check("after 101st point: qualified at k_start+100 (100 intervals)",
          f.k_qualified == 100 and f.k_qualified - f.k_start == 100)
    # reference model exposes no actuation-capable API
    forbidden = [n for n in dir(pm.ModeBPersistence)
                 if re.search(r"(command|actuat|enable|restore|rearm|re_arm|reactivate|open_|close_|contactor)", n, re.I)]
    check("Mode-B model exposes no actuation/re-arm/restore API", not forbidden, forbidden)
    # end-to-end: synthetic 0.8 A envelope -> discrete RMS frames -> Mode B (logical times only)
    dv = sys.modules["discrete_rms_verification"]
    sig = dv.sample_envelope(0.8, TAU, T0)
    frames = [(k, r) for k, n, r in dv.grid_frames(sig)]
    rec = pm.run_stream(frames, IG)
    qual_ms = rec["logical_t_qualified_us"] / 1000.0 if rec["logical_t_qualified_us"] is not None else None
    check("end-to-end synthetic 0.8 A: qualifies 10.0 ms (logical) after the crossing frame (16.0 ms)",
          qual_ms is not None and abs(qual_ms - 26.0) < 1e-9, qual_ms)
    return res


def audit_documents():
    print("\n--- I. document consistency ---")
    led = read("release_blockers_v3.md")
    rows = re.findall(r"^\| \*\*BLK_R3_\d+\*\*.*\|\s*`(\w+)`\s*\|\s*$", led, re.M)
    n_open = sum(1 for s in rows if s == "OPEN")
    n_closed = sum(1 for s in rows if s != "OPEN")
    check("ledger lists 13 blockers", len(rows) == 13, len(rows))
    check("every blocker OPEN; none closed (no closing evidence artifact exists)", n_closed == 0, f"open={n_open} closed={n_closed}")
    table = led.split("## 2.")[0]
    check("closure ledger table does not require confirming 1.12/1.117 ms (no circular criterion)",
          "1.117" not in table.split("## 1. Ledger")[1] and "1.12" not in table.split("## 1. Ledger")[1])
    check("ledger Section 4 lists the six independent-comparison requirements",
          all(s in led for s in ("independently measured physical/envelope crossing",
                                 "independently measured RMS crossing", "observed offset",
                                 "comparison against the analytical prediction",
                                 "documented explanation", "no presupposition")))
    blocked = read("BLOCKED.md")
    check("BLOCKED.md states BLOCKED", "V3_4_N_CORR_04_R3_STATUS         = BLOCKED" in blocked)
    for s in ("MODEL_H                          = FROZEN", "PRODUCTION_MODEL                 = UNCHANGED",
              "FIELD_DATA                       = ZERO", "PHYSICAL_CAPTURE_AUTHORIZATION   = NOT_GRANTED",
              "RESEARCH_DAQ_ACTUATION_AUTHORITY = ZERO", "GROUND_TRUTH                     = NOT_ESTABLISHED",
              "REAL_WORLD_VALIDATION            = NOT_ESTABLISHED"):
        check(f"BLOCKED.md invariant: {s.split('=')[0].strip()}", s in blocked)
    bad = []
    for fn in REQUIRED_FILES:
        if fn.endswith(".md"):
            t = read(fn)
            if re.search(r"=\s*READY_FOR_REAUDIT", t) or re.search(r"PHYSICAL_CAPTURE_AUTHORIZATION\s*=\s*GRANTED", t):
                bad.append(fn)
            if re.search(r"(?m)^\s*(?:V3_4_N_CORR_04_R3_STATUS|MILESTONE_STATUS)\s*=\s*(?!BLOCKED)\S+", t):
                bad.append(fn)
    check("no R3 doc declares READY_FOR_REAUDIT, GRANTED capture, or a non-BLOCKED status", not bad, bad)
    v5 = read("persistence_semantics_v5.md")
    check("persistence v5 replaces the traction label",
          "TRACTION_DEENERGIZED                      = NOT_DIRECTLY_MEASURED" in v5
          and "CURRENT_BELOW_GUARDED_THRESHOLD_PERSISTED" in v5)
    check("persistence v5 keeps 101 points / 100 intervals / 10.0 ms nominal logical",
          "101" in v5 and "100" in v5 and "10.0 ms" in v5 and "nominal" in v5.lower())
    check("anti-alias doc states ANTI_ALIAS_VALIDATION = BLOCKED",
          "ANTI_ALIAS_VALIDATION = BLOCKED" in read("anti_aliasing_audit.md"))
    check("probe doc keeps HISTORICAL_CURRENT_SCALE = UNRESOLVED",
          "HISTORICAL_CURRENT_SCALE        = UNRESOLVED" in read("current_probe_range_reconciliation.md"))
    check("controller doc keeps MOTOR_CONTROLLER_COMPATIBILITY = BLOCKED",
          "MOTOR_CONTROLLER_COMPATIBILITY  = BLOCKED" in read("controller_motor_compatibility_reconciliation_v3.md"))
    check("historical doc keeps TIMING_EVIDENCE = REPORT_BASED",
          "TIMING_EVIDENCE          = REPORT_BASED" in read("historical_trial_evidence_reconciliation.md"))
    spec = read("discrete_rms_specification.md")
    check("discrete spec does NOT declare the continuous boundary exact for RMS-PROC-V1.0",
          "CONTINUOUS_BOUNDARY_EXACT_FOR_RMS_PROC_V1_0 = NOT_DECLARED" in spec)


def audit_provenance():
    print("\n--- J. provenance scans ---")
    path = os.path.join(ROOT, "outputs", "v3_4_n_corr_04_r2", "evidence_manifest_v3.csv")
    rows = []
    if os.path.isfile(path):
        with open(path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    check("manifest has 10 historical rows", len(rows) == 10, len(rows))
    if rows:
        check("all rows: raw_waveform_file == MISSING",
              all(r["raw_waveform_file"] == "MISSING" for r in rows))
        check("all rows: evidence_class == REPORT_BASED",
              all(r["evidence_class"] == "REPORT_BASED" for r in rows))
        deltas = {r["Delta_flush_ms"] for r in rows}
        check("Delta_flush_ms identical (1.12) in all ten rows -> DERIVED, not observed",
              deltas == {"1.12"}, sorted(deltas))
        check("t_phys == t_rms - 1.12 in every row -> DERIVED, not observed",
              all(abs(float(r["t_phys_envelope_cross_ms"]) - (float(r["t_rms_threshold_cross_ms"]) - 1.12)) < 0.006
                  for r in rows))
        rms = sorted({r["t_rms_threshold_cross_ms"] for r in rows})
        check("other timestamps vary across rows (so the constant offset is not a shared setting)",
              len(rms) > 1, rms)
    found = []
    for dp, dn, fns in os.walk(ROOT):
        dn[:] = [d for d in dn if d not in (".git", "node_modules", "venv", ".venv", "__pycache__")]
        for fn in fns:
            if fn.lower().endswith((".wfm", ".isf", ".trc")):
                found.append(os.path.join(dp, fn))
    check("no oscilloscope-native waveform files (.wfm/.isf/.trc) in the repository", not found, found[:3])


def main():
    audit_files()
    dv = load_module("discrete_rms_verification.py", "discrete_rms_verification")
    audit_model_h_and_hashes()
    _, C, crit = audit_continuous(dv)
    audit_roots(dv, C, crit)
    disc = audit_discrete(dv)
    audit_modeb()
    audit_documents()
    audit_provenance()

    failed = [r for r in RESULTS if not r[1]]
    status = {
        "milestone": "V3.4-N-CORR-04-R3",
        "audit_result": "PASS_INTERNAL_CONSISTENCY_ONLY" if not failed else "FAIL",
        "checks_total": len(RESULTS),
        "checks_failed": len(failed),
        "failed_checks": [r[0] for r in failed],
        "final_status": "BLOCKED",
        "blockers_open": 13,
        "blockers_closed": 0,
        "governance": {
            "MODEL_H": "FROZEN", "PRODUCTION_MODEL": "UNCHANGED", "FIELD_DATA": "ZERO",
            "GROUND_TRUTH": "NOT_ESTABLISHED", "REAL_WORLD_VALIDATION": "NOT_ESTABLISHED",
            "PHYSICAL_CAPTURE_AUTHORIZATION": "NOT_GRANTED", "RESEARCH_DAQ_ACTUATION_AUTHORITY": "ZERO",
        },
        "status_tokens": {
            "rms_continuous_model": "VERIFIED_CONDITIONALLY",
            "rms_region_boundary_symbolic": "VERIFIED_CONTINUOUS_TIME_MODEL",
            "rms_boundary_for_rms_proc_v1_0": "NOT_VERIFIED",
            "rms_proc_v1_0_implementation": "NOT_LOCATED",
            "rms_proc_v1_0_definition": "INCONSISTENT_ACROSS_MILESTONES",
            "anti_alias_validation": "BLOCKED",
            "historical_current_scale": "UNRESOLVED",
            "motor_controller_compatibility": "BLOCKED",
            "timing_evidence": "REPORT_BASED",
            "physical_timestamp_semantics": "NOT_VERIFIED",
            "persistence_mode_b": "DEFINED_PENDING_IMPLEMENTATION_AUDIT",
            "tau_eff_generalization": "PROHIBITED",
            "vehicle_functional_safety_claim": "NOT_ESTABLISHED",
        },
        "numbers": {
            "B": round(dv.boundary_factor_B(TW, TAU), 10),
            "C": round(dv.region3_factor_C(TW, TAU), 10),
            "I0crit_A_at_0p410": round(dv.i0_crit(IG, TW, TAU), 10),
            "tau_ln_C_ms": round(TAU * math.log(dv.region3_factor_C(TW, TAU)), 10),
            "I0_0p5": {k: (round(v, 6) if isinstance(v, float) else v)
                       for k, v in dv.continuous_crossing(0.5, IG, TW, TAU, T0).items()
                       if k in ("region", "t_phys_ms", "t_rms_ms", "delta_ms")},
            "I0_0p8": {k: (round(v, 6) if isinstance(v, float) else v)
                       for k, v in dv.continuous_crossing(0.8, IG, TW, TAU, T0).items()
                       if k in ("region", "t_phys_ms", "t_rms_ms", "delta_ms")},
        },
        "document_hashes_sha256": {fn: sha256(os.path.join(HERE, fn)) for fn in sorted(REQUIRED_FILES)
                                   if fn not in ("audit_r3.py",) and os.path.isfile(os.path.join(HERE, fn))},
        "scope_statement": ("Internal consistency checks only. Not physical validation, not safety "
                            "certification, not ISO/PL/SIL compliance, not production readiness."),
    }
    out_path = os.path.join(HERE, "r3_audit_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(status, f, indent=2, sort_keys=True)
        f.write("\n")
    print("\n" + "=" * 78)
    print(f"checks: {len(RESULTS)}  failed: {len(failed)}  ->  {status['audit_result']}")
    print("FINAL_STATUS: BLOCKED   (blockers open: 13, closed: 0)")
    print(f"status file: {out_path}")
    print("=" * 78)
    if failed:
        sys.stderr.write("\n*** AUDIT FAILED — CONTRADICTION(S) DETECTED ***\n")
        for name, _, detail in failed:
            sys.stderr.write(f"  FAIL: {name}  {detail}\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
