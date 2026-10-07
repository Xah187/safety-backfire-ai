"""
Phase 6 — TTC Validation

Validates the Kinematics engine mathematically.
Ensures TTC is correctly defined as distance / closing_speed.
Ensures edge cases (diverging, stationary) are explicitly 'null' and not synthetic values.
"""
import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT))

from core.kinematics import compute_metric_ttc

def run_ttc_validation():
    
    test_cases = [
        {
            "scenario": "Direct Approach",
            "p_pos": (0.0, 0.0), "f_pos": (10.0, 0.0),
            "p_vel": (0.0, 0.0), "f_vel": (-2.0, 0.0), # Forklift moving left at 2m/s
            "distance_m": 10.0,
            "expected_ttc": 5.0,
            "expected_status": "VALID"
        },
        {
            "scenario": "Diverging",
            "p_pos": (0.0, 0.0), "f_pos": (10.0, 0.0),
            "p_vel": (0.0, 0.0), "f_vel": (2.0, 0.0), # Forklift moving right at 2m/s
            "distance_m": 10.0,
            "expected_ttc": None,
            "expected_status": "NO_APPROACH"
        },
        {
            "scenario": "Stationary Objects",
            "p_pos": (2.0, 2.0), "f_pos": (5.0, 5.0),
            "p_vel": (0.0, 0.0), "f_vel": (0.0, 0.0),
            "distance_m": 4.24,
            "expected_ttc": None,
            "expected_status": "NO_APPROACH"
        },
        {
            "scenario": "Zero Relative Velocity (Same Direction)",
            "p_pos": (0.0, 0.0), "f_pos": (10.0, 0.0),
            "p_vel": (2.0, 0.0), "f_vel": (2.0, 0.0),
            "distance_m": 10.0,
            "expected_ttc": None,
            "expected_status": "NO_APPROACH"
        },
        {
            "scenario": "Angled Approach",
            "p_pos": (0.0, 0.0), "f_pos": (10.0, 10.0),
            "p_vel": (0.0, 0.0), "f_vel": (-1.0, -1.0),
            "distance_m": 14.14,
            "expected_ttc": 10.0, # Approach speed is sqrt(2) = 1.414, 14.14 / 1.414 = 10.0
            "expected_status": "VALID"
        }
    ]
    
    results = []
    all_passed = True
    
    for case in test_cases:
        res = compute_metric_ttc(
            case["p_pos"], case["f_pos"],
            case["p_vel"], case["f_vel"],
            case["distance_m"]
        )
        
        ttc_match = res["ttc_sec"] == case["expected_ttc"]
        status_match = res["ttc_status"] == case["expected_status"]
        
        passed = ttc_match and status_match
        if not passed:
            all_passed = False
            
        results.append({
            "scenario": case["scenario"],
            "expected_ttc": case["expected_ttc"],
            "actual_ttc": res["ttc_sec"],
            "expected_status": case["expected_status"],
            "actual_status": res["ttc_status"],
            "passed": passed
        })
        
    report = {
        "all_passed": all_passed,
        "scenarios": results
    }
    
    out_dir = ROOT / "validation" / "ttc"
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "ttc_validation.json", "w") as f:
        json.dump(report, f, indent=2)
        
    print("TTC Validation Completed.")
    print(f"All Passed: {all_passed}")
    if not all_passed:
        for r in results:
            if not r["passed"]:
                print(f"FAILED: {r['scenario']}")

if __name__ == "__main__":
    run_ttc_validation()
