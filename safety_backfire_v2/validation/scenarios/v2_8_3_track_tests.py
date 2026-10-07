"""
V2.8.3 — Adversarial Tests for Track Integrity Gate

Tests the TrackManager's ability to distinguish between OBSERVED, PREDICTED, 
and STALE tracks based on confidence and drift logic.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT))

from core.track_manager import TrackManager, TrackState

def make_obj(t_id, conf, px):
    return {"id": t_id, "class": "person", "conf": conf, "px": px, "bbox": [0,0,10,10]}

class MockCalibrator:
    def pixel_to_world(self, px):
        # 1 px = 0.1m for simplicity
        return (px[0] * 0.1, px[1] * 0.1)

def run_test(name: str, frames_data: list, expected_states: dict):
    manager = TrackManager(strong_conf_threshold=0.35, max_prediction_frames=5, max_drift_speed_m_s=8.0)
    calibrator = MockCalibrator()
    
    for f_idx, frame_objs in enumerate(frames_data):
        manager.process_tracks(f_idx + 1, (f_idx + 1)/30.0, frame_objs, calibrator)
                
    print(f"\n[{name}]")
    passed = True
    for t_id, exp_state in expected_states.items():
        act_state = manager.tracks[t_id]["state"] if t_id in manager.tracks else "LOST"
        print(f"  Track {t_id}: {act_state} (Expected: {exp_state})")
        if act_state != exp_state:
            passed = False
            
    if passed:
        print("  INTEGRITY CHECK: PASS ✓")
    else:
        print("  INTEGRITY CHECK: FAIL ✗")

def main():
    print("=== V2.8.3 Track Integrity Gate Tests ===")
    
    # Test A: Short drop to weak confidence
    # 3 frames strong, 3 frames weak
    frames_A = []
    for i in range(3): frames_A.append([make_obj(1, 0.8, (10, 10))])
    for i in range(3): frames_A.append([make_obj(1, 0.2, (10, 10))])
    run_test("Test A: Short occlusion -> PREDICTED", frames_A, {1: TrackState.PREDICTED})
    
    # Test B: Long drop to weak confidence (Ghost Track)
    # 3 frames strong, 6 frames weak
    frames_B = []
    for i in range(3): frames_B.append([make_obj(2, 0.8, (10, 10))])
    for i in range(6): frames_B.append([make_obj(2, 0.2, (10, 10))])
    run_test("Test B: Long occlusion -> STALE", frames_B, {2: TrackState.STALE})
    
    # Test C: Track Drift
    # Moves normally, then jumps 100 pixels in 1 frame (10 meters / 0.033s = 300 m/s > 8.0 m/s)
    # Note: If confidence is high, it might be a real jump? 
    # Actually, we apply drift check to all tracks, if it jumps it's drift.
    frames_C = []
    frames_C.append([make_obj(3, 0.8, (10, 10))])
    frames_C.append([make_obj(3, 0.2, (11, 10))]) # Normal move
    frames_C.append([make_obj(3, 0.2, (111, 10))]) # Jump!
    run_test("Test C: Prediction Drift -> STALE", frames_C, {3: TrackState.STALE})
    
    # Test D: Complete Disappearance
    frames_D = []
    frames_D.append([make_obj(4, 0.8, (10, 10))])
    frames_D.append([]) # Empty frame
    run_test("Test D: Total Disappearance -> LOST", frames_D, {4: "LOST"})

if __name__ == "__main__":
    main()
