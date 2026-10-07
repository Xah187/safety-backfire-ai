"""
V2.8.1 — Adversarial Tests for Event Promotion Safety Gate

Tests the Evidence Matrix to ensure UNKNOWN relations do not blindly 
promote to CONFIRMED_EVENT based on time alone. They must exhibit 
dangerous trajectory (low TTC).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT))

from core.event_engine_v2 import EventEngineV2

def run_scenario(name: str, frames_data: list, expected_event_state: str, expected_safety_state: str = None):
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
    print(f"  Final Event State:  {evt['event_state']} (Expected: {expected_event_state})")
    if expected_safety_state:
        print(f"  Final Safety State: {evt['safety_state']} (Expected: {expected_safety_state})")
    print(f"  Reason:             {evt['reason']}")
    
    if evt.get("promotion_evidence"):
        print(f"  Promotion Evidence: {evt['promotion_evidence']}")
        
    match_event = evt["event_state"] == expected_event_state
    match_safety = (evt["safety_state"] == expected_safety_state) if expected_safety_state else True
    
    if match_event and match_safety:
        print("  SAFETY CHECK: PASS ✓")
    else:
        print("  SAFETY CHECK: FAIL ✗")

def make_interaction(pid, fid, dist, zone, rel):
    return {"person_id": pid, "forklift_id": fid, "distance_meters": dist, "zone_status": zone, "relation": rel}

def main():
    print("=== V2.8.1 Event Promotion Safety Gate Tests ===")
    
    # Case A: Operator + heavy occlusion + 30 frames (Stationary/Safe)
    frames_A = [[make_interaction(1, 100, 3.5, "SAFE", "UNKNOWN")]] * 30
    run_scenario("Case A: Occluded Operator (Safe, long duration)", frames_A, "INSUFFICIENT_EVIDENCE", "SAFE")
    
    # Case B: Static false detection (UNKNOWN, Danger zone but STATIC distance)
    frames_B = [[make_interaction(2, 100, 1.0, "DANGER", "UNKNOWN")]] * 30
    run_scenario("Case B: Static False Detection (Danger zone, no approach)", frames_B, "CANDIDATE_EVENT", "INSUFFICIENT_EVIDENCE")
    
    # Case D: Unknown + proximity + dangerous trajectory + low TTC
    # Simulating a pedestrian walking straight at the forklift (distance drops by 0.5m every 5 frames = 0.1m/frame = 3m/s)
    frames_D = []
    dist = 5.0
    for i in range(15):
        dist -= 0.2
        zone = "DANGER" if dist <= 1.5 else ("CAUTION" if dist <= 3.0 else "SAFE")
        frames_D.append([make_interaction(4, 100, dist, zone, "UNKNOWN")])
        
    run_scenario("Case D: Unknown Person Approaching (Low TTC)", frames_D, "CONFIRMED_EVENT", "INSUFFICIENT_EVIDENCE")
    
    # Case E: Unknown + high proximity but stationary forklift/person
    frames_E = [[make_interaction(5, 100, 1.2, "DANGER", "UNKNOWN")]] * 20
    run_scenario("Case E: Unknown stationary near forklift", frames_E, "CANDIDATE_EVENT", "INSUFFICIENT_EVIDENCE")

if __name__ == "__main__":
    main()
