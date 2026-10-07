import os
from pathlib import Path

def run_all_tests():
    test_dir = Path(__file__).resolve().parent
    tests = [
        "test_event_engine.py",
        "test_risk_engine.py",
        "test_geometry.py",
        "test_kinematics.py",
        "test_trajectory.py",
        "test_semantics.py",
        "test_severity.py",
        "test_evidence.py",
        "test_comparison.py",
        "test_redistribution.py",
        "test_intervention.py",
        "test_counterfactual.py",
        "test_decision.py",
        "test_explainability.py",
        "test_output.py"
    ]
    
    all_passed = True
    for test in tests:
        test_path = test_dir / test
        print(f"Running {test}...")
        ret = os.system(f"python {test_path}")
        if ret != 0:
            print(f"FAILED: {test}")
            all_passed = False
            
    if all_passed:
        print("\nAll V2 Engine tests passed successfully! Tracking, Geometry, Event logic, and Comparison are fully validated.")
    else:
        print("\nSome tests failed. Check logs.")
        exit(1)

if __name__ == "__main__":
    run_all_tests()
