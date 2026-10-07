"""
V2.6 — Event Preservation Test

Proves that the V2.5/V2.6 OperatorVehicleRelationEngine does NOT
suppress True Positive near-miss events between independent
pedestrians and forklifts.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT))

from core.event_engine import EventEngine
from core.geometry import load_default_calibrator
from core.operator_relation import OperatorVehicleRelationEngine

def run_preservation_test():
    print("=== V2.6 Event Preservation Test ===\n")
    
    calibrator = load_default_calibrator()
    
    event_engine = EventEngine()
    relation_engine = OperatorVehicleRelationEngine()
    
    print("Simulating True Positive Near-Miss...")
    print("Scenario: Pedestrian walking close to an active forklift.\n")
    
    # Simulate 10 frames
    for frame_idx in range(1, 11):
        # Forklift at x=500, y=500
        f = {"id": 2, "bbox": [400, 400, 600, 600], "px": (500, 600), "vel": (0, 0)}
        
        # Pedestrian walking right-to-left beside the forklift
        px = 800 - frame_idx * 30
        p = {"id": 1, "bbox": [px, 200, px+50, 300], "px": (px+25, 300), "vel": (-30, 0)}
        
        # 1. Classify Relation
        rels = relation_engine.classify_frame([p], [f], frame_idx)
        person_rel = rels[0]["relation"]
        
        # 2. Check Distance (100px = 1m based on dummy calibration)
        dist_px = abs(p["px"][0] - f["px"][0])
        dist_m = dist_px / 100.0
        
        zone = "SAFE"
        if dist_m < 2.0: zone = "DANGER"
        elif dist_m < 5.0: zone = "CAUTION"
        
        # 3. Process Interaction
        interactions = []
        # Filter logic from run_experiment.py
        if person_rel != "OPERATOR_ON_VEHICLE":
            interactions.append({
                "person_id": p["id"],
                "forklift_id": f["id"],
                "distance_meters": dist_m,
                "approach_speed_px_s": 30.0,
                "zone_status": zone,
                "risk_exposure_score": 0.5,
                "person_relation": person_rel,
                "relation_confidence": 1.0
            })
            
        event_engine.process_frame_interactions(frame_idx, frame_idx*0.1, interactions)
        
        if frame_idx % 3 == 0:
            print(f"  Frame {frame_idx}: Dist={dist_m:.2f}m, Relation={person_rel}, Zone={zone}")

    event_engine.close_all_events()
    events = event_engine.get_all_events()
    
    print("\nResults:")
    if events:
        print(f"  True Events Preserved: {len(events)} ✓")
        print(f"  Event details: {events[0].get('event_type', 'PROXIMITY_EVENT')}, Duration: {events[0].get('duration_frames', 0)} frames")
    else:
        print("  FAIL: True Event was suppressed!")


if __name__ == "__main__":
    run_preservation_test()
