"""
V3.0.5 Uncertainty Red Team & Out-of-Sample Calibration

Falsification Testing of the V3.0.4 Uncertainty Model (FAIL-28 Remediation):
1. Strict Separation of Calibration and Blind Test Partitions:
   - Partition A: Calibration split (250 pairs, seed 5555) to tune k-factor.
   - Partition B: Blind out-of-sample test split (500 pairs, seed 9999).
2. Realistic Anisotropic Noise Modeling:
   - Monocular camera depth perspective creates anisotropic covariance:
     sigma_Y (longitudinal depth) is 2x to 4x larger than sigma_X (lateral).
3. Fine-Grained Stratification:
   - 8 Distance Tiers: [0-0.5m, 0.5-1m, 1-2m, 2-4m, 4-6m, 6-8m, 8-12m, 12m+]
   - 3 Uncertainty Tiers: LOW, MODERATE, HIGH
   - 4 Geometric Orientations: HEAD_ON, ORTHOGONAL, OBLIQUE_45, REAR
4. Comprehensive k-factor Sweep:
   - k in [1.50, 1.60, 1.70, 1.80, 1.90, 1.96, 2.00, 2.10, 2.20, 2.24, 2.30, 2.40, 2.50, 2.75, 3.00]
5. Asymmetric Safety Metric Separation:
   - Lower Bound Violations (hazard: d_true < lower_95 -> false sense of safety!)
   - Upper Bound Violations (efficiency: d_true > upper_95)
   - Sharpness (mean interval width)
"""
import sys
import os
import math
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
import numpy as np

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from safety_backfire_v3.core.geometry_v3 import GeometryEngineV3

def wilson_score_interval(successes: int, total: int, z: float = 1.96) -> Tuple[float, float]:
    """Computes Wilson score 95% confidence interval for binomial coverage proportion."""
    if total == 0:
        return (0.0, 0.0)
    p = successes / total
    denom = 1.0 + (z**2) / total
    center = (p + (z**2) / (2 * total)) / denom
    margin = (z * math.sqrt((p * (1 - p) / total) + ((z**2) / (4 * (total**2))))) / denom
    return (max(0.0, center - margin), min(1.0, center + margin))

def generate_adversarial_uncertainty_dataset(n_samples: int, seed: int) -> List[Dict[str, Any]]:
    """
    Generates realistic, physically motivated evaluation instances with
    anisotropic covariance and fine-grained distance stratification.
    """
    rng = np.random.RandomState(seed)
    dataset = []
    
    tier_specs = [
        ("0-0.5m", 0.15, 0.50, int(n_samples * 0.10)),
        ("0.5-1m", 0.50, 1.00, int(n_samples * 0.15)),
        ("1-2m",   1.00, 2.00, int(n_samples * 0.20)),
        ("2-4m",   2.00, 4.00, int(n_samples * 0.20)),
        ("4-6m",   4.00, 6.00, int(n_samples * 0.12)),
        ("6-8m",   6.00, 8.00, int(n_samples * 0.10)),
        ("8-12m",  8.00, 12.00, int(n_samples * 0.08)),
        ("12m+",   12.00, 16.00, int(n_samples * 0.05)),
    ]
    
    # Adjust total count to match exactly n_samples
    allocated = sum(s[3] for s in tier_specs)
    tier_specs[2] = (tier_specs[2][0], tier_specs[2][1], tier_specs[2][2], tier_specs[2][3] + (n_samples - allocated))
    
    orientations = ["HEAD_ON", "ORTHOGONAL", "OBLIQUE_45", "REAR"]
    sample_id = 0
    
    for tier_name, d_min, d_max, count in tier_specs:
        for _ in range(count):
            sample_id += 1
            # Forklift positioned in sensor field of view
            f_x = float(rng.uniform(-4.0, 4.0))
            f_y = float(rng.uniform(3.0, 12.0))
            
            true_d = float(rng.uniform(d_min, d_max))
            theta = float(rng.uniform(0.0, 2 * math.pi))
            
            p_x = f_x + true_d * math.cos(theta)
            p_y = f_y + true_d * math.sin(theta)
            
            # Anisotropic covariance: In monocular geometry, depth (Y) variance
            # expands quadratically with camera distance!
            # Lateral variance: sigma_x \approx 0.05 to 0.15m
            # Longitudinal variance: sigma_y \approx sigma_x * (1.5 + 0.15 * Y)
            p_sigma_x = float(rng.uniform(0.08, 0.20))
            p_sigma_y = float(p_sigma_x * rng.uniform(1.8, 3.2))
            
            f_sigma_x = float(rng.uniform(0.06, 0.15))
            f_sigma_y = float(f_sigma_x * rng.uniform(1.5, 2.5))
            
            # Covariances
            cov_p = np.array([[p_sigma_x**2, 0.0], [0.0, p_sigma_y**2]], dtype=np.float64)
            cov_f = np.array([[f_sigma_x**2, 0.0], [0.0, f_sigma_y**2]], dtype=np.float64)
            
            # Sample noisy observations
            obs_p = rng.multivariate_normal([p_x, p_y], cov_p)
            obs_f = rng.multivariate_normal([f_x, f_y], cov_f)
            
            tot_sigma = math.hypot(p_sigma_y, f_sigma_y)
            if tot_sigma <= 0.25:
                unc_tier = "LOW"
            elif tot_sigma <= 0.50:
                unc_tier = "MODERATE"
            else:
                unc_tier = "HIGH"
                
            angle_deg = math.degrees(theta) % 360
            if angle_deg < 45 or angle_deg >= 315:
                orient = "HEAD_ON"
            elif 45 <= angle_deg < 135:
                orient = "ORTHOGONAL"
            elif 135 <= angle_deg < 225:
                orient = "REAR"
            else:
                orient = "OBLIQUE_45"
                
            dataset.append({
                "sample_id": f"SMP_{sample_id:04d}",
                "distance_tier": tier_name,
                "uncertainty_tier": unc_tier,
                "orientation": orient,
                "true_d": true_d,
                "p_true": (p_x, p_y),
                "f_true": (f_x, f_y),
                "p_obs": (float(obs_p[0]), float(obs_p[1])),
                "f_obs": (float(obs_f[0]), float(obs_f[1])),
                "cov_p": cov_p.tolist(),
                "cov_f": cov_f.tolist(),
                "tot_sigma": tot_sigma
            })
            
    return dataset

def evaluate_partition(
    dataset: List[Dict[str, Any]],
    k_factor: float,
    debias_jensen: bool = True
) -> Dict[str, Any]:
    """Evaluates coverage, sharpness, and directional violations on a dataset."""
    n = len(dataset)
    covered_count = 0
    lower_violation_count = 0  # CRITICAL: true_d < lower_bound (over-estimated distance, unsafe!)
    upper_violation_count = 0  # true_d > upper_bound (under-estimated distance)
    interval_widths = []
    
    # Stratified collectors
    strat_dist = {}
    strat_unc = {}
    strat_orient = {}
    
    for item in dataset:
        p_obs = tuple(item["p_obs"])
        f_obs = tuple(item["f_obs"])
        cov_p = np.array(item["cov_p"])
        cov_f = np.array(item["cov_f"])
        true_d = item["true_d"]
        
        # Geometry engine calibrated uncertainty computation
        res = GeometryEngineV3.compute_distance_with_uncertainty(
            p_pos=p_obs,
            f_pos=f_obs,
            p_cov=cov_p,
            f_cov=cov_f,
            coverage_factor=k_factor,
            debias_jensen=debias_jensen,
            adaptive_2d_calibration=False # Use explicit k
        )
        
        lower_95 = res["distance_interval_m"][0]
        upper_95 = res["distance_interval_m"][1]
        width = upper_95 - lower_95
        interval_widths.append(width)
        
        is_covered = (lower_95 <= true_d <= upper_95)
        if is_covered:
            covered_count += 1
        elif true_d < lower_95:
            lower_violation_count += 1
        else:
            upper_violation_count += 1
            
        # Groupings
        d_tier = item["distance_tier"]
        u_tier = item["uncertainty_tier"]
        orient = item["orientation"]
        
        for group_dict, key in [(strat_dist, d_tier), (strat_unc, u_tier), (strat_orient, orient)]:
            if key not in group_dict:
                group_dict[key] = {"total": 0, "covered": 0, "lower_viol": 0, "upper_viol": 0, "widths": []}
            group_dict[key]["total"] += 1
            if is_covered:
                group_dict[key]["covered"] += 1
            elif true_d < lower_95:
                group_dict[key]["lower_viol"] += 1
            else:
                group_dict[key]["upper_viol"] += 1
            group_dict[key]["widths"].append(width)
            
    coverage_rate = covered_count / n
    ci_low, ci_high = wilson_score_interval(covered_count, n)
    
    # Process group summaries
    def process_groups(g_dict):
        out = {}
        for k, v in g_dict.items():
            tot = v["total"]
            cov = v["covered"]
            c_low, c_high = wilson_score_interval(cov, tot)
            out[k] = {
                "total": tot,
                "coverage_pct": round(cov / tot * 100.0, 2),
                "wilson_95_ci": [round(c_low * 100.0, 2), round(c_high * 100.0, 2)],
                "lower_viol_pct": round(v["lower_viol"] / tot * 100.0, 2),
                "upper_viol_pct": round(v["upper_viol"] / tot * 100.0, 2),
                "mean_width_m": round(float(np.mean(v["widths"])), 3)
            }
        return out

    return {
        "n_samples": n,
        "k_factor": k_factor,
        "coverage_pct": round(coverage_rate * 100.0, 2),
        "wilson_score_95_ci": [round(ci_low * 100.0, 2), round(ci_high * 100.0, 2)],
        "lower_violation_pct": round(lower_violation_count / n * 100.0, 2),
        "upper_violation_pct": round(upper_violation_count / n * 100.0, 2),
        "mean_interval_width_m": round(float(np.mean(interval_widths)), 3),
        "median_interval_width_m": round(float(np.median(interval_widths)), 3),
        "by_distance_tier": process_groups(strat_dist),
        "by_uncertainty_tier": process_groups(strat_unc),
        "by_orientation": process_groups(strat_orient)
    }

def run_uncertainty_red_team_suite():
    print("=" * 80)
    print("   V3.0.5 UNCERTAINTY RED TEAM: OUT-OF-SAMPLE FALSIFICATION SUITE   ")
    print("=" * 80)
    
    # 1. Independent Partition Generation
    print("\n[1/4] Generating Independent Partitions (Zero Sample Overlap)...")
    calib_set = generate_adversarial_uncertainty_dataset(n_samples=250, seed=5555)
    test_set = generate_adversarial_uncertainty_dataset(n_samples=500, seed=9999)
    print(f"  Partition A (Calibration): {len(calib_set)} samples (Seed: 5555)")
    print(f"  Partition B (Blind Test):  {len(test_set)} samples (Seed: 9999)")
    
    # 2. k-factor Sweep on Calibration Set vs Blind Test Set
    print("\n[2/4] Executing Comprehensive k-factor Calibration Sweep...")
    k_candidates = [1.50, 1.60, 1.70, 1.80, 1.90, 1.96, 2.00, 2.10, 2.20, 2.24, 2.30, 2.40, 2.50, 2.75, 3.00]
    
    sweep_results = []
    print(f"  {'k':<6} | {'Calib Cov %':<12} | {'Calib Width':<12} | {'Blind Cov %':<12} | {'Blind 95% CI':<16} | {'Lower Viol %':<14} | {'Blind Width'}")
    print("  " + "-" * 95)
    
    calib_optimal_k = None
    min_diff_to_95 = 999.0
    
    for k in k_candidates:
        res_cal = evaluate_partition(calib_set, k_factor=k)
        res_test = evaluate_partition(test_set, k_factor=k)
        
        diff = abs(res_cal["coverage_pct"] - 95.0)
        if diff < min_diff_to_95 and res_cal["coverage_pct"] >= 95.0:
            min_diff_to_95 = diff
            calib_optimal_k = k
            
        ci_str = f"[{res_test['wilson_score_95_ci'][0]:.1f}, {res_test['wilson_score_95_ci'][1]:.1f}]%"
        print(f"  {k:<6.2f} | {res_cal['coverage_pct']:<12.1f} | {res_cal['mean_interval_width_m']:<12.3f}m | {res_test['coverage_pct']:<12.1f} | {ci_str:<16} | {res_test['lower_violation_pct']:<14.1f} | {res_test['mean_interval_width_m']:.3f}m")
        
        sweep_results.append({
            "k": k,
            "calib_coverage_pct": res_cal["coverage_pct"],
            "calib_width_m": res_cal["mean_interval_width_m"],
            "blind_coverage_pct": res_test["coverage_pct"],
            "blind_wilson_ci": res_test["wilson_score_95_ci"],
            "blind_lower_viol_pct": res_test["lower_violation_pct"],
            "blind_upper_viol_pct": res_test["upper_violation_pct"],
            "blind_width_m": res_test["mean_interval_width_m"]
        })

    print(f"\n  Optimal Calibrated k on Partition A: k = {calib_optimal_k:.2f}")

    # 3. In-Depth Evaluation of Production k=2.24 vs Baseline k=1.96 on Blind Partition B
    print("\n[3/4] Forensic Evaluation of Production k=2.24 vs Baseline k=1.96 on Blind Test Set...")
    eval_196 = evaluate_partition(test_set, k_factor=1.96)
    eval_224 = evaluate_partition(test_set, k_factor=2.24)
    eval_optimal = evaluate_partition(test_set, k_factor=calib_optimal_k)

    print("\n--- Distance Tier Stratification on Blind Partition B (500 samples) ---")
    print(f"  {'Distance Tier':<15} | {'N':<5} | {'k=1.96 Cov':<12} | {'k=2.24 Cov':<12} | {'k=2.24 Viol (L/U)':<18} | {'k=2.24 Mean Width'}")
    print("  " + "-" * 85)
    for tier in ["0-0.5m", "0.5-1m", "1-2m", "2-4m", "4-6m", "6-8m", "8-12m", "12m+"]:
        t196 = eval_196["by_distance_tier"][tier]
        t224 = eval_224["by_distance_tier"][tier]
        viol_str = f"{t224['lower_viol_pct']:.1f}% / {t224['upper_viol_pct']:.1f}%"
        print(f"  {tier:<15} | {t224['total']:<5} | {t196['coverage_pct']:<12.1f} | {t224['coverage_pct']:<12.1f} | {viol_str:<18} | {t224['mean_width_m']:.3f}m")

    print("\n--- Uncertainty Tier Stratification on Blind Partition B ---")
    print(f"  {'Uncertainty Tier':<18} | {'N':<5} | {'k=1.96 Cov':<12} | {'k=2.24 Cov':<12} | {'k=2.24 Viol (L/U)':<18} | {'k=2.24 Mean Width'}")
    print("  " + "-" * 88)
    for utier in ["LOW", "MODERATE", "HIGH"]:
        u196 = eval_196["by_uncertainty_tier"][utier]
        u224 = eval_224["by_uncertainty_tier"][utier]
        viol_str = f"{u224['lower_viol_pct']:.1f}% / {u224['upper_viol_pct']:.1f}%"
        print(f"  {utier:<18} | {u224['total']:<5} | {u196['coverage_pct']:<12.1f} | {u224['coverage_pct']:<12.1f} | {viol_str:<18} | {u224['mean_width_m']:.3f}m")

    # 4. Check for Under-Coverage and Critical Safety Boundaries
    print("\n[4/4] Safety Falsification Verdict on Uncertainty Model:")
    blind_cov_224 = eval_224["coverage_pct"]
    blind_low_viol = eval_224["lower_violation_pct"]
    print(f"  - Blind Test Set Overall Coverage at k=2.24: {blind_cov_224:.1f}% (Wilson 95% CI: [{eval_224['wilson_score_95_ci'][0]:.1f}%, {eval_224['wilson_score_95_ci'][1]:.1f}%])")
    print(f"  - Critical Lower-Bound Violation Rate:       {blind_low_viol:.1f}% (Targets genuinely closer than safety lower bound)")
    print(f"  - Upper-Bound Violation Rate (Efficiency):   {eval_224['upper_violation_pct']:.1f}%")
    
    if blind_cov_224 >= 94.0:
        print("  - FALSIFICATION RESULT: V3.0.4 2D Rice uncertainty calibration GENERALIZES OUT-OF-SAMPLE.")
        print(f"    Coverage remained rock-solid ({blind_cov_224:.1f}% >= 94.0%) despite anisotropic sensor noise.")
        falsified = False
    else:
        print(f"  - FALSIFICATION RESULT: V3.0.4 claims FALSIFIED! True coverage fell to {blind_cov_224:.1f}%.")
        falsified = True

    out_dir = Path(WORKSPACE_ROOT) / "safety_backfire_v3/outputs/v3_0_5"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    output_data = {
        "calib_optimal_k": calib_optimal_k,
        "k_sweep": sweep_results,
        "production_eval_k_2_24": eval_224,
        "baseline_eval_k_1_96": eval_196,
        "optimal_eval": eval_optimal,
        "falsified": falsified
    }
    
    with open(out_dir / "uncertainty_red_team_metrics.json", "w") as f:
        json.dump(output_data, f, indent=2)
        
    print(f"\n[SUCCESS] Uncertainty Red Team Suite Completed! Saved to {out_dir / 'uncertainty_red_team_metrics.json'}")
    return output_data

if __name__ == "__main__":
    run_uncertainty_red_team_suite()
