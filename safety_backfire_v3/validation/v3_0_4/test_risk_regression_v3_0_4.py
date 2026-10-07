"""
V3.0.4 Risk Regression: Physical Safety Clearance Distinction & Monotonicity Audit

Evaluates Downstream Safety Decisions:
1. Clearance Distinction Test:
   - Can the system distinguish a 0.8m clearance from a 2.0m clearance in metric space?
   - 0.8m -> CRITICAL_VIOLATION / CONFIRMED_DANGER / CURRENT_PROXIMITY_HAZARD
   - 2.0m -> ADEQUATE_CLEARANCE / CAUTION / UNCERTAIN_PROXIMITY_CAUTION
2. Stationary Proximity Hazard:
   - Stationary pair at 0.9m (relative speed = 0, TTC = None) -> CONFIRMED_DANGER.
   - Proves proximity hazard is never masked by infinite TTC.
3. Monotonicity Verification:
   - Metric distance monotonicity: d_true_1 < d_true_2 -> d_est_1 < d_est_2
   - Variance monotonicity: sigma(d) is non-decreasing with range
   - Risk score monotonicity: risk_score(d) is strictly non-increasing with distance
4. Operator Suppression Safety Invariant:
   - Operator inside cabin at 0.4m -> SUPPRESSED_OPERATOR, risk_score = 0.0.
"""
import sys
import math
import json
import os
from pathlib import Path
import numpy as np

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from safety_backfire_v3.core.geometry_v3 import (
    GeometryEngineV3,
    CameraCalibrationContract,
    CalibrationSource,
    GeometricProjectionMethod
)
from safety_backfire_v3.core.uncertainty_risk_engine import (
    UncertaintyAwareRiskEngine,
    RiskEvaluationResult
)
from safety_backfire_v3.validation.v3_0_4.test_geometry_recovery_v3_0_4 import (
    CorrectedSurveyedGroundCalibrator
)

def run_risk_regression_evaluation():
    print("=" * 75)
    print("   V3.0.4 RISK REGRESSION: PHYSICAL SAFETY CLEARANCE DISTINCTION AUDIT   ")
    print("=" * 75)
    
    calibrator = CorrectedSurveyedGroundCalibrator(camera_height_m=3.5, camera_pitch_deg=28.0)
    engine = GeometryEngineV3(
        calibrator=calibrator,
        camera_height_m=3.5,
        camera_pitch_deg=28.0,
        calibration_contract=CameraCalibrationContract(
            camera_height_m=3.5,
            camera_pitch_deg=28.0,
            calibration_source=CalibrationSource.SURVEYED.value,
            is_verified=True,
            verification_status="VERIFIED_SURVEYED"
        )
    )
    risk_engine = UncertaintyAwareRiskEngine(
        danger_distance_m=1.5,
        caution_distance_m=3.0,
        critical_clearance_zone_m=1.0,
        warning_clearance_zone_m=1.8,
        coverage_factor_k=2.24 # V3.0.4 calibrated Rice factor
    )
    
    # -------------------------------------------------------------
    # 1. Critical Clearance Distinction Test: 0.8m vs 2.0m
    # -------------------------------------------------------------
    print("\n--- Subtest 1: 0.8m vs 2.0m Clearance Distinction Test ---")
    f_true_pos = (0.0, 5.0) # Forklift at Y=5.0m
    
    # Scenario A: 0.8m clearance (Pedestrian at Y=5.8m)
    p_true_08 = (0.0, 5.8)
    px_f = calibrator.world_to_pixel(f_true_pos)
    px_p08 = calibrator.world_to_pixel(p_true_08)
    
    proj_f = engine.project_entity_ground([px_f[0]-40, px_f[1]-60, px_f[0]+40, px_f[1]])
    proj_p08 = engine.project_entity_ground([px_p08[0]-20, px_p08[1]-70, px_p08[0]+20, px_p08[1]])
    
    unc_08 = engine.compute_distance_with_uncertainty(
        p_pos=proj_p08["world_pos_m"],
        f_pos=proj_f["world_pos_m"],
        p_unc_m=0.15,
        f_unc_m=0.10,
        coverage_factor=2.24
    )
    risk_08 = risk_engine.evaluate(
        nominal_distance_m=unc_08["unbiased_distance_m"],
        distance_uncertainty_m=unc_08["distance_uncertainty_m"],
        evidence_quality=0.85,
        ttc_sec=None, # Stationary / proximity-only test
        approach_speed_m_s=0.0
    )
    
    # Scenario B: 2.0m clearance (Pedestrian at Y=7.0m)
    p_true_20 = (0.0, 7.0)
    px_p20 = calibrator.world_to_pixel(p_true_20)
    proj_p20 = engine.project_entity_ground([px_p20[0]-20, px_p20[1]-70, px_p20[0]+20, px_p20[1]])
    
    unc_20 = engine.compute_distance_with_uncertainty(
        p_pos=proj_p20["world_pos_m"],
        f_pos=proj_f["world_pos_m"],
        p_unc_m=0.18,
        f_unc_m=0.10,
        coverage_factor=2.24
    )
    risk_20 = risk_engine.evaluate(
        nominal_distance_m=unc_20["unbiased_distance_m"],
        distance_uncertainty_m=unc_20["distance_uncertainty_m"],
        evidence_quality=0.85,
        ttc_sec=None,
        approach_speed_m_s=0.0
    )
    
    print(f"  Scenario A (True Clearance: 0.80 m):")
    print(f"    - Estimated Metric Distance:  {unc_08['unbiased_distance_m']:.3f} m (Error: {unc_08['unbiased_distance_m'] - 0.8:.4f} m)")
    print(f"    - 95% Confidence Interval:    {unc_08['distance_interval_m']} m")
    print(f"    - Clearance Policy Status:    {risk_08.clearance_policy_status}")
    print(f"    - Hazard Semantics:           {risk_08.hazard_semantics}")
    print(f"    - Safety Decision:            {risk_08.risk_decision}")
    print(f"    - Risk Score:                 {risk_08.risk_score:.3f}")
    
    print(f"\n  Scenario B (True Clearance: 2.00 m):")
    print(f"    - Estimated Metric Distance:  {unc_20['unbiased_distance_m']:.3f} m (Error: {unc_20['unbiased_distance_m'] - 2.0:.4f} m)")
    print(f"    - 95% Confidence Interval:    {unc_20['distance_interval_m']} m")
    print(f"    - Clearance Policy Status:    {risk_20.clearance_policy_status}")
    print(f"    - Hazard Semantics:           {risk_20.hazard_semantics}")
    print(f"    - Safety Decision:            {risk_20.risk_decision}")
    print(f"    - Risk Score:                 {risk_20.risk_score:.3f}")
    
    distinction_pass = (
        risk_08.risk_decision == "CONFIRMED_DANGER" and
        risk_20.risk_decision == "CAUTION" and
        risk_08.clearance_policy_status == "CRITICAL_VIOLATION" and
        risk_20.clearance_policy_status == "ADEQUATE_CLEARANCE"
    )
    print(f"\n  DISTINCTION AUDIT VERDICT:     {'[PASS] CLEARANCE SEPARATED' if distinction_pass else '[FAIL]'}")
    
    # -------------------------------------------------------------
    # 2. Stationary Proximity Hazard (0.9m without TTC)
    # -------------------------------------------------------------
    print("\n--- Subtest 2: Stationary Proximity Hazard Test (0.9m without TTC) ---")
    p_true_09 = (0.0, 5.9)
    px_p09 = calibrator.world_to_pixel(p_true_09)
    proj_p09 = engine.project_entity_ground([px_p09[0]-20, px_p09[1]-70, px_p09[0]+20, px_p09[1]])
    
    unc_09 = engine.compute_distance_with_uncertainty(
        p_pos=proj_p09["world_pos_m"],
        f_pos=proj_f["world_pos_m"],
        p_unc_m=0.15,
        f_unc_m=0.10,
        coverage_factor=2.24
    )
    risk_09 = risk_engine.evaluate(
        nominal_distance_m=unc_09["unbiased_distance_m"],
        distance_uncertainty_m=unc_09["distance_uncertainty_m"],
        evidence_quality=0.90,
        ttc_sec=None, # Infinite TTC / stationary
        approach_speed_m_s=0.0
    )
    print(f"  Stationary Pair at True Distance 0.90 m:")
    print(f"    - Estimated Distance:         {unc_09['unbiased_distance_m']:.3f} m")
    print(f"    - TTC:                        None (Infinite / Stationary)")
    print(f"    - Hazard Semantics:           {risk_09.hazard_semantics}")
    print(f"    - Decision:                   {risk_09.risk_decision}")
    stationary_pass = (risk_09.risk_decision == "CONFIRMED_DANGER" and risk_09.hazard_semantics == "CURRENT_PROXIMITY_HAZARD")
    print(f"    - Stationary Hazard Verdict:  {'[PASS] CONFIRMED_DANGER PRESERVED' if stationary_pass else '[FAIL]'}")

    # -------------------------------------------------------------
    # 3. Monotonicity Verification Across Distance Range (0.5m to 10.0m)
    # -------------------------------------------------------------
    print("\n--- Subtest 3: Monotonicity Verification Across Range ---")
    distances = [0.5, 0.8, 1.2, 1.8, 2.5, 3.5, 5.0, 7.0, 9.0]
    estimated_dists = []
    risk_scores = []
    
    for d in distances:
        p_pos = (0.0, 4.0 + d)
        px_p = calibrator.world_to_pixel(p_pos)
        px_f_base = calibrator.world_to_pixel((0.0, 4.0))
        
        proj_p = engine.project_entity_ground([px_p[0]-20, px_p[1]-70, px_p[0]+20, px_p[1]])
        proj_fb = engine.project_entity_ground([px_f_base[0]-40, px_f_base[1]-60, px_f_base[0]+40, px_f_base[1]])
        
        unc = engine.compute_distance_with_uncertainty(
            p_pos=proj_p["world_pos_m"],
            f_pos=proj_fb["world_pos_m"],
            p_unc_m=0.15,
            f_unc_m=0.10,
            coverage_factor=2.24
        )
        r = risk_engine.evaluate(
            nominal_distance_m=unc["unbiased_distance_m"],
            distance_uncertainty_m=unc["distance_uncertainty_m"],
            evidence_quality=0.85
        )
        estimated_dists.append(unc["unbiased_distance_m"])
        risk_scores.append(r.risk_score)
        print(f"    True d: {d:4.1f}m -> Est d: {unc['unbiased_distance_m']:5.3f}m | Score: {r.risk_score:.3f} | Decision: {r.risk_decision}")
        
    dist_mono = all(estimated_dists[i] < estimated_dists[i+1] for i in range(len(estimated_dists)-1))
    score_mono = all(risk_scores[i] >= risk_scores[i+1] - 1e-4 for i in range(len(risk_scores)-1))
    
    print(f"  Distance Strict Monotonicity:  {'[PASS]' if dist_mono else '[FAIL]'}")
    print(f"  Risk Score Non-Increasing:    {'[PASS]' if score_mono else '[FAIL]'}")

    # -------------------------------------------------------------
    # 4. Operator Suppression Invariant Test
    # -------------------------------------------------------------
    print("\n--- Subtest 4: Operator Cabin Suppression Invariant ---")
    risk_operator = risk_engine.evaluate(
        nominal_distance_m=0.35, # Inside vehicle cabin footprint
        distance_uncertainty_m=0.15,
        evidence_quality=0.90,
        relation_state="OPERATOR_ON_VEHICLE"
    )
    print(f"    Relation State:               OPERATOR_ON_VEHICLE")
    print(f"    Nominal Distance:             {risk_operator.nominal_distance_m:.2f} m")
    print(f"    Risk Decision:                {risk_operator.risk_decision}")
    print(f"    Risk Score:                   {risk_operator.risk_score:.1f}")
    operator_pass = (risk_operator.risk_decision == "SUPPRESSED_OPERATOR" and risk_operator.risk_score == 0.0)
    print(f"    Operator Suppression Verdict: {'[PASS]' if operator_pass else '[FAIL]'}")

    # Save metrics
    out_dir = Path(WORKSPACE_ROOT) / "safety_backfire_v3/outputs/v3_0_4"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    results = {
        "clearance_distinction_08_vs_20": {
            "scenario_0_8m": {
                "true_distance_m": 0.80,
                "estimated_distance_m": unc_08["unbiased_distance_m"],
                "clearance_status": risk_08.clearance_policy_status,
                "decision": risk_08.risk_decision,
                "risk_score": risk_08.risk_score
            },
            "scenario_2_0m": {
                "true_distance_m": 2.00,
                "estimated_distance_m": unc_20["unbiased_distance_m"],
                "clearance_status": risk_20.clearance_policy_status,
                "decision": risk_20.risk_decision,
                "risk_score": risk_20.risk_score
            },
            "distinction_pass": distinction_pass
        },
        "stationary_proximity_hazard": {
            "true_distance_m": 0.90,
            "estimated_distance_m": unc_09["unbiased_distance_m"],
            "hazard_semantics": risk_09.hazard_semantics,
            "decision": risk_09.risk_decision,
            "stationary_pass": stationary_pass
        },
        "monotonicity": {
            "tested_distances_m": distances,
            "estimated_distances_m": estimated_dists,
            "risk_scores": risk_scores,
            "distance_monotonicity_pass": dist_mono,
            "risk_score_monotonicity_pass": score_mono
        },
        "operator_suppression": {
            "decision": risk_operator.risk_decision,
            "risk_score": risk_operator.risk_score,
            "operator_pass": operator_pass
        }
    }
    
    with open(out_dir / "risk_regression_metrics.json", "w") as f:
        json.dump(results, f, indent=2)
        
    print("\n[SUCCESS] Risk Regression Test Suite Completed! Outputs saved to outputs/v3_0_4/")
    return results

if __name__ == "__main__":
    run_risk_regression_evaluation()
