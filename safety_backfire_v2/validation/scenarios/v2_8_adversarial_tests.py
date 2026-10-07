"""
V2.8 — Adversarial Tests for Uncertainty-Aware Safety Policy

Tests the new EventEngineV2 to ensure that UNKNOWN relations 
are properly handled via temporal evidence (Safety Matrix).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT))

from core.event_engine_v2 import EventEngineV2

def run_scenario(name: str, frames_data: list, expected_state: str):
    engine = EventEngineV2(max_gap_frames=15)
    
    # Run the frames
    for f_idx, interactions in enumerate(frames_data):
        engine.process_frame_interactions(f_idx + 1, (f_idx + 1)/30.0, interactions)
        
    engine.close_all_events()
    events = engine.get_all_events()
    
    print(f"\n[{name}]")
    if not events:
        print("  No events generated!")
        return
        
    evt = events[0]
    print(f"  Final Event State: {evt['event_state']} (Expected: {expected_state})")
    print(f"  Reason:            {evt['reason']}")
    print(f"  Risk Frames:       {evt['end_frame'] - evt['start_frame'] + 1}")
    
    if evt["event_state"] == expected_state:
        print("  SAFETY CHECK: PASS ✓")
    else:
        print("  SAFETY CHECK: FAIL ✗")

def make_interaction(pid, fid, dist, zone, rel):
    return {"person_id": pid, "forklift_id": fid, "distance_meters": dist, "zone_status": zone, "relation": rel}

def main():
    print("=== V2.8 Adversarial Policy Tests ===")
    
    # Case A: Operator with heavy occlusion (UNKNOWN, no risk -> INSUFFICIENT_EVIDENCE)
    # We pass it to the event engine, but distance is large (SAFE)
    frames_A = [[make_interaction(1, 100, 3.5, "SAFE", "UNKNOWN")]] * 30
    run_scenario("Case A: Occluded Operator (Safe Zone)", frames_A, "INSUFFICIENT_EVIDENCE")
    
    # Case B: Operator leaning outside forklift (UNKNOWN, Danger for 30 frames -> CONFIRMED)
    frames_B = [[make_interaction(2, 100, 0.5, "DANGER", "UNKNOWN")]] * 30
    run_scenario("Case B: Operator Leaning (Sustained Danger)", frames_B, "CONFIRMED_EVENT")
    
    # Case C: Independent pedestrian crossing in front (INDEPENDENT, Danger -> CONFIRMED quickly)
    frames_C = [[make_interaction(3, 100, 0.8, "DANGER", "INDEPENDENT_PEDESTRIAN")]] * 5
    run_scenario("Case C: Pedestrian crossing in front", frames_C, "CONFIRMED_EVENT")
    
    # Case G: One-frame jitter (UNKNOWN, Danger for 1 frame -> CANDIDATE/INSUFFICIENT)
    frames_G = [[make_interaction(4, 100, 0.9, "DANGER", "UNKNOWN")]]
    run_scenario("Case G: One-frame Jitter", frames_G, "CANDIDATE_EVENT")
    
    # Case H: Two-frame jitter
    frames_H = [[make_interaction(5, 100, 0.9, "DANGER", "UNKNOWN")]] * 2
    run_scenario("Case H: Two-frame Jitter", frames_H, "CANDIDATE_EVENT")
    
    # Case I: Sustained genuine interaction
    frames_I = [[make_interaction(6, 100, 1.2, "CAUTION", "INDEPENDENT_PEDESTRIAN")]] * 20
    run_scenario("Case I: Sustained Pedestrian Interaction", frames_I, "CONFIRMED_EVENT")
    
    # Case K: Clear operator overrides everything
    frames_K = [[make_interaction(7, 100, 0.0, "DANGER", "OPERATOR_ON_VEHICLE")]] * 30
    run_scenario("Case K: Clear Operator", frames_K, "SUPPRESSED_OPERATOR_EVENT")

if __name__ == "__main__":
    main()
