"""
V2.9 Red-Team Test: Adversarial Failure Injection Suite

Injects controlled synthetic perturbations to observe failure propagation:
1. FI-01: Temporal Frame Drops (Simulating camera buffer stutter).
2. FI-02: Bounding Box Jitter (Interpreted as high-speed motion).
3. FI-03: Sudden Pose Dropout (Worker facing away or in shadow).
4. FI-04: False Forklift Chassis Hallucination Injection.
5. FI-05: ID Switch Injection during active event.
"""
import sys
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT))

from core.track_manager import TrackManager, TrackState
from core.observation_gate import ObservationIntegrityGate, ObservationValidity
from core.event_engine_v2 import EventEngineV2
from core.geometry import load_default_calibrator

def test_failure_injection():
    print("\n=== V2.9 Red-Team: Adversarial Failure Injection Audit ===")
    failures = []
    tests_run = 0

    calibrator = load_default_calibrator()

    # FI-01: Temporal Frame Drop Injection
    # A vehicle moving at 2 m/s experiences a 10-frame drop (0.4s missing).
    # Does TrackManager falsely declare drift (> 8 m/s) or handle dt?
    tests_run += 1
    tm1 = TrackManager(strong_conf_threshold=0.35, max_prediction_frames=5)
    # Frame 1 at t=0.0s, ground pos (0, 0)
    tm1.process_tracks(1, 0.04, [{"id": 1, "class": "forklift", "bbox": [500, 500, 600, 600], "conf": 0.9, "px": (550, 600)}], calibrator)
    # Jump to Frame 12 at t=0.48s (10 dropped frames), vehicle moved 0.8m
    out_drop = tm1.process_tracks(12, 0.48, [{"id": 1, "class": "forklift", "bbox": [500, 520, 600, 620], "conf": 0.9, "px": (550, 620)}], calibrator)
    if out_drop[0]["track_state"] == TrackState.STALE:
        failures.append("FI-01 FAILED: Dropped frames caused legitimate track to be falsely killed as STALE/Drift!")
    else:
        print(f"  [PASS] FI-01: Dropped frames handled (speed: {out_drop[0]['speed_m_s']:.2f} m/s).")

    # FI-02: Bounding Box Jitter
    # Stationary person (ground truth speed 0.0 m/s) with 20px box jitter
    tests_run += 1
    tm2 = TrackManager()
    speeds = []
    for f in range(1, 15):
        # Oscillate pixel y between 600 and 620
        y = 600 if f % 2 == 0 else 620
        out = tm2.process_tracks(f, f * 0.04, [{"id": 2, "class": "person", "bbox": [200, 500, 250, y], "conf": 0.8, "px": (225, y)}], calibrator)
        speeds.append(out[0]["speed_m_s"])
    
    avg_speed = sum(speeds) / len(speeds)
    print(f"    FI-02: Stationary worker with 20px jitter produced avg speed: {avg_speed:.2f} m/s")
    if avg_speed > 0.8:
        failures.append(f"FI-02 FAILED (HIGH): 20px pixel jitter created false velocity of {avg_speed:.2f} m/s (exceeds 0.8 m/s operator threshold)!")
    else:
        print("  [PASS] FI-02: Jitter smoothing kept velocity below threshold.")

    # FI-03: Sudden Pose Dropout on Active Track
    # Worker had strong pose for 5 frames, then pose drops to 0 keypoints for 3 frames (occlusion)
    tests_run += 1
    gate = ObservationIntegrityGate()
    hist = {"track_age": 10, "prior_pose_count": 5}
    # Evaluated with 0 keypoints
    dec = gate.evaluate("person", [100, 100, 150, 250], keypoints=None, conf=0.8, track_history=hist)
    if dec.validity == ObservationValidity.INVALID or dec.safety_eligible == False:
        failures.append("FI-03 FAILED: Temporary pose dropout invalidated an established human track!")
    else:
        print(f"  [PASS] FI-03: Pose dropout preserved via track history (validity={dec.validity}, eligible={dec.safety_eligible}).")

    # FI-04: False Forklift Chassis Hallucination
    # Injection of a bulky chassis detection (P18/P89) on vehicle
    tests_run += 1
    dec_ghost = gate.evaluate("person", [100, 100, 500, 450], keypoints=None, conf=0.25, 
                              track_history={"track_age": 1, "prior_pose_count": 0},
                              spatial_context={"vehicle_overlap": 0.85})
    if dec_ghost.validity != ObservationValidity.INVALID:
        failures.append(f"FI-04 FAILED: Bulky vehicle chassis hallucination NOT rejected by gate: {dec_ghost.validity}!")
    else:
        print("  [PASS] FI-04: Vehicle chassis hallucination correctly isolated as INVALID.")

    # FI-05: ID Switch during active event
    # Person 10 is interacting with Forklift 20 in DANGER zone.
    # At frame 5, tracker switches Person 10's ID to Person 11.
    tests_run += 1
    ee = EventEngineV2(max_gap_frames=15)
    for f in range(1, 5):
        ee.process_frame_interactions(f, f * 0.04, [{"person_id": 10, "forklift_id": 20, "distance_meters": 1.0, "zone_status": "DANGER", "relation": "INDEPENDENT_PEDESTRIAN"}])
    
    # ID Switch occurs at frame 5
    for f in range(5, 10):
        ee.process_frame_interactions(f, f * 0.04, [{"person_id": 11, "forklift_id": 20, "distance_meters": 1.0, "zone_status": "DANGER", "relation": "INDEPENDENT_PEDESTRIAN"}])
    
    # Both active events exist
    events = list(ee.active_events.values())
    if len(events) > 1:
        failures.append(f"FI-05 FAILED (HIGH): ID switch caused event fragmentation! Single physical interaction split into {len(events)} separate events (P10_F20 and P11_F20)!")
    else:
        print("  [PASS] FI-05: Event persisted across ID switch.")

    print(f"\nCompleted {tests_run} failure injection checks. Discovered {len(failures)} failures.")
    for f in failures:
        print(f"  * {f}")
    return failures

if __name__ == "__main__":
    failures = test_failure_injection()
    if failures:
        print("\nFAILURE INJECTION AUDIT RESULT: FAILURES DETECTED")
        sys.exit(1)
    else:
        print("\nFAILURE INJECTION AUDIT RESULT: ALL PASSED")
        sys.exit(0)
