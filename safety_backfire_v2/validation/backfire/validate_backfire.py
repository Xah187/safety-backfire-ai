"""
Phase 10 — Backfire Validation

Validates the final Decision Engine logic to differentiate between:
- True Backfire
- True Improvement
- Ambiguous / Poor Evidence
"""
import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT))

from validation.scenarios.validate_scenarios import (
    test_scenario_e_backfire,
    test_scenario_f_improvement,
    test_scenario_g_insufficient
)

def run_backfire_validation():
    errors = []
    
    try:
        test_scenario_e_backfire()
    except AssertionError as e:
        errors.append(str(e))
        
    try:
        test_scenario_f_improvement()
    except AssertionError as e:
        errors.append(str(e))
        
    try:
        test_scenario_g_insufficient()
    except AssertionError as e:
        errors.append(str(e))
        
    passed = len(errors) == 0
    
    report = {
        "backfire_validation_passed": passed,
        "errors": errors
    }
    
    out_dir = ROOT / "validation" / "backfire"
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "backfire_validation.json", "w") as f:
        json.dump(report, f, indent=2)
        
    print(f"Backfire Validation Passed: {passed}")
    if not passed:
        print(errors)

if __name__ == "__main__":
    run_backfire_validation()
