"""
V2.6 — Regression Runner

Runs all critical validation scenarios to ensure no regressions
were introduced by recent architectural changes.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))


def run_regressions():
    print("=== V2.6 Final Regression Runner ===\n")
    
    passed_all = True
    
    # 1. V2.5 Operator Scenarios
    print("--- 1. Running V2.5 Operator/Pedestrian Scenarios ---")
    try:
        from validation.scenarios.v2_5_operator_scenarios import run_all as run_v25
        results_v25, p, f = run_v25()
        if f > 0: passed_all = False
    except Exception as e:
        print(f"FAILED to run V2.5 scenarios: {e}")
        passed_all = False

    # 2. V2.6 Fast-Track Scenarios
    print("\n--- 2. Running V2.6 Fast-Track Validation ---")
    try:
        from validation.scenarios.v2_6_fast_track_tests import main as run_v26_fast
        run_v26_fast()
        # Visual check in output
    except Exception as e:
        print(f"FAILED to run V2.6 fast-track tests: {e}")
        passed_all = False
        
    # 3. V2.6 Event Preservation
    print("\n--- 3. Running V2.6 Event Preservation Test ---")
    try:
        from validation.scenarios.v2_6_event_preservation import run_preservation_test
        run_preservation_test()
    except Exception as e:
        print(f"FAILED to run V2.6 event preservation: {e}")
        passed_all = False

    print("\n==============================================")
    if passed_all:
        print("  REGRESSION STATUS: PASS ✓")
    else:
        print("  REGRESSION STATUS: FAIL ✗")
    print("==============================================")


if __name__ == "__main__":
    run_regressions()
