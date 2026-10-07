"""
V2.8.4 — Adversarial Tests for Observation Integrity & Safety Input Gate

Tests the ObservationIntegrityGate and TrackManager's Safety Eligibility contract.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT))

from core.track_manager import TrackManager, TrackState
from core.observation_gate import ObservationValidity

# Helpers
def make_forklift(t_id):
    return {"id": t_id, "class": "forklift", "conf": 0.9, "px": (10,10), "bbox": [0,0,100,100]}

def make_person(t_id, conf, height, pose_visible_count):
    # Width will be height / 2.5 (tall aspect ratio)
    width = height / 2.5
    kpts = [[0, 0, 0.9]] * pose_visible_count # Mock high conf keypoints
    return {
        "id": t_id, 
        "class": "person", 
        "conf": conf, 
        "px": (50, 50), 
        "bbox": [0, 0, width, height],
        "keypoints": kpts
    }

def make_false_person(t_id, conf, height):
    # No keypoints!
    width = height / 1.5 # Boxy aspect
    return {
        "id": t_id, 
        "class": "person", 
        "conf": conf, 
        "px": (50, 50), 
        "bbox": [0, 0, width, height],
        "keypoints": []
    }

class MockCalibrator:
    def pixel_to_world(self, px):
        return (px[0] * 0.1, px[1] * 0.1)

def run_test(name: str, frames_data: list, expected_eligibility: dict, expected_validity: dict):
    manager = TrackManager(strong_conf_threshold=0.35, max_prediction_frames=5)
    calibrator = MockCalibrator()
    
    final_eligible = {}
    final_validity = {}
    
    for f_idx, frame_objs in enumerate(frames_data):
        valid_objs = manager.process_tracks(f_idx + 1, (f_idx + 1)/30.0, frame_objs, calibrator)
        for obj in frame_objs:
            if obj["id"] in manager.tracks:
                final_eligible[obj["id"]] = obj.get("safety_eligible", False)
                final_validity[obj["id"]] = obj.get("observation_validity", "N/A")
                
    print(f"\n[{name}]")
    passed = True
    for t_id, exp_elig in expected_eligibility.items():
        act_elig = final_eligible.get(t_id, False)
        act_val = final_validity.get(t_id, "LOST")
        exp_val = expected_validity.get(t_id, "N/A")
        
        print(f"  Track {t_id}: Eligible={act_elig}, Validity={act_val}")
        if act_elig != exp_elig or act_val != exp_val:
            passed = False
            print(f"    -> MISMATCH! Expected Elig={exp_elig}, Val={exp_val}")
            
    if passed:
        print("  INTEGRITY CHECK: PASS ✓")
    else:
        print("  INTEGRITY CHECK: FAIL ✗")

def main():
    print("=== V2.8.4 Class Contamination Tests ===")
    
    # Test A: Forklift only
    # Expected: Forklift = Eligible (Forklifts are always valid)
    run_test("Test A: Forklift Only", 
             [[make_forklift(1)] for _ in range(5)], 
             {1: True}, {1: ObservationValidity.VALID})
             
    # Test B: Forklift + Real Person (Operator/Ped)
    # Expected: Both Eligible. Person has 10 pose kpts.
    run_test("Test B: Real Person", 
             [[make_forklift(1), make_person(2, 0.8, 400, 10)] for _ in range(5)], 
             {1: True, 2: True}, {1: ObservationValidity.VALID, 2: ObservationValidity.VALID})

    # Test D: Forklift + False Person Detection (Large box, 0 kpts)
    # Expected: False person is INVALID and NOT Eligible.
    run_test("Test D: False Person Contamination (Large)", 
             [[make_forklift(1), make_false_person(3, 0.6, 500)] for _ in range(5)], 
             {1: True, 3: False}, {1: ObservationValidity.VALID, 3: ObservationValidity.INVALID})
             
    # Test E: Small/Distant person (No pose, but small box and valid aspect)
    # Expected: Person is WEAK, but Eligible.
    small_distant = {
        "id": 4, "class": "person", "conf": 0.4, "px": (50,50), 
        "bbox": [0,0, 50, 150], "keypoints": [] # Aspect 3.0, height 150
    }
    run_test("Test E: Distant Person (Small box)", 
             [[make_forklift(1), small_distant] for _ in range(5)], 
             {1: True, 4: True}, {1: ObservationValidity.VALID, 4: ObservationValidity.WEAK})

if __name__ == "__main__":
    main()
