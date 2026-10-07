import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from core.event_engine import EventEngine

def test_event_engine():
    engine = EventEngine(max_gap_frames=2)
    
    # Simulate Frame 1
    engine.process_frame_interactions(1, 0.1, [
        {"person_id": 1, "forklift_id": 99, "distance_meters": 2.0, "approach_speed_px_s": 10.0, "zone_status": "CAUTION"}
    ])
    
    # Simulate Frame 2
    engine.process_frame_interactions(2, 0.2, [
        {"person_id": 1, "forklift_id": 99, "distance_meters": 1.5, "approach_speed_px_s": 12.0, "zone_status": "DANGER"}
    ])
    
    # Simulate Frame 5 (Gap of 3 frames > max_gap_frames of 2, should close EVT_0001)
    engine.process_frame_interactions(5, 0.5, [
        {"person_id": 1, "forklift_id": 99, "distance_meters": 3.0, "approach_speed_px_s": 5.0, "zone_status": "SAFE"}
    ])
    
    engine.close_all_events()
    events = engine.get_all_events()
    
    assert len(events) == 2, f"Expected 2 events, got {len(events)}"
    
    evt1 = events[0]
    assert evt1["start_frame"] == 1
    assert evt1["end_frame"] == 2
    assert evt1["min_distance_m"] == 1.5
    assert evt1["zone"] == "DANGER"
    assert evt1["duration_sec"] == 0.1
    
    evt2 = events[1]
    assert evt2["start_frame"] == 5
    assert evt2["zone"] == "SAFE"
    
    print("EventEngine tests passed successfully!")

if __name__ == "__main__":
    test_event_engine()
