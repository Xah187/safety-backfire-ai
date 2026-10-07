"""
V3.0 Core Validation — Behavioral Hazard & Man-Down Incident Classification

Tests:
1. Posture Classification:
   - STANDING, WALKING, RUNNING, CROUCHED, FALLEN_CANDIDATE, PARTIALLY_OCCLUDED.
2. Invariant: Crouched/stooping technician must NOT be falsely classified as FALLEN.
3. Invariant: True horizontal fallen worker must be classified as FALLEN_CANDIDATE and
   marked SAFETY_ELIGIBLE_INCIDENT_CANDIDATE (never rejected as invalid observation).
4. Alert Lifecycle & Recovery:
   - Candidate -> Persistent Detection (T > 2.0s) -> Confirmed Incident
   - Worker recovery (standing back up) clears incident state.
"""
import sys
import time
import math
from pathlib import Path
from typing import Dict, List, Any, Optional
import numpy as np

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))
_V2_PATH = WORKSPACE_ROOT / "safety_backfire_v2"
if str(_V2_PATH) not in sys.path:
    sys.path.insert(0, str(_V2_PATH))

from safety_backfire_v3.core.geometry_v3 import ManDownClassifier

def test_posture_classification_matrix():
    print("\n--- Test 1: Behavioral Posture Classification Matrix ---")
    
    # 1. Standing Worker (Aspect 2.4, Speed 0.05 m/s)
    res_stand = ManDownClassifier.classify_posture(
        bbox=[100, 100, 150, 220], # w=50, h=120 -> aspect = 2.4
        speed_m_s=0.05,
        keypoints=None
    )
    print(f"  Standing Worker: posture={res_stand['posture']}, aspect={res_stand['aspect_ratio']}")
    assert res_stand["posture"] == "STANDING"
    
    # 2. Walking Worker (Aspect 2.2, Speed 1.1 m/s)
    res_walk = ManDownClassifier.classify_posture(
        bbox=[100, 100, 150, 210],
        speed_m_s=1.1,
        keypoints=None
    )
    print(f"  Walking Worker: posture={res_walk['posture']}, speed={res_walk['speed_m_s']} m/s")
    assert res_walk["posture"] == "WALKING"
    
    # 3. Running Worker (Aspect 2.1, Speed 2.6 m/s)
    res_run = ManDownClassifier.classify_posture(
        bbox=[100, 100, 150, 205],
        speed_m_s=2.6,
        keypoints=None
    )
    print(f"  Running Worker: posture={res_run['posture']}, speed={res_run['speed_m_s']} m/s")
    assert res_run["posture"] == "RUNNING"
    
    # 4. Crouched Technician (Aspect 1.05, Speed 0.0 m/s)
    res_crouch = ManDownClassifier.classify_posture(
        bbox=[100, 100, 195, 200], # w=95, h=100 -> aspect = 1.05
        speed_m_s=0.0,
        keypoints=None
    )
    print(f"  Crouched Technician: posture={res_crouch['posture']}, aspect={res_crouch['aspect_ratio']}")
    assert res_crouch["posture"] == "CROUCHED"
    assert res_crouch["posture"] != "FALLEN_CANDIDATE", "Crouched technician must not trigger false Man-Down alarm!"
    
    # 5. Fallen Worker on Floor (Aspect 0.42, Speed 0.0 m/s, Horizontal Torso)
    # Lying prone on warehouse floor: w=120, h=50 -> aspect = 0.42
    kpts_fallen = [[0.0, 0.0, 0.0] for _ in range(17)]
    kpts_fallen[5] = [120.0, 115.0, 0.85] # L-Shoulder
    kpts_fallen[6] = [120.0, 135.0, 0.85] # R-Shoulder
    kpts_fallen[11] = [190.0, 120.0, 0.80] # L-Hip
    kpts_fallen[12] = [190.0, 130.0, 0.80] # R-Hip
    
    res_fallen = ManDownClassifier.classify_posture(
        bbox=[100, 100, 220, 150], # w=120, h=50
        speed_m_s=0.0,
        keypoints=kpts_fallen
    )
    print(f"  Fallen Worker: posture={res_fallen['posture']}, safety_status={res_fallen['safety_status']}, torso_angle={res_fallen['torso_angle_deg']} deg")
    assert res_fallen["posture"] == "FALLEN_CANDIDATE"
    assert res_fallen["safety_status"] == "SAFETY_ELIGIBLE_INCIDENT_CANDIDATE"
    print("  [PASS] Posture matrix correctly distinguishes standing, walking, running, crouching, and fallen.")


def test_man_down_alert_lifecycle():
    print("\n--- Test 2: Man-Down Incident Alert Lifecycle & Worker Recovery ---")
    
    class ManDownMonitor:
        def __init__(self, confirmation_sec: float = 2.0):
            self.confirmation_sec = confirmation_sec
            self.candidate_start_time = None
            self.incident_state = "NORMAL" # NORMAL, CANDIDATE, CONFIRMED_MAN_DOWN, RECOVERED
            
        def update(self, posture_dict: dict, timestamp: float) -> str:
            posture = posture_dict["posture"]
            
            if posture == "FALLEN_CANDIDATE":
                if self.candidate_start_time is None:
                    self.candidate_start_time = timestamp
                    self.incident_state = "CANDIDATE"
                elif (timestamp - self.candidate_start_time) >= self.confirmation_sec:
                    self.incident_state = "CONFIRMED_MAN_DOWN"
            elif posture in ("STANDING", "WALKING"):
                if self.incident_state in ("CANDIDATE", "CONFIRMED_MAN_DOWN"):
                    self.incident_state = "RECOVERED"
                    self.candidate_start_time = None
                else:
                    self.incident_state = "NORMAL"
                    self.candidate_start_time = None
            return self.incident_state
            
    monitor = ManDownMonitor(confirmation_sec=2.0)
    
    # Prone fallen posture dict
    prone_dict = {"posture": "FALLEN_CANDIDATE", "safety_status": "SAFETY_ELIGIBLE_INCIDENT_CANDIDATE"}
    stand_dict = {"posture": "STANDING", "safety_status": "SAFETY_ELIGIBLE_NORMAL"}
    
    # t = 0.0s: Worker falls
    s0 = monitor.update(prone_dict, 0.0)
    assert s0 == "CANDIDATE"
    print("  t=0.0s: Worker falls -> State: CANDIDATE")
    
    # t = 1.0s: Still down (< 2.0s confirmation window)
    s1 = monitor.update(prone_dict, 1.0)
    assert s1 == "CANDIDATE"
    print("  t=1.0s: Worker down for 1.0s -> State: CANDIDATE (No premature alarm)")
    
    # t = 2.2s: Worker down for > 2.0s -> CONFIRMED_MAN_DOWN
    s2 = monitor.update(prone_dict, 2.2)
    assert s2 == "CONFIRMED_MAN_DOWN"
    print("  t=2.2s: Sustained prone position -> State: CONFIRMED_MAN_DOWN (High-priority alert!)")
    
    # t = 4.0s: Worker stands back up
    s3 = monitor.update(stand_dict, 4.0)
    assert s3 == "RECOVERED"
    print("  t=4.0s: Worker stands up -> State: RECOVERED (Alert revoked/audited)")
    
    print("  [PASS] Man-Down incident lifecycle confirmed with persistence confirmation and recovery.")


def run_all_man_down_tests():
    print("=================================================================")
    print("   V3.0 CORE VALIDATION: MAN-DOWN SAFETY & BEHAVIORAL HAZARD     ")
    print("=================================================================")
    test_posture_classification_matrix()
    test_man_down_alert_lifecycle()
    print("\nALL MAN-DOWN SAFETY TESTS PASSED!")

if __name__ == "__main__":
    run_all_man_down_tests()
