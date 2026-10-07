"""
V2.9 Red-Team Test: Metric TTC & Closest Point of Approach (CPA) Audit

Exposes the 1D Range-Rate TTC flaw where non-colliding crossing paths
are falsely classified as impending collisions due to momentary distance decrease.
"""
import sys
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT))

from core.kinematics import compute_metric_ttc

def compute_cpa_distance(p_pos, f_pos, p_vel, f_vel):
    """Computes true 2D Closest Point of Approach (CPA) / Miss-Distance."""
    # r(t) = (p0 - f0) + (vp - vf)*t = r0 + v_rel * t
    r0_x = p_pos[0] - f_pos[0]
    r0_y = p_pos[1] - f_pos[1]
    
    # Relative velocity of person relative to forklift
    dv_x = p_vel[0] - f_vel[0]
    dv_y = p_vel[1] - f_vel[1]
    
    v_sq = dv_x**2 + dv_y**2
    if v_sq < 1e-6:
        return math.hypot(r0_x, r0_y), 0.0 # Stationary relative to each other
        
    t_cpa = -(r0_x * dv_x + r0_y * dv_y) / v_sq
    if t_cpa <= 0:
        return math.hypot(r0_x, r0_y), 0.0 # Moving apart, closest was in the past
        
    cpa_x = r0_x + dv_x * t_cpa
    cpa_y = r0_y + dv_y * t_cpa
    miss_distance = math.hypot(cpa_x, cpa_y)
    return miss_distance, t_cpa

def test_ttc_cpa():
    print("\n=== V2.9 Red-Team: Metric TTC vs CPA Geometry Audit ===")
    failures = []
    tests_run = 0

    # Scenario 1: Head-on Collision Course (True Positive)
    tests_run += 1
    p_pos = (5.0, 0.0)
    f_pos = (0.0, 0.0)
    p_vel = (-1.0, 0.0) # Moving west at 1 m/s
    f_vel = (1.5, 0.0)  # Moving east at 1.5 m/s
    d = 5.0
    res = compute_metric_ttc(p_pos, f_pos, p_vel, f_vel, d)
    miss_dist, t_cpa = compute_cpa_distance(p_pos, f_pos, p_vel, f_vel)
    
    if res["ttc_status"] != "VALID" or res["ttc_sec"] != 2.0:
        failures.append(f"TTC-01 FAILED: True head-on collision failed TTC: {res}")
    else:
        print(f"  [PASS] TTC-01: Head-on collision correctly detected (TTC={res['ttc_sec']}s, Miss-Distance={miss_dist:.2f}m).")

    # Scenario 2B: Crossing Paths where distance is closing but Miss-Distance > 6.0m
    # Forklift at (0, 2) moving South at 1.0 m/s (crosses origin at t=2.0s)
    # Person at (10, 0) moving West at 1.0 m/s (crosses origin at t=10.0s)
    p_pos2b = (10.0, 0.0)
    f_pos2b = (0.0, 2.0)
    p_vel2b = (-1.0, 0.0)
    f_vel2b = (0.0, -1.0)
    d2b = math.hypot(10.0, -2.0) # 10.20m
    
    res2b = compute_metric_ttc(p_pos2b, f_pos2b, p_vel2b, f_vel2b, d2b)
    miss_dist2b, t_cpa2b = compute_cpa_distance(p_pos2b, f_pos2b, p_vel2b, f_vel2b)
    
    print(f"    Scenario 2B: Current Distance={d2b:.2f}m, Miss-Distance (CPA)={miss_dist2b:.2f}m")
    print(f"    compute_metric_ttc output: {res2b}")
    
    if res2b.get("ttc_status") == "VALID" and miss_dist2b > 3.0:
        failures.append(f"TTC-02 FAILED (CRITICAL): False Collision Alert! 1D range-rate TTC declared valid collision course (TTC={res2b.get('ttc_sec')}s) when miss-distance is {miss_dist2b:.2f}m (no collision occurs)!")
    else:
        print("  [PASS] TTC-02: Non-colliding crossing path rejected from TTC.")

    # Scenario 3: Man Down / Crouching Person Aspect Ratio Gate Failure
    tests_run += 1
    from core.observation_gate import ObservationIntegrityGate
    gate = ObservationIntegrityGate()
    # A person lying on the ground: width 180px, height 80px (aspect = 80/180 = 0.44)
    # Keypoints missing due to dust/shadow
    man_down_dec = gate.evaluate("person", [100, 100, 280, 180], keypoints=None, conf=0.7)
    if man_down_dec.safety_eligible == False:
        failures.append(f"OBS-01 FAILED (CRITICAL): Man-down / fallen worker (aspect=0.44) completely erased from safety eligibility: {man_down_dec.reason}!")
    else:
        print("  [PASS] OBS-01: Man-down worker preserved as safety eligible.")

    print(f"\nCompleted {tests_run} TTC/CPA/Geometry checks. Discovered {len(failures)} failures.")
    for f in failures:
        print(f"  * {f}")
    return failures

if __name__ == "__main__":
    failures = test_ttc_cpa()
    if failures:
        print("\nTTC/CPA AUDIT RESULT: FAILURES DETECTED")
        sys.exit(1)
    else:
        print("\nTTC/CPA AUDIT RESULT: ALL PASSED")
        sys.exit(0)
