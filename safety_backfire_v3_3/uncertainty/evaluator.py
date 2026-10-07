"""
uncertainty/evaluator.py
V3.3 Out-of-Sample Uncertainty Validation Engine.
Enforces strict pre-lock of calibration factor k before out-of-sample evaluation.
Generates stratified coverage metrics and records failure cases.
"""

import math
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

@dataclass
class UncertaintyPoint:
    point_id: str
    dx: float  # Ground error x (meters)
    dy: float  # Ground error y (meters)
    sigma_x: float  # Estimated standard deviation x
    sigma_y: float  # Estimated standard deviation y
    distance_m: float
    illumination_lux: float
    camera_pitch_deg: float
    occlusion_state: str  # "NONE", "PARTIAL", "HEAVY"

    @property
    def mahalanobis_sq(self) -> float:
        # Assuming uncorrelated diagonal covariance for 2D ground error
        var_x = max(self.sigma_x ** 2, 1e-6)
        var_y = max(self.sigma_y ** 2, 1e-6)
        return (self.dx ** 2) / var_x + (self.dy ** 2) / var_y

    def is_covered(self, k: float) -> bool:
        return self.mahalanobis_sq <= (k ** 2)

class UncertaintyEvaluator:
    def __init__(self):
        self.locked_k: Optional[float] = None
        self.calibration_record: Optional[Dict[str, Any]] = None

    def fit_and_lock_k(self, calibration_points: List[UncertaintyPoint], target_coverage: float = 0.95) -> float:
        """Fit empirical k on calibration split and permanently lock it."""
        if not calibration_points:
            raise ValueError("Calibration split cannot be empty.")

        d_sq_list = sorted([p.mahalanobis_sq for p in calibration_points])
        idx = min(int(math.ceil(target_coverage * len(d_sq_list))) - 1, len(d_sq_list) - 1)
        k_val = round(math.sqrt(d_sq_list[idx]), 2)

        # Enforce minimum floor
        k_val = max(k_val, 2.0)
        self.locked_k = k_val

        covered_count = sum(1 for p in calibration_points if p.is_covered(k_val))
        in_sample_cov = round(covered_count / len(calibration_points), 4)

        self.calibration_record = {
            "locked_factor_k": self.locked_k,
            "target_coverage": target_coverage,
            "calibration_sample_size": len(calibration_points),
            "in_sample_calibration_coverage": in_sample_cov,
            "status": "CALIBRATION_LOCKED_DO_NOT_ALTER",
            "mathematical_note": "k is empirically calibrated on CALIBRATION split and locked before blind evaluation."
        }
        return self.locked_k

    def evaluate_out_of_sample(self, eval_points: List[UncertaintyPoint]) -> Dict[str, Any]:
        """Evaluate locked k on unseen out-of-sample data with zero parameter tuning."""
        if self.locked_k is None:
            raise RuntimeError("Cannot evaluate out-of-sample coverage before factor k is fitted and locked!")

        k = self.locked_k
        n_total = len(eval_points)
        if n_total == 0:
            raise ValueError("Evaluation split is empty.")

        covered_points = [p for p in eval_points if p.is_covered(k)]
        failure_points = [p for p in eval_points if not p.is_covered(k)]

        overall_cov = round(len(covered_points) / n_total, 4)
        undercoverage_freq = round(len(failure_points) / n_total, 4)

        # Strata: Distance
        strata_dist = {"NEAR_0_4M": [], "MID_4_8M": [], "FAR_GT_8M": []}
        for p in eval_points:
            if p.distance_m <= 4.0:
                strata_dist["NEAR_0_4M"].append(p)
            elif p.distance_m <= 8.0:
                strata_dist["MID_4_8M"].append(p)
            else:
                strata_dist["FAR_GT_8M"].append(p)

        dist_breakdown = {}
        for s_name, pts in strata_dist.items():
            if pts:
                cov = round(sum(1 for p in pts if p.is_covered(k)) / len(pts), 4)
                dist_breakdown[s_name] = {"n": len(pts), "coverage": cov}

        # Strata: Illumination
        strata_illum = {"LOW_LT_250_LUX": [], "NORMAL_GE_250_LUX": []}
        for p in eval_points:
            if p.illumination_lux < 250.0:
                strata_illum["LOW_LT_250_LUX"].append(p)
            else:
                strata_illum["NORMAL_GE_250_LUX"].append(p)

        illum_breakdown = {}
        for s_name, pts in strata_illum.items():
            if pts:
                cov = round(sum(1 for p in pts if p.is_covered(k)) / len(pts), 4)
                illum_breakdown[s_name] = {"n": len(pts), "coverage": cov}

        # Strata: Occlusion
        strata_occ = {"NONE": [], "PARTIAL": [], "HEAVY": []}
        for p in eval_points:
            strata_occ.get(p.occlusion_state, strata_occ["NONE"]).append(p)

        occ_breakdown = {}
        for s_name, pts in strata_occ.items():
            if pts:
                cov = round(sum(1 for p in pts if p.is_covered(k)) / len(pts), 4)
                occ_breakdown[s_name] = {"n": len(pts), "coverage": cov}

        results = {
            "evaluation_type": "OUT_OF_SAMPLE_VALIDATION",
            "locked_factor_k": k,
            "sample_size": n_total,
            "out_of_sample_coverage": overall_cov,
            "undercoverage_frequency": undercoverage_freq,
            "coverage_by_condition": {
                "distance_strata": dist_breakdown,
                "illumination_strata": illum_breakdown,
                "occlusion_strata": occ_breakdown
            },
            "failure_case_count": len(failure_points),
            "failure_cases": [
                {
                    "point_id": p.point_id,
                    "distance_m": p.distance_m,
                    "illumination_lux": p.illumination_lux,
                    "occlusion_state": p.occlusion_state,
                    "mahalanobis_sq": round(p.mahalanobis_sq, 4),
                    "threshold_k_sq": round(k ** 2, 4)
                } for p in failure_points[:15]
            ]
        }
        return results

    def save_artifacts(self, out_dir: Path, eval_results: Dict[str, Any]):
        out_dir.mkdir(parents=True, exist_ok=True)
        if self.calibration_record:
            with open(out_dir / "calibration_record.json", "w") as f:
                json.dump(self.calibration_record, f, indent=2)

        with open(out_dir / "blind_coverage_metrics.json", "w") as f:
            json.dump({
                "locked_k": eval_results["locked_factor_k"],
                "sample_size": eval_results["sample_size"],
                "out_of_sample_coverage": eval_results["out_of_sample_coverage"],
                "undercoverage_frequency": eval_results["undercoverage_frequency"]
            }, f, indent=2)

        with open(out_dir / "coverage_by_condition.json", "w") as f:
            json.dump(eval_results["coverage_by_condition"], f, indent=2)

        with open(out_dir / "coverage_failure_cases.json", "w") as f:
            json.dump({
                "failure_case_count": eval_results["failure_case_count"],
                "failure_cases": eval_results["failure_cases"]
            }, f, indent=2)
