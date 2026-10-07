"""
V3.0.2 Adversarial Validation — Uncertainty-Aware Risk Policy & Monotonicity Audit

Addresses FAIL-22:
Validates that Risk Engine evaluates spatial intervals rather than scalar point distances,
strictly prevents naive worst-case over-alerting, guarantees risk monotonicity,
and resolves Cases A, B, and C as required.
"""
import sys
import math
from pathlib import Path
from typing import Dict, List, Any

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from safety_backfire_v3.core.uncertainty_risk_engine import UncertaintyAwareRiskEngine, RiskEvaluationResult


def test_adversarial_case_a_caution_plausible_danger_no_trajectory():
    """
    Case A:
      Nominal distance = 1.63m, uncertainty = +-0.83m -> interval [0.80m, 2.46m]
      Lower bound <= 1.5m (plausible danger), but NO dangerous trajectory.
      Requirement: Must NOT trigger automatic CONFIRMED_DANGER (prevents over-alerting).
      Expected Decision: HIGH_PRIORITY_CANDIDATE / CAUTION.
    """
    print("\n--- Test Case A: Plausible Danger under Uncertainty without Collision Trajectory ---")
    engine = UncertaintyAwareRiskEngine()
    
    result = engine.evaluate(
        nominal_distance_m=1.63,
        distance_uncertainty_m=0.83,
        evidence_quality=0.75,
        ttc_sec=None,            # No imminent collision
        cpa_miss_m=2.5,          # Safe passing clearance
        relation_state="INDEPENDENT_PEDESTRIAN"
    )
    
    print(f"  Nominal Distance:     {result.nominal_distance_m} m")
    print(f"  Distance Uncertainty: +-{result.distance_uncertainty_m} m")
    print(f"  Plausible Interval:   {result.distance_interval_m} m")
    print(f"  Nominal Risk:         {result.nominal_risk}")
    print(f"  Uncertainty Level:    {result.uncertainty_level}")
    print(f"  Plausible Danger:     {result.plausible_danger}")
    print(f"  Final Risk Decision:  {result.risk_decision}")
    print(f"  Reason:               {result.reason}")

    assert result.plausible_danger is True, "Lower bound (0.80m) must be identified as plausible danger"
    assert result.risk_decision != "CONFIRMED_DANGER", "Case A must NOT be blindly promoted to CONFIRMED_DANGER"
    assert result.risk_decision in ["HIGH_PRIORITY_CANDIDATE", "CAUTION"], f"Unexpected decision {result.risk_decision}"
    print("  [PASS] Case A: Plausible danger under uncertainty elevated to candidate review without false confirmation.")
    return result


def test_adversarial_case_b_same_uncertainty_with_dangerous_trajectory():
    """
    Case B:
      Same geometry uncertainty (1.63m +-0.83m)
      PLUS strong dangerous trajectory: low TTC (1.2s) and low CPA miss distance (0.4m).
      Requirement: Plausible danger combined with collision kinematics MUST escalate.
      Expected Decision: CONFIRMED_DANGER.
    """
    print("\n--- Test Case B: Same Uncertainty + Converging Trajectory Escalate to Confirmed Danger ---")
    engine = UncertaintyAwareRiskEngine()
    
    result = engine.evaluate(
        nominal_distance_m=1.63,
        distance_uncertainty_m=0.83,
        evidence_quality=0.85,
        ttc_sec=1.2,             # Imminent collision (< 2.5s)
        cpa_miss_m=0.40,         # Direct impact line (< 1.8m)
        relation_state="INDEPENDENT_PEDESTRIAN",
        approach_speed_m_s=1.5
    )
    
    print(f"  Nominal Distance:     {result.nominal_distance_m} m")
    print(f"  Distance Uncertainty: +-{result.distance_uncertainty_m} m")
    print(f"  TTC:                  {result.evidence_telemetry['ttc_sec']} s")
    print(f"  CPA Miss Distance:    {result.evidence_telemetry['cpa_miss_m']} m")
    print(f"  Final Risk Decision:  {result.risk_decision}")
    print(f"  Risk Score:           {result.risk_score}")

    assert result.risk_decision == "CONFIRMED_DANGER", "Case B with dangerous trajectory must escalate to CONFIRMED_DANGER"
    print("  [PASS] Case B: Converging trajectory correctly escalates plausible danger to CONFIRMED_DANGER.")
    return result


def test_adversarial_case_c_nominal_safe_huge_uncertainty_weak_evidence():
    """
    Case C:
      Nominal safe distance (3.5m)
      HUGE uncertainty (+-1.5m -> interval [2.0m, 5.0m])
      Weak evidence quality (0.35).
      Requirement: System must NOT declare SAFE when sensory data is severely degraded.
      Expected Decision: INSUFFICIENT_EVIDENCE.
    """
    print("\n--- Test Case C: Nominal Safe Distance Masked by Severe Spatial Uncertainty ---")
    engine = UncertaintyAwareRiskEngine()
    
    result = engine.evaluate(
        nominal_distance_m=3.5,
        distance_uncertainty_m=1.5,
        evidence_quality=0.35,   # Severely degraded foot visibility
        ttc_sec=None,
        cpa_miss_m=None,
        relation_state="INDEPENDENT_PEDESTRIAN"
    )
    
    print(f"  Nominal Distance:     {result.nominal_distance_m} m")
    print(f"  Distance Uncertainty: +-{result.distance_uncertainty_m} m")
    print(f"  Evidence Quality:     {result.evidence_telemetry['evidence_quality']}")
    print(f"  Nominal Risk:         {result.nominal_risk}")
    print(f"  Final Risk Decision:  {result.risk_decision}")

    assert result.risk_decision != "SAFE", "Degraded observation must NEVER be blindly declared SAFE"
    assert result.risk_decision == "INSUFFICIENT_EVIDENCE", f"Expected INSUFFICIENT_EVIDENCE, got {result.risk_decision}"
    print("  [PASS] Case C: Severe spatial uncertainty correctly flags INSUFFICIENT_EVIDENCE.")
    return result


def test_risk_monotonicity_under_distance_and_variance():
    """
    Monotonicity Audit:
    1. Distance Monotonicity: As distance decreases at fixed uncertainty, risk score must NEVER decrease.
    2. Variance Monotonicity: Increasing uncertainty must elevate risk score monotonically without erratic state jumps.
    """
    print("\n--- Test Monotonicity: Distance and Variance Sweeps ---")
    engine = UncertaintyAwareRiskEngine()
    
    # 1. Distance Monotonicity Sweep (from 5.0m down to 0.5m)
    print("  Subtest 1: Distance Monotonicity (Uncertainty = 0.25m):")
    distances = [5.0, 4.0, 3.0, 2.5, 2.0, 1.63, 1.2, 0.8, 0.5]
    prev_score = -1.0
    for d in distances:
        res = engine.evaluate(nominal_distance_m=d, distance_uncertainty_m=0.25, evidence_quality=0.8)
        print(f"    d = {d:4.2f}m -> score = {res.risk_score:5.3f} | decision = {res.risk_decision:<22}")
        assert res.risk_score >= prev_score, f"Monotonicity violated: dist {d} score {res.risk_score} < prev {prev_score}"
        prev_score = res.risk_score
    print("  [PASS] Distance Monotonicity strictly preserved.")

    # 2. Variance Monotonicity Sweep (from 0.10m to 1.50m at fixed d = 2.0m)
    print("  Subtest 2: Variance Monotonicity (Nominal Distance = 2.0m):")
    uncertainties = [0.10, 0.20, 0.35, 0.50, 0.75, 1.00, 1.50]
    prev_unc_score = -1.0
    for u in uncertainties:
        res = engine.evaluate(nominal_distance_m=2.0, distance_uncertainty_m=u, evidence_quality=0.8)
        print(f"    unc = {u:4.2f}m -> score = {res.risk_score:5.3f} | decision = {res.risk_decision:<22} | unc_level = {res.uncertainty_level}")
        assert res.risk_score >= prev_unc_score, f"Variance Monotonicity violated: unc {u} score {res.risk_score} < prev {prev_unc_score}"
        # Ensure it does NOT randomly flap into CONFIRMED_DANGER without trajectory
        assert res.risk_decision != "CONFIRMED_DANGER", "High uncertainty alone must not trigger CONFIRMED_DANGER"
        prev_unc_score = res.risk_score
    print("  [PASS] Variance Monotonicity strictly preserved without erratic state flapping.")


def run_all_uncertainty_risk_tests():
    print("=================================================================")
    print("   V3.0.2 RED-TEAM: UNCERTAINTY-AWARE RISK & MONOTONICITY AUDIT  ")
    print("=================================================================")
    test_adversarial_case_a_caution_plausible_danger_no_trajectory()
    test_adversarial_case_b_same_uncertainty_with_dangerous_trajectory()
    test_adversarial_case_c_nominal_safe_huge_uncertainty_weak_evidence()
    test_risk_monotonicity_under_distance_and_variance()
    print("\nALL UNCERTAINTY RISK ADVERSARIAL TESTS COMPLETED!")

if __name__ == "__main__":
    run_all_uncertainty_risk_tests()
