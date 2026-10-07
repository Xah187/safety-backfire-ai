"""
V3.0.3 Validation Integrity: Risk Semantic Separation & Monotonicity Suite

Verifies:
1. Semantic Hazard Separation:
   - CURRENT_PROXIMITY_HAZARD (spatial breach of clearance zone)
   - PREDICTIVE_COLLISION_HAZARD (kinetic trajectory convergence / low TTC)
   - MEASUREMENT_UNCERTAINTY (sensor/calibration variance level)
2. Stationary Proximity Hazard Test:
   - Person stationary, Forklift stationary, Distance = 0.9m, Evidence = 0.85, TTC = unavailable.
   - Proves that Proximity Hazard exists independently of TTC convergence.
   - Evaluates under defined operational clearance policy (CRITICAL_VIOLATION <= 1.0m).
3. Inverse Collision Threat Test:
   - Safe current distance (3.5m) + Converging collision trajectory (TTC=1.2s, CPA=0.4m).
   - Proves Predictive Collision Hazard triggers without current proximity breach.
4. Non-Decreasing / Non-Increasing Monotonicity Proof:
   - Continuous score monotonicity under distance and uncertainty sweeps.
   - Discrete decision monotonicity across safety states.
"""
import sys
import math
import json
import os
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from safety_backfire_v3.core.uncertainty_risk_engine import (
    UncertaintyAwareRiskEngine,
    RiskEvaluationResult
)

def run_safety_semantic_separation_suite():
    print("=" * 70)
    print("   V3.0.3 VALIDATION INTEGRITY: RISK SEMANTICS & MONOTONICITY   ")
    print("=" * 70)
    
    engine = UncertaintyAwareRiskEngine(
        danger_distance_m=1.5,
        caution_distance_m=3.0,
        critical_ttc_sec=2.5,
        cleared_cpa_miss_m=1.8,
        critical_clearance_zone_m=1.0,
        warning_clearance_zone_m=1.8
    )
    
    # Subtest 1: Stationary Pair at 0.9m (No TTC)
    print("\n--- Subtest 1: Mandatory Stationary Pair Hazard Test (0.9m Separation) ---")
    res_stationary = engine.evaluate(
        nominal_distance_m=0.9,
        distance_uncertainty_m=0.20,
        evidence_quality=0.85,
        ttc_sec=None, # Unavailable
        cpa_miss_m=None,
        relation_state="INDEPENDENT_PEDESTRIAN",
        approach_speed_m_s=0.0
    )
    
    print(f"  Nominal Distance:            {res_stationary.nominal_distance_m:.2f} m")
    print(f"  TTC Available:               False")
    print(f"  Approach Speed:              0.0 m/s (Stationary)")
    print(f"  Clearance Policy Status:     {res_stationary.clearance_policy_status}")
    print(f"  Proximity Hazard Flag:       {res_stationary.proximity_hazard}")
    print(f"  Predictive Collision Hazard: {res_stationary.predictive_collision_hazard}")
    print(f"  Hazard Semantics:            {res_stationary.hazard_semantics}")
    print(f"  Risk Decision:               {res_stationary.risk_decision}")
    print(f"  Decision Reason:             {res_stationary.reason}")
    
    assert res_stationary.risk_decision != "SAFE", "CRITICAL SAFETY VIOLATION: Stationary pair at 0.9m marked SAFE!"
    assert res_stationary.hazard_semantics == "CURRENT_PROXIMITY_HAZARD"
    assert res_stationary.risk_decision == "CONFIRMED_DANGER"
    print("  [PASS] Stationary proximity hazard correctly confirmed without requiring TTC.")

    # Subtest 2: Inverse Threat (Safe Distance + Converging Trajectory)
    print("\n--- Subtest 2: Predictive Collision Hazard at Safe Current Distance (3.5m) ---")
    res_predictive = engine.evaluate(
        nominal_distance_m=3.5,
        distance_uncertainty_m=0.20,
        evidence_quality=0.85,
        ttc_sec=1.2, # Converging fast
        cpa_miss_m=0.4,
        relation_state="INDEPENDENT_PEDESTRIAN",
        approach_speed_m_s=2.5
    )
    
    print(f"  Nominal Distance:            {res_predictive.nominal_distance_m:.2f} m (Nominal Safe)")
    print(f"  TTC / CPA:                   {res_predictive.evidence_telemetry['ttc_sec']}s / {res_predictive.evidence_telemetry['cpa_miss_m']}m")
    print(f"  Proximity Hazard Flag:       {res_predictive.proximity_hazard}")
    print(f"  Predictive Collision Hazard: {res_predictive.predictive_collision_hazard}")
    print(f"  Hazard Semantics:            {res_predictive.hazard_semantics}")
    print(f"  Risk Decision:               {res_predictive.risk_decision}")
    
    assert res_predictive.proximity_hazard is False
    assert res_predictive.predictive_collision_hazard is True
    assert res_predictive.hazard_semantics == "PREDICTIVE_COLLISION_HAZARD"
    assert res_predictive.risk_decision == "HIGH_PRIORITY_CANDIDATE"
    print("  [PASS] Predictive collision threat correctly disambiguated from current proximity.")

    # Subtest 3: Non-Increasing Distance Monotonicity Proof
    print("\n--- Subtest 3: Non-Increasing Distance Monotonicity Sweep (u = 0.25m) ---")
    distances = [6.0, 5.0, 4.0, 3.5, 3.0, 2.5, 2.0, 1.63, 1.5, 1.2, 1.0, 0.8, 0.5, 0.2]
    prev_score = -1.0
    
    decision_order = {
        "SAFE": 1,
        "CAUTION": 2,
        "CANDIDATE_REVIEW": 2,
        "HIGH_PRIORITY_CANDIDATE": 3,
        "CONFIRMED_DANGER": 4
    }
    
    print(f"  {'Distance (m)':<14} | {'Risk Score':<12} | {'Risk Decision':<25} | {'Hazard Semantics':<28}")
    print("  " + "-" * 85)
    
    # Decreasing distance should yield non-decreasing risk score
    prev_score = 0.0
    prev_dec_rank = 1
    for d in reversed(distances): # from 0.2m up to 6.0m
        r = engine.evaluate(nominal_distance_m=d, distance_uncertainty_m=0.25)
        # As distance increases, score must be non-increasing
        # (checked below in forward iteration)
    
    last_score = 999.0
    last_rank = 999
    for d in distances: # from 6.0m down to 0.2m
        r = engine.evaluate(nominal_distance_m=d, distance_uncertainty_m=0.25)
        score = r.risk_score
        rank = decision_order.get(r.risk_decision, 2)
        print(f"  {d:<14.2f} | {score:<12.3f} | {r.risk_decision:<25} | {r.hazard_semantics:<28}")
        
        # d1 > d2 => score(d1) <= score(d2)
        if last_score != 999.0:
            assert score >= last_score - 1e-6, f"Distance Monotonicity Inversion: at d={d}, score {score} < {last_score}"
            assert rank >= last_rank, f"Decision Monotonicity Inversion: at d={d}, rank {rank} < {last_rank}"
        last_score = score
        last_rank = rank
        
    print("  [PASS] Non-increasing distance monotonicity verified across score and decision.")

    # Subtest 4: Non-Decreasing Variance Monotonicity Proof
    print("\n--- Subtest 4: Non-Decreasing Variance Monotonicity Sweep (d = 2.0m) ---")
    sigmas = [0.05, 0.10, 0.15, 0.20, 0.30, 0.40, 0.50, 0.75, 1.00, 1.50, 2.00]
    last_score = -1.0
    last_rank = -1
    
    print(f"  {'Sigma (m)':<14} | {'Risk Score':<12} | {'Risk Decision':<25} | {'Uncertainty Level':<18}")
    print("  " + "-" * 75)
    
    for u in sigmas:
        r = engine.evaluate(nominal_distance_m=2.0, distance_uncertainty_m=u)
        score = r.risk_score
        rank = decision_order.get(r.risk_decision, 2)
        print(f"  {u:<14.2f} | {score:<12.3f} | {r.risk_decision:<25} | {r.uncertainty_level:<18}")
        
        if last_score != -1.0:
            assert score >= last_score - 1e-6, f"Variance Monotonicity Inversion: at u={u}, score {score} < {last_score}"
            assert rank >= last_rank, f"Decision Monotonicity Inversion: at u={u}, rank {rank} < {last_rank}"
        last_score = score
        last_rank = rank
        
    print("  [PASS] Non-decreasing variance monotonicity verified across score and decision.")

    semantic_metrics = {
        "stationary_0_9m_hazard_confirmed": True,
        "stationary_hazard_semantics": res_stationary.hazard_semantics,
        "predictive_collision_hazard_confirmed": True,
        "distance_monotonicity_non_increasing": True,
        "variance_monotonicity_non_decreasing": True
    }
    
    with open("safety_backfire_v3/outputs/v3_0_3/safety_semantic_metrics.json", "w") as f:
        json.dump(semantic_metrics, f, indent=2)

    print("\n[SUCCESS] Safety Semantic Separation & Monotonicity Suite Completed!")
    return semantic_metrics

if __name__ == "__main__":
    run_safety_semantic_separation_suite()
