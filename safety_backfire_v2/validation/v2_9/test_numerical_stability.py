"""
V2.9 Red-Team Test: Numerical Stability & Schema Consistency

Audits numerical boundaries, extreme values, division-by-zero, NaN/Inf propagation,
and schema compatibility across core mathematical engines.
"""
import sys
import math
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT))

from core.geometry import GroundPlaneCalibrator
from core.kinematics import calculate_world_velocity, compute_metric_ttc
from core.risk_engine import RiskEngine
from core.event_engine_v2 import InteractionEventV2

def test_numerical_stability():
    print("\n=== V2.9 Red-Team: Numerical Stability & Schema Audit ===")
    failures = []
    tests_run = 0

    # 1. Delta-t = 0 in velocity calculation
    tests_run += 1
    vx, vy, spd = calculate_world_velocity((1.0, 2.0), (1.0, 2.0), 0.0)
    if math.isnan(spd) or math.isinf(spd):
        failures.append("NUM-01 FAILED: calculate_world_velocity produced NaN/Inf on dt=0!")
    else:
        print("  [PASS] NUM-01: dt=0 handled cleanly in calculate_world_velocity.")

    # 2. Delta-t < 0 in velocity calculation (out-of-order timestamps)
    tests_run += 1
    vx, vy, spd = calculate_world_velocity((2.0, 3.0), (1.0, 2.0), -0.04)
    if spd != 0.0:
        failures.append(f"NUM-02 FAILED: Negative dt produced non-zero velocity: {spd} m/s!")
    else:
        print("  [PASS] NUM-02: Negative dt returns zero velocity.")

    # 3. Distance = 0 in Metric TTC
    tests_run += 1
    res = compute_metric_ttc((5.0, 5.0), (5.0, 5.0), (0.0, 0.0), (1.0, 0.0), 0.0)
    if res.get("ttc_sec") is not None and (math.isnan(res["ttc_sec"]) or math.isinf(res["ttc_sec"])):
        failures.append("NUM-03 FAILED: compute_metric_ttc produced NaN/Inf when distance=0!")
    else:
        print(f"  [PASS] NUM-03: Distance=0 handled in TTC (status: {res.get('ttc_status')}).")

    # 4. Zero approach velocity in Metric TTC
    tests_run += 1
    res = compute_metric_ttc((10.0, 0.0), (0.0, 0.0), (0.0, 0.0), (-1.0, 0.0), 10.0)
    if res.get("ttc_sec") is not None:
        failures.append(f"NUM-04 FAILED: TTC calculated when objects are moving apart: {res.get('ttc_sec')}s!")
    else:
        print("  [PASS] NUM-04: Separating objects correctly assigned ttc_sec=None.")

    # 5. Horizon Point Homography Singularity
    tests_run += 1
    cal = GroundPlaneCalibrator()
    # Point near horizon / vanishing line
    world_pt = cal.pixel_to_world((640.0, -1000.0))
    if world_pt is not None:
        wx, wy = world_pt
        if math.isnan(wx) or math.isnan(wy) or math.isinf(wx) or math.isinf(wy) or abs(wx) > 1e6 or abs(wy) > 1e6:
            failures.append(f"NUM-05 FAILED: Homography produced astronomical / NaN coordinate: {world_pt}!")
        else:
            print(f"  [PASS] NUM-05: Horizon pixel handled without overflow ({world_pt}).")

    # 6. Schema Incompatibility: RiskEngine with InteractionEventV2
    tests_run += 1
    re = RiskEngine()
    evt_v2 = InteractionEventV2("EVT_SCHEMA", 1, 2, 1, 0.04, "INDEPENDENT_PEDESTRIAN")
    evt_v2.update(1, 0.04, 1.2, "DANGER", "INDEPENDENT_PEDESTRIAN")
    evt_v2.end()
    try:
        score = re.calculate_risk_exposure(evt_v2)
        print(f"  [PASS] NUM-06: RiskEngine calculated score: {score}")
    except AttributeError as e:
        failures.append(f"NUM-06 FAILED (CRITICAL): RiskEngine crashed on InteractionEventV2 due to missing attributes: {e}!")
    except Exception as e:
        failures.append(f"NUM-06 FAILED: RiskEngine crashed with unexpected exception: {e}!")

    # 7. Unbounded Velocity Spike on ID Switch
    tests_run += 1
    # If ID swaps from person at (1.0, 1.0) to person at (20.0, 20.0) in 1 frame (0.04s)
    vx, vy, spd = calculate_world_velocity((20.0, 20.0), (1.0, 1.0), 0.04)
    # 26.87m in 0.04s = 671.75 m/s (Mach 2!)
    if spd > 10.0:
        failures.append(f"NUM-07 FAILED: ID switch jump produced unphysical velocity: {spd:.2f} m/s without unbounded clamp!")
    else:
        print("  [PASS] NUM-07: Unphysical velocity was clamped.")

    print(f"\nCompleted {tests_run} numerical/schema checks. Discovered {len(failures)} failures.")
    for f in failures:
        print(f"  * {f}")
    return failures

if __name__ == "__main__":
    failures = test_numerical_stability()
    if failures:
        print("\nNUMERICAL AUDIT RESULT: FAILURES DETECTED")
        sys.exit(1)
    else:
        print("\nNUMERICAL AUDIT RESULT: ALL PASSED")
        sys.exit(0)
