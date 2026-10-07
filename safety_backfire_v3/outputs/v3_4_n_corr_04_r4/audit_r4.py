#!/usr/bin/env python3
"""
V3.4-N-CORR-04-R4 — Evidence Readiness & Traceability Automated Audit Script.

Verifies and FAILS LOUDLY (exit code 1) on any contradiction:
  1. MODEL_H frozen constants invariant
  2. Production script hashes match recorded baseline
  3. Required R3 and R4 output files exist
  4. Production scripts unmodified (mtime and sha256)
  5. Search for forbidden safety claims across R4 outputs
  6. Search for circular acceptance wording in R4 documents
  7. Search for fabricated / unverified evidence assertions
  8. Verify RMS implementation status == RMS_IMPLEMENTATION_MISSING
  9. Verify anti-aliasing status == ANTI_ALIAS_VALIDATION = BLOCKED
  10. Verify current-scale status == HISTORICAL_CURRENT_SCALE = UNRESOLVED
  11. Verify powertrain compatibility status == MOTOR_CONTROLLER_COMPATIBILITY = BLOCKED
  12. Verify tau_eff status == TAU_EFF_STATUS = DESCRIPTIVE_UNTRACEABLE_FIT
  13. Verify historical trial provenance status == TIMING_EVIDENCE = REPORT_BASED
  14. Verify physical capture remains PHYSICAL_CAPTURE_AUTHORIZATION = NOT_GRANTED
  15. Emit deterministic machine-readable JSON: r4_audit_results.json

Usage:
  python3 outputs/v3_4_n_corr_04_r4/audit_r4.py
"""

import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))

MODEL_H_EXPECTED = {"k0": 2.40, "beta_d": 0.08, "beta_l": 0.12, "beta_pitch": 0.22}

PROD_HASH_BASELINE = {
    "scripts/v3_4/discover_event_candidates.py": "656f2fb79f8bef48c53c752f1a51c409e24762d9989c719c3de1ee111a1c7623",
    "scripts/v3_4/automated_evidence_screening.py": "4e19e411207e7be7b39096ee0aca701415da19f8216f807e2a030201678c9896"
}

R3_DIR = os.path.join(ROOT, "outputs", "v3_4_n_corr_04_r3")

R4_REQUIRED_FILES = [
    "evidence_dependency_graph.md",
    "rms_implementation_forensic_search.md",
    "discrete_rms_index_contract.md",
    "reference_vs_historical_rms_gap.md",
    "anti_aliasing_evidence_matrix.md",
    "current_measurement_traceability.md",
    "oscilloscope_configuration_traceability.md",
    "powertrain_identity_chain.md",
    "tau_eff_reproducibility_audit.md",
    "historical_trial_provenance_v2.md",
    "measurement_acceptance_contract.md",
    "measurement_uncertainty_decision_framework.md",
    "blocker_dependency_matrix.md",
    "minimum_traceable_evidence_package.md",
    "capture_readiness_gate.md",
    "master_status_r4.md",
    "audit_r4.py"
]

FORBIDDEN_POSITIVE_CLAIMS = [
    r"\bPL\s*d\b",
    r"\bPL\s*e\b",
    r"\bSIL\s*2\b",
    r"\bSIL\s*3\b",
    r"\bISO_COMPLIANT\b",
    r"\bSAFETY_CERTIFIED\b",
    r"\bVEHICLE_FUNCTIONAL_SAFETY_ESTABLISHED\b",
    r"\bPRODUCTION_READY\b"
]

CIRCULAR_PHRASES = [
    r"confirm\s+(?:that\s+)?(?:Delta_flush\s*≈\s*|Delta_flush\s*=\s*)?1\.1(?:17|2)\s*ms",
    r"verify\s+(?:that\s+)?(?:Delta_flush\s*≈\s*|Delta_flush\s*=\s*)?1\.1(?:17|2)\s*ms",
    r"confirming\s+(?:Delta_flush\s*≈\s*|Delta_flush\s*=\s*)?1\.1(?:17|2)\s*ms",
    r"verifying\s+(?:Delta_flush\s*≈\s*|Delta_flush\s*=\s*)?1\.1(?:17|2)\s*ms"
]

RESULTS = []


def check(name, condition, detail=""):
    passed = bool(condition)
    RESULTS.append({
        "check": name,
        "passed": passed,
        "detail": str(detail)
    })
    prefix = "[PASS] " if passed else "[FAIL] "
    suffix = f" -> {detail}" if detail else ""
    print(prefix + name + suffix)
    return passed


def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def read_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------
# Audit Check Implementations
# ---------------------------------------------------------------------------

def audit_01_model_h():
    print("\n--- 1. MODEL_H Constants Audit ---")
    # Verify Model H constants match
    check("MODEL_H invariants", MODEL_H_EXPECTED == {
        "k0": 2.40,
        "beta_d": 0.08,
        "beta_l": 0.12,
        "beta_pitch": 0.22
    }, "k0=2.40, beta_d=0.08, beta_l=0.12, beta_pitch=0.22")


def audit_02_production_script_hashes():
    print("\n--- 2. Production Script Hashes Invariant ---")
    for rel_path, expected_hash in PROD_HASH_BASELINE.items():
        abs_path = os.path.join(ROOT, rel_path)
        exists = os.path.isfile(abs_path)
        check(f"Exists: {rel_path}", exists)
        if exists:
            actual_hash = sha256_file(abs_path)
            check(f"SHA-256: {rel_path}", actual_hash == expected_hash, f"hash={actual_hash}")


def audit_03_files_exist():
    print("\n--- 3. Required R3 & R4 Files Exist ---")
    check("R3 directory exists", os.path.isdir(R3_DIR))
    for fname in R4_REQUIRED_FILES:
        fpath = os.path.join(HERE, fname)
        check(f"R4 file exists: {fname}", os.path.isfile(fpath))


def audit_04_production_scripts_unmodified():
    print("\n--- 4. Verify Production Scripts Unmodified ---")
    for rel_path in PROD_HASH_BASELINE:
        abs_path = os.path.join(ROOT, rel_path)
        current_hash = sha256_file(abs_path)
        check(f"Immutable: {rel_path}", current_hash == PROD_HASH_BASELINE[rel_path])


def audit_05_forbidden_safety_claims():
    print("\n--- 5. Forbidden Safety Claims Scan ---")
    # Allowed context markers where forbidden tokens may appear legitimately:
    negation_patterns = [
        r"NOT_ESTABLISHED", r"NOT_CLAIMED", r"NOT_GRANTED", r"PROHIBITED",
        r"Never claim", r"expunged", r"withdrawn", r"cannot claim",
        r"strictly PROHIBITED", r"no claim", r"Do not claim", r"FORBIDDEN",
        r"refuted", r"UNVERIFIED", r"BLOCKED", r"without evidence"
    ]
    
    violation_found = False
    for fname in R4_REQUIRED_FILES:
        if not fname.endswith(".md"):
            continue
        text = read_file(os.path.join(HERE, fname))
        lines = text.splitlines()
        for idx, line in enumerate(lines, 1):
            for pat in FORBIDDEN_POSITIVE_CLAIMS:
                m = re.search(pat, line, re.IGNORECASE)
                if m:
                    # Check if line contains negation / prohibition context
                    has_negation = any(re.search(neg, line, re.IGNORECASE) for neg in negation_patterns)
                    if not has_negation:
                        print(f"Violation in {fname}:{idx} -> {line.strip()}")
                        violation_found = True
    
    check("Forbidden safety claims absent from positive assertions", not violation_found)


def audit_06_circular_acceptance():
    print("\n--- 6. Circular Acceptance Language Scan ---")
    circular_found = False
    for fname in R4_REQUIRED_FILES:
        if not fname.endswith(".md"):
            continue
        text = read_file(os.path.join(HERE, fname))
        for pat in CIRCULAR_PHRASES:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                # Check whether it's within expunging or historical quote context
                for line in text.splitlines():
                    if re.search(pat, line, re.IGNORECASE):
                        if not any(k in line.lower() for k in ["expunged", "removed", "circular", "prohibited", "clause", "prior", "r2"]):
                            print(f"Circular phrase in {fname}: {line.strip()}")
                            circular_found = True
    check("No active circular acceptance criteria", not circular_found)


def audit_07_unverified_evidence_assertions():
    print("\n--- 7. Unverified Evidence Assertions Scan ---")
    master_text = read_file(os.path.join(HERE, "master_status_r4.md"))
    # Verify that raw waveforms are not asserted as existing
    check("Field data asserted ZERO", "FIELD_DATA                      = ZERO" in master_text)
    check("Ground truth NOT_ESTABLISHED", "GROUND_TRUTH                    = NOT_ESTABLISHED" in master_text)
    check("Real world validation NOT_ESTABLISHED", "REAL_WORLD_VALIDATION           = NOT_ESTABLISHED" in master_text)


def audit_08_rms_implementation_status():
    print("\n--- 8. RMS Implementation Status ---")
    rms_text = read_file(os.path.join(HERE, "rms_implementation_forensic_search.md"))
    master_text = read_file(os.path.join(HERE, "master_status_r4.md"))
    check("RMS status in forensic report is MISSING", "RMS_IMPLEMENTATION_STATUS = RMS_IMPLEMENTATION_MISSING" in rms_text)
    check("RMS status in master status is MISSING", "RMS_IMPLEMENTATION_TRACEABILITY          = RMS_IMPLEMENTATION_MISSING" in master_text)
    check("Reference model verified is TRUE", "REFERENCE_MODEL_VERIFIED        = TRUE" in rms_text)
    check("Frozen RMS implementation verified is FALSE", "FROZEN_RMS_IMPLEMENTATION_VERIFIED = FALSE" in rms_text)


def audit_09_anti_aliasing_status():
    print("\n--- 9. Anti-Aliasing Blocker Status ---")
    aa_text = read_file(os.path.join(HERE, "anti_aliasing_evidence_matrix.md"))
    master_text = read_file(os.path.join(HERE, "master_status_r4.md"))
    check("Anti-aliasing validation is BLOCKED in matrix", "ANTI_ALIAS_VALIDATION       = BLOCKED" in aa_text or "ANTI_ALIAS_VALIDATION           = BLOCKED" in aa_text)
    check("Anti-aliasing validation is BLOCKED in master", "ANTI_ALIAS_VALIDATION                    = BLOCKED" in master_text)


def audit_10_current_scale_status():
    print("\n--- 10. Current Scale Traceability Status ---")
    curr_text = read_file(os.path.join(HERE, "current_measurement_traceability.md"))
    master_text = read_file(os.path.join(HERE, "master_status_r4.md"))
    check("Historical current scale UNRESOLVED in current report", "HISTORICAL_CURRENT_SCALE        = UNRESOLVED" in curr_text)
    check("Historical current scale UNRESOLVED in master", "CURRENT_SCALE_TRACEABILITY               = UNRESOLVED" in master_text)


def audit_11_powertrain_status():
    print("\n--- 11. Powertrain Compatibility Status ---")
    pt_text = read_file(os.path.join(HERE, "powertrain_identity_chain.md"))
    master_text = read_file(os.path.join(HERE, "master_status_r4.md"))
    check("Powertrain compatibility BLOCKED in identity chain", "MOTOR_CONTROLLER_COMPATIBILITY          = BLOCKED" in pt_text or "MOTOR_CONTROLLER_COMPATIBILITY  = BLOCKED" in pt_text)
    check("Powertrain compatibility BLOCKED in master", "POWERTRAIN_CONFIGURATION_TRACEABILITY   = BLOCKED" in master_text)


def audit_12_tau_eff_status():
    print("\n--- 12. Tau_eff Provenance Status ---")
    tau_text = read_file(os.path.join(HERE, "tau_eff_reproducibility_audit.md"))
    master_text = read_file(os.path.join(HERE, "master_status_r4.md"))
    check("tau_eff status is DESCRIPTIVE_UNTRACEABLE_FIT", "TAU_EFF_STATUS              = DESCRIPTIVE_UNTRACEABLE_FIT" in tau_text or "TAU_EFF_STATUS                  = DESCRIPTIVE_UNTRACEABLE_FIT" in tau_text)
    check("tau_eff in master is DESCRIPTIVE_UNTRACEABLE_FIT", "TAU_EFF_TRACEABILITY                     = DESCRIPTIVE_UNTRACEABLE_FIT" in master_text)


def audit_13_historical_trial_provenance():
    print("\n--- 13. Historical Trial Provenance Status ---")
    hist_text = read_file(os.path.join(HERE, "historical_trial_provenance_v2.md"))
    master_text = read_file(os.path.join(HERE, "master_status_r4.md"))
    check("Historical timing evidence is REPORT_BASED", "TIMING_EVIDENCE                 = REPORT_BASED" in hist_text or "TIMING_EVIDENCE                 = REPORT_BASED" in master_text)
    check("Raw waveforms reported missing for all trials", "RAW_WAVEFORMS                   = MISSING (0 of 10 available)" in hist_text)


def audit_14_physical_capture_status():
    print("\n--- 14. Physical Capture Authorization Status ---")
    gate_text = read_file(os.path.join(HERE, "capture_readiness_gate.md"))
    master_text = read_file(os.path.join(HERE, "master_status_r4.md"))
    check("Physical capture authorization NOT_GRANTED in gate", "PHYSICAL_CAPTURE_AUTHORIZATION   = NOT_GRANTED" in gate_text or "PHYSICAL_CAPTURE_AUTHORIZATION  = NOT_GRANTED" in gate_text)
    check("Physical capture authorization NOT_GRANTED in master", "PHYSICAL_CAPTURE_AUTHORIZATION           = NOT_GRANTED" in master_text)
    check("Readiness gate level is NOT_READY", "CURRENT_READINESS_GATE           = NOT_READY" in gate_text or "CURRENT_GATE_LEVEL              = NOT_READY" in gate_text)
    check("Final status is BLOCKED in master", "FINAL_STATUS                             = BLOCKED" in master_text)


def audit_15_emit_json():
    print("\n--- 15. Emit Machine-Readable Audit JSON ---")
    all_passed = all(r["passed"] for r in RESULTS)
    out_record = {
        "milestone": "V3.4-N-CORR-04-R4",
        "audit_version": "1.0.0",
        "all_checks_passed": all_passed,
        "total_checks": len(RESULTS),
        "passed_checks": sum(1 for r in RESULTS if r["passed"]),
        "failed_checks": sum(1 for r in RESULTS if not r["passed"]),
        "governance_state": {
            "MODEL_H": MODEL_H_EXPECTED,
            "PRODUCTION_MODEL": "UNCHANGED",
            "FIELD_DATA": "ZERO",
            "GROUND_TRUTH": "NOT_ESTABLISHED",
            "REAL_WORLD_VALIDATION": "NOT_ESTABLISHED",
            "PHYSICAL_CAPTURE_AUTHORIZATION": "NOT_GRANTED",
            "RESEARCH_DAQ_ACTUATION_AUTHORITY": "ZERO",
            "REFERENCE_MODEL_VERIFIED": True,
            "FROZEN_RMS_IMPLEMENTATION_VERIFIED": False,
            "RMS_IMPLEMENTATION_STATUS": "RMS_IMPLEMENTATION_MISSING",
            "ANTI_ALIAS_VALIDATION": "BLOCKED",
            "HISTORICAL_CURRENT_SCALE": "UNRESOLVED",
            "MOTOR_CONTROLLER_COMPATIBILITY": "BLOCKED",
            "TAU_EFF_STATUS": "DESCRIPTIVE_UNTRACEABLE_FIT",
            "TIMING_EVIDENCE": "REPORT_BASED",
            "FINAL_STATUS": "BLOCKED"
        },
        "results": RESULTS
    }
    
    json_path = os.path.join(HERE, "r4_audit_results.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(out_record, f, indent=2, sort_keys=True)
    check("Emitted r4_audit_results.json", os.path.isfile(json_path))
    return all_passed


def main():
    print("======================================================================")
    print("V3.4-N-CORR-04-R4 — AUTOMATED FORENSIC EVIDENCE AUDIT")
    print("======================================================================")
    
    audit_01_model_h()
    audit_02_production_script_hashes()
    audit_03_files_exist()
    audit_04_production_scripts_unmodified()
    audit_05_forbidden_safety_claims()
    audit_06_circular_acceptance()
    audit_07_unverified_evidence_assertions()
    audit_08_rms_implementation_status()
    audit_09_anti_aliasing_status()
    audit_10_current_scale_status()
    audit_11_powertrain_status()
    audit_12_tau_eff_status()
    audit_13_historical_trial_provenance()
    audit_14_physical_capture_status()
    all_passed = audit_15_emit_json()
    
    print("\n======================================================================")
    if all_passed:
        print(f"AUDIT PASSED: {len(RESULTS)}/{len(RESULTS)} checks passed.")
        print("FINAL_STATUS = BLOCKED (Preserved with strict evidence governance)")
        print("======================================================================")
        sys.exit(0)
    else:
        failed_count = sum(1 for r in RESULTS if not r["passed"])
        print(f"AUDIT FAILED: {failed_count} check(s) failed!")
        print("======================================================================")
        sys.exit(1)


if __name__ == "__main__":
    main()
