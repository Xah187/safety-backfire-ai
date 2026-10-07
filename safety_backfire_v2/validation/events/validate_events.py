"""
Phase 7 — Event Validation

Validates the Event Engine's ability to consolidate continuous tracking frames
into single InteractionEvents, and ensures metrics (start, end, duration, min_distance)
are correct, preventing the V1 fragmentation issue.
"""
import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT))

from core.event_engine import EventEngine

def run_event_validation():
    engine = EventEngine(max_gap_frames=15)
    
    # Simulate a single continuous interaction spanning frames 100 to 130
    # with a 5-frame gap (115-119) where tracking is lost.
    
    fps = 30.0
    
    # Frame 100 to 114
    for frame in range(100, 115):
        time_sec = frame / fps
        dist = 5.0 - (frame - 100) * 0.1 # Distance decreases from 5.0 to 3.6
        interactions = [{
            "person_id": 1, "forklift_id": 99,
            "distance_meters": dist, "approach_speed_px_s": 0.5,
            "zone_status": "CAUTION" if dist < 3.0 else "SAFE",
            "risk_exposure_score": 10.0
        }]
        engine.process_frame_interactions(frame, time_sec, interactions)
        
    # Frames 115 to 119: Tracking lost (empty interactions)
    for frame in range(115, 120):
        time_sec = frame / fps
        engine.process_frame_interactions(frame, time_sec, [])
        
    # Frames 120 to 130: Tracking resumes
    for frame in range(120, 131):
        time_sec = frame / fps
        dist = 3.6 - (frame - 120) * 0.1 # Distance decreases to 2.6
        interactions = [{
            "person_id": 1, "forklift_id": 99,
            "distance_meters": dist, "approach_speed_px_s": 0.5,
            "zone_status": "CAUTION" if dist < 3.0 else "SAFE",
            "risk_exposure_score": 10.0
        }]
        engine.process_frame_interactions(frame, time_sec, interactions)
        
    # Frames 131 to 150: Empty
    for frame in range(131, 151):
        time_sec = frame / fps
        engine.process_frame_interactions(frame, time_sec, [])
        
    # Close
    engine.close_all_events()
    
    events = engine.historical_events
    
    passed = True
    errors = []
    
    if len(events) != 1:
        passed = False
        errors.append(f"Expected 1 event, got {len(events)}")
    else:
        evt = events[0]
        if evt.start_frame != 100 or evt.end_frame != 130:
            passed = False
            errors.append(f"Expected frames 100-130, got {evt.start_frame}-{evt.end_frame}")
            
        expected_duration = round((130 - 100) / fps, 3)
        if evt.duration_sec != expected_duration:
            passed = False
            errors.append(f"Expected duration {expected_duration}, got {evt.duration_sec}")
            
        # Min distance should be at frame 130 (2.6m)
        if evt.min_distance_m != 2.6:
            passed = False
            errors.append(f"Expected min_dist 2.6, got {evt.min_distance_m}")
            
    report = {
        "event_validation_passed": passed,
        "errors": errors,
        "total_events": len(events)
    }
    
    out_dir = ROOT / "validation" / "events"
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "event_validation.json", "w") as f:
        json.dump(report, f, indent=2)
        
    print(f"Event Validation Passed: {passed}")
    if not passed:
        print(errors)

if __name__ == "__main__":
    run_event_validation()
