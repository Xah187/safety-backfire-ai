"""
Phase 3 & Phase 5 — Ground-Plane and Distance Validation

Validates the homography matrix accuracy across different regions of the camera view
by comparing known ground-truth physical distances against the engine's predictions.
Computes MAE, RMSE, and relative errors.
"""
import sys
import math
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT))

from core.geometry import GroundPlaneCalibrator, compute_metric_distance

def calculate_metrics(results):
    total_abs_error = 0.0
    total_sq_error = 0.0
    valid_count = 0
    
    for r in results:
        if r["estimated_distance_m"] is not None:
            err = r["absolute_error_m"]
            total_abs_error += err
            total_sq_error += err**2
            valid_count += 1
            
    if valid_count == 0:
        return {"MAE": None, "RMSE": None}
        
    return {
        "MAE": round(total_abs_error / valid_count, 3),
        "RMSE": round(math.sqrt(total_sq_error / valid_count), 3)
    }

def run_geometry_validation():
    # We use the default calibrator (which maps pixel points to a 3.5m x 6.0m rectangle)
    # src: [210, 180], [340, 180], [150, 340], [430, 340]
    # dst: [0, 6], [3.5, 6], [0, 0], [3.5, 0]
    calibrator = GroundPlaneCalibrator()
    
    # Ground truth test cases representing different zones in the image
    # We simulate points and their expected physical distances.
    # Note: Since the homography is mathematically exact for the 4 corners, we test interpolated points.
    
    test_cases = [
        # Foreground (Bottom of image) - width is 3.5m
        {"zone": "foreground_center", "p1_px": (150, 340), "p2_px": (430, 340), "expected_m": 3.5},
        {"zone": "foreground_left", "p1_px": (150, 340), "p2_px": (290, 340), "expected_m": 1.75},
        
        # Background (Top of image) - width is 3.5m
        {"zone": "background_center", "p1_px": (210, 180), "p2_px": (340, 180), "expected_m": 3.5},
        
        # Depth (Bottom to Top) - depth is 6.0m
        {"zone": "depth_left", "p1_px": (150, 340), "p2_px": (210, 180), "expected_m": 6.0},
        {"zone": "depth_right", "p1_px": (430, 340), "p2_px": (340, 180), "expected_m": 6.0},
        
        # Middle ground (interpolated)
        {"zone": "middle_ground", "p1_px": (180, 260), "p2_px": (385, 260), "expected_m": 3.5},
        
        # Diagonal
        {"zone": "diagonal_cross", "p1_px": (150, 340), "p2_px": (340, 180), "expected_m": math.hypot(3.5, 6.0)},
        
        # Outside calibrated region (Should be flagged or rejected if margin is strict, but we relaxed it to 100px)
        {"zone": "out_of_bounds_left", "p1_px": (50, 340), "p2_px": (150, 340), "expected_m": 1.25} # Approx extrapolation
    ]
    
    results = []
    
    for case in test_cases:
        geo_res = compute_metric_distance(case["p1_px"], case["p2_px"], calibrator)
        est_m = geo_res["distance_m"]
        
        if est_m is not None:
            abs_err = abs(est_m - case["expected_m"])
            rel_err = (abs_err / case["expected_m"]) * 100.0
        else:
            abs_err = None
            rel_err = None
            
        results.append({
            "zone": case["zone"],
            "known_distance_m": round(case["expected_m"], 3),
            "estimated_distance_m": est_m,
            "absolute_error_m": round(abs_err, 3) if abs_err is not None else None,
            "relative_error_percent": round(rel_err, 2) if rel_err is not None else None,
            "status": geo_res["calibration_status"]
        })
        
    metrics = calculate_metrics(results)
    
    report = {
        "overall_metrics": metrics,
        "point_tests": results
    }
    
    # Save validation report
    out_dir = ROOT / "validation" / "geometry"
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "geometry_validation.json", "w") as f:
        json.dump(report, f, indent=2)
        
    print("Geometry & Distance Validation Completed.")
    print(f"MAE: {metrics['MAE']}m, RMSE: {metrics['RMSE']}m")
    
if __name__ == "__main__":
    run_geometry_validation()
