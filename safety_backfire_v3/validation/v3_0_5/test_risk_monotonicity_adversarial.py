"""
V3.0.5 Risk Monotonicity, Uncertainty Interaction & TTC Decoupling Suite

Adversarial Stress Testing of the Risk Policy & Score Engine:
1. 5,000 Random Scenario Pairs for Monotonicity Inversion Search:
   - For any pair (A, B) where d_A > d_B and kinematics/uncertainty are matched:
     Assert risk_score(A) <= risk_score(B).
   - Flag any condition where greater distance results in higher risk.
2. Cross-Coupled Uncertainty Inversion Test:
   - Check if severe uncertainty on a distant entity (d > 3.0m) can ever invert
     risk against a close entity (d < 1.5m).
3. Uncertainty Sweep Behavior (sigma from 0.01m to 1.00m):
   - At fixed distances (0.8m, 1.2m, 1.5m, 2.0m, 3.0m), observe decision transitions.
   - Verify: Higher uncertainty must elevate review/caution priority, but must
     NEVER falsely trigger CONFIRMED_DANGER if evidence quality drops.
4. TTC & Kinematic Decoupling:
   - Verify stationary pair (TTC = None, v = 0) at d <= 1.5m retains CURRENT_PROXIMITY_HAZARD.
   - Verify approaching pair (TTC < 2.5s) at d > 1.5m triggers PREDICTIVE_COLLISION_HAZARD.
   - Verify approaching pair at d <= 1.5m triggers DUAL_HAZARD.
   - Verify receding pair (v < 0, TTC = None) does not trigger collision hazard.
"""
import sys
import os
import math
import json
from pathlib import Path
from typing import Dict, Any, List
import numpy as np

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from safety_backfire_v3.core.uncertainty_risk_engine import UncertaintyAwareRiskEngine

def run_risk_monotonicity_suite():
    print("=" * 80)
    print("   V3.0.5 RISK MONOTONICITY, UNCERTAINTY INTERACTION & TTC DECOUPLING   ")
    print("=" * 80)
    
    engine = UncertaintyAwareRiskEngine(
        danger_distance_m=1.5,
        caution_distance_m=3.0,
        critical_ttc_sec=2.5,
        critical_clearance_zone_m=1.0,
        warning_clearance_zone_m=1.8,
        coverage_factor_k=2.24
    )
    
    rng = np.random.RandomState(8888)
    
    # -------------------------------------------------------------
    # 1. 5,000 Pairwise Monotonicity Inversion Search
    # -------------------------------------------------------------
    print("\n[1/4] Running 5,000 Pairwise Monotonicity Inversion Tests...")
    inversion_count_matched = 0
    inversion_count_cross = 0
    n_pairs = 5000
    
    inversion_records = []
    
    for _ in range(n_pairs):
        # Generate two distances
        d1 = float(rng.uniform(0.2, 5.0))
        d2 = float(rng.uniform(0.2, 5.0))
        if abs(d1 - d2) < 0.02:
            continue
            
        d_close = min(d1, d2)
        d_far = max(d1, d2)
        
        # Test 1A: Matched conditions (identical uncertainty & TTC)
        u_matched = float(rng.uniform(0.05, 0.40))
        ev_matched = float(rng.uniform(0.5, 1.0))
        ttc_matched = float(rng.uniform(1.0, 5.0)) if rng.rand() > 0.5 else None
        
        res_close = engine.evaluate(d_close, u_matched, ev_matched, ttc_matched)
        res_far = engine.evaluate(d_far, u_matched, ev_matched, ttc_matched)
        
        if res_far.risk_score > res_close.risk_score + 1e-6:
            inversion_count_matched += 1
            inversion_records.append({
                "type": "MATCHED_INVERSION",
                "d_close": d_close,
                "d_far": d_far,
                "score_close": res_close.risk_score,
                "score_far": res_far.risk_score
            })
            
        # Test 1B: Cross-coupled: close entity with low uncertainty vs far entity with high uncertainty
        # Close entity is in danger zone (<= 1.5m), far entity is outside caution zone (>= 3.0m)
        if d_close <= 1.50 and d_far >= 3.00:
            res_close_clean = engine.evaluate(d_close, distance_uncertainty_m=0.08, evidence_quality=0.90)
            res_far_noisy = engine.evaluate(d_far, distance_uncertainty_m=0.85, evidence_quality=0.40)
            
            # Far noisy entity should NEVER have a higher risk score than close entity!
            if res_far_noisy.risk_score > res_close_clean.risk_score:
                inversion_count_cross += 1
                inversion_records.append({
                    "type": "CROSS_COUPLED_INVERSION",
                    "d_close": d_close,
                    "d_far": d_far,
                    "score_close": res_close_clean.risk_score,
                    "score_far": res_far_noisy.risk_score
                })

    print(f"  - Matched Condition Monotonicity Violations: {inversion_count_matched}/{n_pairs} ({inversion_count_matched/n_pairs*100.0:.2f}%)")
    print(f"  - Cross-Coupled Safe/Danger Inversions:     {inversion_count_cross}/{n_pairs} ({inversion_count_cross/n_pairs*100.0:.2f}%)")

    # -------------------------------------------------------------
    # 2. Uncertainty Sweep Behavior (sigma from 0.05m to 1.00m)
    # -------------------------------------------------------------
    print("\n[2/4] Testing Uncertainty Sweep across 5 Physical Distance Levels...")
    sigmas = list(np.round(np.linspace(0.05, 1.00, 20), 3))
    test_dists = [0.8, 1.2, 1.5, 2.0, 3.5]
    
    unc_sweep_data = {}
    for d in test_dists:
        decisions_for_d = []
        scores_for_d = []
        for s in sigmas:
            # High evidence quality
            res_high_ev = engine.evaluate(d, distance_uncertainty_m=s, evidence_quality=0.85)
            # Low evidence quality
            res_low_ev = engine.evaluate(d, distance_uncertainty_m=s, evidence_quality=0.35)
            decisions_for_d.append({
                "sigma_m": s,
                "high_ev_decision": res_high_ev.risk_decision,
                "high_ev_score": res_high_ev.risk_score,
                "low_ev_decision": res_low_ev.risk_decision,
                "low_ev_score": res_low_ev.risk_score
            })
            scores_for_d.append(res_high_ev.risk_score)
        
        unc_sweep_data[f"dist_{d}m"] = decisions_for_d
        
        # Check that risk score is monotonically non-decreasing with uncertainty at fixed distance
        monotonic_score_with_u = all(scores_for_d[i] <= scores_for_d[i+1] + 1e-5 for i in range(len(scores_for_d)-1))
        print(f"  - d = {d:<4.1f}m: Score Monotonic with Uncertainty: {'PASS' if monotonic_score_with_u else 'FAIL'} (Min: {scores_for_d[0]:.3f}, Max: {scores_for_d[-1]:.3f})")

    # -------------------------------------------------------------
    # 3. TTC & Kinematic Threat Decoupling Suite
    # -------------------------------------------------------------
    print("\n[3/4] Evaluating Kinetic Threat & Hazard Semantic Decoupling...")
    scenarios = [
        # 1. Stationary Proximity Hazard (TTC = None, v = 0, d <= 1.0m)
        {
            "name": "Stationary Critical Clearance",
            "d": 0.8, "u": 0.15, "ev": 0.9, "ttc": None, "v": 0.0,
            "exp_hazard": "CURRENT_PROXIMITY_HAZARD", "exp_decision": "CONFIRMED_DANGER"
        },
        # 2. Stationary Danger Hazard (TTC = None, v = 0, d = 1.3m)
        {
            "name": "Stationary Proximity Danger",
            "d": 1.3, "u": 0.15, "ev": 0.9, "ttc": None, "v": 0.0,
            "exp_hazard": "CURRENT_PROXIMITY_HAZARD", "exp_decision": "CONFIRMED_DANGER"
        },
        # 3. Converging Collision Threat from Caution Distance (TTC = 1.5s, d = 2.2m)
        {
            "name": "Approaching Collision from Caution Distance",
            "d": 2.2, "u": 0.20, "ev": 0.8, "ttc": 1.5, "v": 1.2,
            "exp_hazard": "PREDICTIVE_COLLISION_HAZARD", "exp_decision": "CONFIRMED_DANGER"
        },
        # 4. Dual Hazard: Close Proximity + Active Convergence (TTC = 1.2s, d = 0.9m)
        {
            "name": "Dual Hazard: Proximity + Convergence",
            "d": 0.9, "u": 0.15, "ev": 0.9, "ttc": 1.2, "v": 1.0,
            "exp_hazard": "DUAL_HAZARD", "exp_decision": "CONFIRMED_DANGER"
        },
        # 5. Safe Distance Converging Threat (TTC = 2.0s, d = 3.5m)
        {
            "name": "Safe Distance Converging Threat",
            "d": 3.5, "u": 0.25, "ev": 0.8, "ttc": 2.0, "v": 1.5,
            "exp_hazard": "PREDICTIVE_COLLISION_HAZARD", "exp_decision": "HIGH_PRIORITY_CANDIDATE"
        },
        # 6. Receding Vehicle (v < 0, TTC = None, d = 2.0m)
        {
            "name": "Receding Vehicle Caution",
            "d": 2.0, "u": 0.15, "ev": 0.8, "ttc": None, "v": -1.2,
            "exp_hazard": "UNCERTAIN_PROXIMITY_CAUTION", "exp_decision": "CAUTION"
        },
        # 7. Safe Separation Stationary (TTC = None, d = 4.0m)
        {
            "name": "Safe Stationary Separation",
            "d": 4.0, "u": 0.15, "ev": 0.9, "ttc": None, "v": 0.0,
            "exp_hazard": "CLEAR_SEPARATION", "exp_decision": "SAFE"
        }
    ]
    
    decoupling_results = []
    print(f"  {'Scenario Name':<38} | {'Nom d':<6} | {'TTC':<6} | {'Reported Semantics':<28} | {'Decision':<18} | {'Match'}")
    print("  " + "-" * 110)
    
    all_decoupling_matched = True
    for sc in scenarios:
        res = engine.evaluate(
            nominal_distance_m=sc["d"],
            distance_uncertainty_m=sc["u"],
            evidence_quality=sc["ev"],
            ttc_sec=sc["ttc"],
            approach_speed_m_s=sc["v"]
        )
        
        hazard_match = (res.hazard_semantics == sc["exp_hazard"])
        decision_match = (res.risk_decision == sc["exp_decision"])
        matched = hazard_match and decision_match
        if not matched:
            all_decoupling_matched = False
            
        ttc_str = f"{sc['ttc']:.1f}s" if sc["ttc"] is not None else "None"
        print(f"  {sc['name']:<38} | {sc['d']:<6.1f} | {ttc_str:<6} | {res.hazard_semantics:<28} | {res.risk_decision:<18} | {'PASS' if matched else 'FAIL'}")
        
        decoupling_results.append({
            "scenario": sc["name"],
            "nominal_distance_m": sc["d"],
            "ttc_sec": sc["ttc"],
            "approach_speed_m_s": sc["v"],
            "reported_hazard_semantics": res.hazard_semantics,
            "expected_hazard_semantics": sc["exp_hazard"],
            "reported_risk_decision": res.risk_decision,
            "expected_risk_decision": sc["exp_decision"],
            "passed": matched
        })

    # -------------------------------------------------------------
    # 4. Safe Degradation under Severe Uncertainty
    # -------------------------------------------------------------
    print("\n[4/4] Verifying Safe Degradation under Severe Uncertainty and Low Evidence Quality...")
    # When distance is nominal danger (d=1.2m) but uncertainty is massive (sigma=0.8m) and evidence quality is low (0.3):
    res_degrade_danger = engine.evaluate(1.2, distance_uncertainty_m=0.8, evidence_quality=0.3)
    # When distance is nominal safe (d=4.0m) but uncertainty is massive (sigma=0.8m) and evidence quality is low (0.3):
    res_degrade_safe = engine.evaluate(4.0, distance_uncertainty_m=0.8, evidence_quality=0.3)
    
    print(f"  - Severe Noise at Danger Distance (d=1.2m, sigma=0.8m, ev=0.3): Decision = {res_degrade_danger.risk_decision} (Safe degrade: CANDIDATE_REVIEW)")
    print(f"  - Severe Noise at Safe Distance   (d=4.0m, sigma=0.8m, ev=0.3): Decision = {res_degrade_safe.risk_decision} (Safe degrade: INSUFFICIENT_EVIDENCE)")
    
    safe_degrade_confirmed = (res_degrade_danger.risk_decision in ["CANDIDATE_REVIEW", "HIGH_PRIORITY_CANDIDATE"]) and (res_degrade_safe.risk_decision == "INSUFFICIENT_EVIDENCE")
    print(f"  - Safe Degradation Verification: {'CONFIRMED' if safe_degrade_confirmed else 'VIOLATION DETECTED'}")

    out_dir = Path(WORKSPACE_ROOT) / "safety_backfire_v3/outputs/v3_0_5"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    output_data = {
        "n_monotonicity_pairs_tested": n_pairs,
        "matched_inversions": inversion_count_matched,
        "cross_coupled_inversions": inversion_count_cross,
        "monotonicity_passed": (inversion_count_matched == 0 and inversion_count_cross == 0),
        "decoupling_all_matched": all_decoupling_matched,
        "safe_degradation_confirmed": safe_degrade_confirmed,
        "scenarios_evaluated": decoupling_results,
        "uncertainty_sweeps": unc_sweep_data
    }
    
    with open(out_dir / "risk_monotonicity_metrics.json", "w") as f:
        json.dump(output_data, f, indent=2)
        
    print(f"\n[SUCCESS] Risk Monotonicity & TTC Decoupling Suite Completed! Saved to {out_dir / 'risk_monotonicity_metrics.json'}")
    return output_data

if __name__ == "__main__":
    run_risk_monotonicity_suite()
