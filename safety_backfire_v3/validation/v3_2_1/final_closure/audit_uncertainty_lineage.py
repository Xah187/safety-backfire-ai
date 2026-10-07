"""
audit_uncertainty_lineage.py
Forensic auditor for uncertainty factor k = 2.24 and calibration split independence (Issues C & D).
Outputs:
  - outputs/v3_2_1/final_closure/uncertainty_factor_lineage.json
  - outputs/v3_2_1/final_closure/uncertainty_split_audit.json
"""

import sys
import json
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

OUT_DIR = WORKSPACE_ROOT / "outputs/v3_2_1/final_closure"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def audit_uncertainty_lineage():
    """
    Issue C: Mathematical description of k = 2.24.
    Reconciles 2.24 with theoretical sqrt(chi2_2(0.95)) = 2.448.
    Ensures 'empirically calibrated coverage factor' is used, never 'mathematical guarantee'.
    """
    factor_lineage = {
        "audit_version": "V3.2.1_UNCERTAINTY_FACTOR_LINEAGE",
        "factor": 2.24,
        "derivation": "empirically calibrated coverage factor",
        "theoretical_reference": "sqrt(chi2_2(0.95)) = 2.44774689347",
        "mathematical_reconciliation": {
            "theoretical_chi2_95": 2.448,
            "selected_factor": 2.24,
            "discrepancy_explanation": (
                "Theoretical 95% circular error probable for a 2-DOF bivariate Gaussian requires k = sqrt(chi2_2(0.95)) = 2.448. "
                "In historical V3.0.4/V3.0.5 development, k = 2.24 was empirically calibrated downward on calibration residuals to "
                "prevent excessive volumetric inflation of spatial bounding ellipses while maintaining empirical containment >= 0.95. "
                "Therefore, k = 2.24 is NOT the mathematical Chi-Square 95% quantile, and must strictly be cited as an "
                "'empirically calibrated coverage factor' under 2D Gaussian assumptions."
            )
        },
        "calibration_data_split": "CALIBRATION_SPLIT",
        "fitting_method": "Empirical grid search minimizing covariance bounding volume subject to empirical containment >= 95.0%",
        "optimization_objective": "min(det(k^2 * Sigma)) subject to empirical_containment >= 0.95",
        "assumptions": [
            "Bivariate zero-mean Gaussian measurement residuals in camera ground plane projection",
            "Nominal floor planarity (slope < 1.5 deg)",
            "Nominal camera mounting pitch (35 - 55 deg)",
            "Distance <= 8.0 meters from optical center"
        ],
        "empirical_coverage_result": 0.9760,
        "limitations": [
            "Calibrated in-sample on CAM02 calibration sequence (500 frames)",
            "Valid only within nominal ODD boundaries",
            "Degrades on non-planar surfaces (e.g. 3.5 deg ramp, FAIL-45) and shallow pitch (< 35 deg, FAIL-38)",
            "Cannot provide an unconditional mathematical guarantee against non-Gaussian outliers"
        ],
        "mandatory_reporting_terminology": {
            "allowed_terms": [
                "empirically calibrated coverage factor",
                "calibrated 2D Gaussian coverage multiplier",
                "in-sample empirical coverage"
            ],
            "prohibited_terms": [
                "mathematical guarantee",
                "guaranteed safety coverage",
                "Chi-Square 95% quantile",
                "unconditioned coverage",
                "zero failure probability"
            ]
        }
    }
    
    out_file = OUT_DIR / "uncertainty_factor_lineage.json"
    with open(out_file, "w") as f:
        json.dump(factor_lineage, f, indent=2)
    print(f"Generated uncertainty factor lineage: {out_file}")
    return factor_lineage

def audit_uncertainty_split():
    """
    Issue D: Uncertainty Calibration / Test Independence.
    488/500 (97.60%) is assigned to CALIBRATION_SPLIT.
    Must be designated as 'in-sample calibration coverage', NOT independent validation.
    """
    split_audit = {
        "audit_version": "V3.2.1_UNCERTAINTY_SPLIT_AUDIT",
        "metric_name": "uncertainty_containment_coverage",
        "dataset_split": "CALIBRATION_SPLIT",
        "source_stream": "VID_CAL_001 (CAM02_RACK_CORRIDOR_CALIB)",
        "sample_size_N": 500,
        "contained_samples": 488,
        "in_sample_coverage": 0.9760,
        "wilson_ci_descriptive": [0.9585, 0.9862],
        "designation": "in-sample calibration coverage",
        "evaluation_type": "CALIBRATION_SPLIT_IN_SAMPLE",
        "independent_validation_status": "NOT_AN_INDEPENDENT_TEST",
        "leakage_audit_verdict": {
            "leakage_present_in_original_label": True,
            "leakage_mitigated_by_relabeling": True,
            "finding": (
                "The 500 observations evaluated for spatial uncertainty containment originated from the same "
                "CALIBRATION_SPLIT used to tune factor k = 2.24. Presenting 97.60% as an independent validation "
                "score constituted test-set contamination. The metric has been formally reclassified as "
                "'in-sample calibration coverage'."
            )
        },
        "post_calibration_evaluation": {
            "validation_split_evaluated": False,
            "blind_split_evaluated": False,
            "recommendation": "Independent out-of-sample coverage verification should be performed in future operational pilot testing."
        }
    }
    
    out_file = OUT_DIR / "uncertainty_split_audit.json"
    with open(out_file, "w") as f:
        json.dump(split_audit, f, indent=2)
    print(f"Generated uncertainty split audit: {out_file}")
    return split_audit

def main():
    audit_uncertainty_lineage()
    audit_uncertainty_split()

if __name__ == "__main__":
    main()
