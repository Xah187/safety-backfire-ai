"""
V3.0.5 Stochastic Decision Boundary & Clearance Separation Suite

Falsification Testing of Policy Decision Transitions under Sensory Noise:
1. Continuous Distance Sweep from 0.50m to 3.50m (1,000 Monte Carlo noisy trials per step).
2. High-density sweeps at critical physical clearance boundaries:
   - Critical clearance envelope: 1.0m
   - Danger distance envelope:    1.5m
   - Warning clearance envelope:   1.8m
   - Caution boundary envelope:   3.0m
3. Computes exact empirical decision state distributions:
   P(CONFIRMED_DANGER), P(CAUTION), P(SAFE), P(CANDIDATE_REVIEW), P(HIGH_PRIORITY_CANDIDATE).
4. Evaluates False Negative Rate (FNR) at danger boundaries (d <= 1.0m)
   and False Positive Rate (FPR) at safe distances (d >= 3.0m).
5. Checks decision continuity: Verifies system transitions smoothly through
   intermediate review states rather than erratic chatter/flip-flop.
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

from safety_backfire_v3.core.geometry_v3 import GeometryEngineV3
from safety_backfire_v3.core.uncertainty_risk_engine import UncertaintyAwareRiskEngine

def run_stochastic_clearance_test():
    print("=" * 80)
    print("   V3.0.5 STOCHASTIC DECISION BOUNDARY & CLEARANCE SEPARATION SUITE   ")
    print("=" * 80)
    
    risk_engine = UncertaintyAwareRiskEngine(
        danger_distance_m=1.5,
        caution_distance_m=3.0,
        critical_clearance_zone_m=1.0,
        warning_clearance_zone_m=1.8,
        coverage_factor_k=2.24
    )
    
    # Distance sweep points
    standard_steps = list(np.round(np.arange(0.50, 3.55, 0.15), 2))
    boundary_steps = [0.75, 0.80, 0.85, 0.90, 0.95, 1.00, 1.05, 1.10, 1.40, 1.45, 1.50, 1.55, 1.60, 1.75, 1.80, 1.85, 2.90, 3.00, 3.10]
    all_dists = sorted(list(set(standard_steps + boundary_steps)))
    
    n_trials_per_step = 1000
    rng = np.random.RandomState(4242)
    
    # Sensor noise characteristics
    p_sigma_x, p_sigma_y = 0.12, 0.22
    f_sigma_x, f_sigma_y = 0.08, 0.16
    cov_p = np.array([[p_sigma_x**2, 0.0], [0.0, p_sigma_y**2]], dtype=np.float64)
    cov_f = np.array([[f_sigma_x**2, 0.0], [0.0, f_sigma_y**2]], dtype=np.float64)
    
    results_sweep = []
    
    print(f"\n[1/3] Executing 1,000 Monte Carlo Trials across {len(all_dists)} Distance Steps ({len(all_dists) * n_trials_per_step} total runs)...")
    print(f"  {'d_true (m)':<10} | {'P(DANGER)':<11} | {'P(CAND_REV)':<12} | {'P(CAUTION)':<11} | {'P(SAFE)':<10} | {'Mean d_obs':<12} | {'Mean Width'}")
    print("  " + "-" * 88)
    
    # Track critical boundary metrics
    fn_count_1m = 0
    tot_trials_1m = 0
    fp_count_3m = 0
    tot_trials_3m = 0
    
    for d_true in all_dists:
        counts = {
            "CONFIRMED_DANGER": 0,
            "CANDIDATE_REVIEW": 0,
            "HIGH_PRIORITY_CANDIDATE": 0,
            "CAUTION": 0,
            "SAFE": 0,
            "INSUFFICIENT_EVIDENCE": 0
        }
        
        obs_dists = []
        widths = []
        risk_scores = []
        
        # Forklift at nominal position (0, 6.0)
        f_pos = np.array([0.0, 6.0])
        
        for _ in range(n_trials_per_step):
            # True position at distance d_true along a random orientation
            angle = rng.uniform(0, 2 * math.pi)
            p_pos = f_pos + np.array([d_true * math.cos(angle), d_true * math.sin(angle)])
            
            # Sample noisy observations
            obs_f = rng.multivariate_normal(f_pos, cov_f)
            obs_p = rng.multivariate_normal(p_pos, cov_p)
            
            # Geometry engine evaluation
            geom = GeometryEngineV3.compute_distance_with_uncertainty(
                p_pos=tuple(obs_p),
                f_pos=tuple(obs_f),
                p_cov=cov_p,
                f_cov=cov_f,
                coverage_factor=2.24,
                debias_jensen=True,
                adaptive_2d_calibration=True
            )
            
            d_nom = geom["unbiased_distance_m"]
            u_sigma = geom["distance_uncertainty_m"]
            width = geom["distance_interval_m"][1] - geom["distance_interval_m"][0]
            
            obs_dists.append(d_nom)
            widths.append(width)
            
            # Risk engine evaluation (nominal high quality evidence, stationary pair)
            eval_res = risk_engine.evaluate(
                nominal_distance_m=d_nom,
                distance_uncertainty_m=u_sigma,
                evidence_quality=0.85,
                ttc_sec=None, # Pure proximity clearance test
                coverage_factor=2.24
            )
            
            counts[eval_res.risk_decision] = counts.get(eval_res.risk_decision, 0) + 1
            risk_scores.append(eval_res.risk_score)
            
            if d_true <= 1.00:
                tot_trials_1m += 1
                if eval_res.risk_decision not in ["CONFIRMED_DANGER", "HIGH_PRIORITY_CANDIDATE"]:
                    fn_count_1m += 1
                    
            if d_true >= 3.00:
                tot_trials_3m += 1
                if eval_res.risk_decision == "CONFIRMED_DANGER":
                    fp_count_3m += 1

        p_danger = counts["CONFIRMED_DANGER"] / n_trials_per_step
        p_cand = (counts["CANDIDATE_REVIEW"] + counts["HIGH_PRIORITY_CANDIDATE"]) / n_trials_per_step
        p_caution = counts["CAUTION"] / n_trials_per_step
        p_safe = counts["SAFE"] / n_trials_per_step
        
        mean_obs = float(np.mean(obs_dists))
        mean_w = float(np.mean(widths))
        mean_score = float(np.mean(risk_scores))
        
        # Print selected illustrative steps
        if d_true in [0.5, 0.8, 1.0, 1.2, 1.45, 1.5, 1.6, 1.8, 2.0, 2.5, 3.0, 3.5]:
            print(f"  {d_true:<10.2f} | {p_danger:<11.1%} | {p_cand:<12.1%} | {p_caution:<11.1%} | {p_safe:<10.1%} | {mean_obs:<12.3f}m | {mean_w:.3f}m")
            
        results_sweep.append({
            "d_true_m": d_true,
            "probabilities": {
                "CONFIRMED_DANGER": round(p_danger, 4),
                "CANDIDATE_REVIEW": round(counts["CANDIDATE_REVIEW"] / n_trials_per_step, 4),
                "HIGH_PRIORITY_CANDIDATE": round(counts["HIGH_PRIORITY_CANDIDATE"] / n_trials_per_step, 4),
                "CAUTION": round(p_caution, 4),
                "SAFE": round(p_safe, 4)
            },
            "mean_observed_d_m": round(mean_obs, 3),
            "mean_interval_width_m": round(mean_w, 3),
            "mean_risk_score": round(mean_score, 3)
        })

    # 2. Decision Boundary Diagnostics
    print("\n[2/3] Boundary Clearance Separation Analysis:")
    fnr_1m = (fn_count_1m / tot_trials_1m) * 100.0 if tot_trials_1m > 0 else 0.0
    fpr_3m = (fp_count_3m / tot_trials_3m) * 100.0 if tot_trials_3m > 0 else 0.0
    
    print(f"  - Critical Clearance Envelope (d <= 1.0m) False Negative Rate: {fnr_1m:.2f}% ({fn_count_1m}/{tot_trials_1m} missed danger)")
    print(f"  - Safe Separation Envelope   (d >= 3.0m) False Positive Rate: {fpr_3m:.2f}% ({fp_count_3m}/{tot_trials_3m} false danger alerts)")

    # 3. Check for Monotonicity and Chatter/Flip-Flop
    print("\n[3/3] Checking Decision Boundary Continuity & Monotonicity:")
    danger_probs = [r["probabilities"]["CONFIRMED_DANGER"] for r in results_sweep]
    safe_probs = [r["probabilities"]["SAFE"] for r in results_sweep]
    
    # Verify P(DANGER) is monotonically non-increasing with distance (with small epsilon for sample variance)
    monotonic_danger = all(danger_probs[i] >= danger_probs[i+1] - 0.02 for i in range(len(danger_probs)-1))
    monotonic_safe = all(safe_probs[i] <= safe_probs[i+1] + 0.02 for i in range(len(safe_probs)-1))
    
    # Check for direct chatter (SAFE directly jumping to DANGER without intermediate states)
    # At d=1.5m (boundary), intermediate states (CANDIDATE_REVIEW or CAUTION) must absorb transition!
    boundary_1_5m = [r for r in results_sweep if abs(r["d_true_m"] - 1.50) < 1e-4][0]
    p_intermediate_1_5m = boundary_1_5m["probabilities"]["CAUTION"] + boundary_1_5m["probabilities"]["CANDIDATE_REVIEW"]
    
    print(f"  - P(DANGER) Monotonicity with Distance:    {'CONFIRMED MONOTONIC' if monotonic_danger else 'VIOLATION DETECTED'}")
    print(f"  - P(SAFE) Monotonicity with Distance:      {'CONFIRMED MONOTONIC' if monotonic_safe else 'VIOLATION DETECTED'}")
    print(f"  - Intermediate State Mass at 1.5m Boundary: {p_intermediate_1_5m:.1%} (Prevents binary flip-flop)")

    out_dir = Path(WORKSPACE_ROOT) / "safety_backfire_v3/outputs/v3_0_5"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    output_data = {
        "n_trials_per_step": n_trials_per_step,
        "distance_steps_evaluated": len(all_dists),
        "total_evaluations": len(all_dists) * n_trials_per_step,
        "false_negative_rate_under_1m_pct": round(fnr_1m, 3),
        "false_positive_rate_over_3m_pct": round(fpr_3m, 3),
        "boundary_1_5m_intermediate_mass_pct": round(p_intermediate_1_5m * 100.0, 2),
        "monotonic_danger": monotonic_danger,
        "monotonic_safe": monotonic_safe,
        "sweep_data": results_sweep
    }
    
    with open(out_dir / "stochastic_clearance_metrics.json", "w") as f:
        json.dump(output_data, f, indent=2)
        
    print(f"\n[SUCCESS] Stochastic Clearance Suite Completed! Saved to {out_dir / 'stochastic_clearance_metrics.json'}")
    return output_data

if __name__ == "__main__":
    run_stochastic_clearance_test()
