"""
V2.8.2 — Adversarial Tests for TTC Integrity & Alert Lifecycle

Tests the new EMA-smoothed TTC calculations and the retroactive 
alert correction logic.
"""
import sys
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT))

from core.event_engine_v2 import EventEngineV2

def run_scenario(name: str, frames_data: list, expected_alert: str, expected_revoked: bool = False):
    engine = EventEngineV2(max_gap_frames=15)
    
    for f_idx, interactions in enumerate(frames_data):
        engine.process_frame_interactions(f_idx + 1, (f_idx + 1)/30.0, interactions)
        
    engine.close_all_events()
    events = engine.get_all_events()
    
    print(f"\n[{name}]")
    if not events:
        print("  No events generated!")
        return
        
    evt = events[0]
    print(f"  Final Event State:  {evt['event_state']}")
    print(f"  Final Alert State:  {evt['alert_state']} (Expected: {expected_alert})")
    print(f"  Revision History:   {len(evt['revision_history'])} revisions")
    
    has_revoked = len(evt['revision_history']) > 0
    match_alert = evt["alert_state"] == expected_alert
    match_revoked = has_revoked == expected_revoked
    
    if match_alert and match_revoked:
        print("  SAFETY CHECK: PASS ✓")
    else:
        print("  SAFETY CHECK: FAIL ✗")

def make_interaction(pid, fid, dist, zone, rel):
    return {"person_id": pid, "forklift_id": fid, "distance_meters": dist, "zone_status": zone, "relation": rel}

def main():
    print("=== V2.8.2 TTC Integrity & Alert Lifecycle Tests ===")
    
    # Case C: True closing trajectory (DANGER) over 20 frames
    # Starts at 3.0m, drops 0.1m every frame (3.0 m/s)
    frames_C = []
    dist = 3.0
    for i in range(20):
        dist -= 0.1
        frames_C.append([make_interaction(1, 100, max(0.1, dist), "DANGER", "UNKNOWN")])
    run_scenario("Case C: True Closing Trajectory", frames_C, "ALERTED", False)
    
    # Case E: Pose-Induced Jitter
    # Distance fluctuates rapidly 2.0 -> 1.0 -> 2.0 -> 1.0. 
    # Without EMA, approach speed = 1.0m per frame = 30 m/s!
    # With Negative Steps Check, it should be ignored.
    frames_E = []
    for i in range(20):
        jitter_dist = 2.0 if i % 2 == 0 else 1.0
        frames_E.append([make_interaction(2, 100, jitter_dist, "DANGER", "UNKNOWN")])
    run_scenario("Case E: Pose-Induced Jitter (EMA test)", frames_E, "NONE", False)
    
    # Retroactive Correction Test
    # 1. 20 frames of dangerous approach (UNKNOWN) -> Should trigger ALERTED
    # 2. 5 frames later, relation becomes OPERATOR -> Should trigger REVOKED
    frames_Retro = []
    dist = 3.0
    for i in range(20):
        dist -= 0.1
        frames_Retro.append([make_interaction(3, 100, dist, "DANGER", "UNKNOWN")])
    for i in range(5):
        frames_Retro.append([make_interaction(3, 100, dist, "DANGER", "OPERATOR_ON_VEHICLE")])
        
    run_scenario("Retroactive Correction (UNKNOWN -> ALERTED -> OPERATOR -> REVOKED)", frames_Retro, "REVOKED", True)

if __name__ == "__main__":
    main()
