"""
V2.6.1 — Fast-Track Integrity & Safety Tests

Validates whether the strict fast-track thresholds (Cont > 0.7, ROI > 0.6)
cause over-suppression or false negatives across 7 critical scenarios.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT))

from core.operator_relation import OperatorVehicleRelationEngine

def make_person(pid, bbox, vel=(0,0)):
    cx = (bbox[0]+bbox[2])/2.0; fy = bbox[3]
    return {"id": pid, "bbox": bbox, "vel": vel, "px": (cx, fy), "pos": (cx/100, fy/100)}

def make_forklift(fid, bbox, vel=(0,0)):
    cx = (bbox[0]+bbox[2])/2.0; fy = bbox[3]
    return {"id": fid, "bbox": bbox, "vel": vel, "px": (cx, fy), "pos": (cx/100, fy/100)}


def test_scenario(engine, name, expected, persons, forklifts):
    rels = engine.classify_frame(persons, forklifts, frame_idx=1)
    
    # Check all persons
    for p in persons:
        actual = "UNKNOWN"
        evidence_dict = {}
        
        rel = next((r for r in rels if r["person_id"] == p["id"]), None)
        if rel:
            actual = rel["relation"]
            evidence_dict = rel["evidence"]
            
        print(f"\n[{name} - Person {p['id']}]")
        print(f"  Expected: {expected[p['id']]}")
        print(f"  Predicted: {actual}")
        
        if evidence_dict:
            print(f"  Evidence: Cont={evidence_dict['spatial_containment']:.2f}, ROI={evidence_dict['operator_roi_match']:.2f}, Score={evidence_dict['weighted_score']:.2f}")
            print(f"  Decision: {evidence_dict['decision']}")
        else:
            print(f"  Decision: INDEPENDENT_PEDESTRIAN (No interaction evaluated)")

def main():
    print("=== V2.6.1 Fast-Track Safety & Integrity Tests ===")
    
    engine = OperatorVehicleRelationEngine()
    
    # Base forklift for all tests
    f = make_forklift(100, [850, 0, 1273, 620])
    
    # 1. Real Operator (Perfectly inside ROI)
    p1 = make_person(1, [900, 280, 1060, 510])
    test_scenario(engine, "1. Real Operator", {1: "OPERATOR_ON_VEHICLE"}, [p1], [f])
    
    # 2. Independent Pedestrian passing forklift (Crossing in front)
    p2 = make_person(2, [850, 300, 920, 600])
    test_scenario(engine, "2. Independent Pedestrian passing", {2: "UNKNOWN"}, [p2], [f]) # UNKNOWN is safe, doesn't suppress event
    
    # 3. Pedestrian very close to forklift
    p3 = make_person(3, [780, 300, 840, 600])
    test_scenario(engine, "3. Pedestrian very close", {3: "INDEPENDENT_PEDESTRIAN"}, [p3], [f])
    
    # 4. Pedestrian partial overlap (Walking near the side, cont = 0.3)
    p4 = make_person(4, [800, 300, 900, 600])
    test_scenario(engine, "4. Pedestrian partial overlap", {4: "INDEPENDENT_PEDESTRIAN"}, [p4], [f])
    
    # 5. Occluded pedestrian (Walking behind forklift)
    p5 = make_person(5, [880, 100, 950, 400])
    test_scenario(engine, "5. Occluded pedestrian", {5: "UNKNOWN"}, [p5], [f])
    
    # 6. Operator exits vehicle
    print("\n[6. Operator exits vehicle]")
    p6_start = make_person(6, [1000, 250, 1150, 500])
    for i in range(1, 4):
        engine.classify_frame([p6_start], [f], frame_idx=i) # Build history
    p6_end = make_person(6, [1100, 250, 1200, 500]) # Exited
    rels = engine.classify_frame([p6_end], [f], frame_idx=4)
    rel = next((r for r in rels if r["person_id"] == 6))
    print(f"  Expected: UNKNOWN (Temporary safe state)")
    print(f"  Predicted: {rel['relation']}")
    print(f"  Evidence: Cont={rel['evidence']['spatial_containment']:.2f}, ROI={rel['evidence']['operator_roi_match']:.2f}, Temp={rel['evidence']['temporal_consistency']:.2f}")
    
    # 7. Operator + independent pedestrian simultaneously
    p7_op = make_person(7, [900, 280, 1060, 510])
    p7_ped = make_person(8, [780, 300, 840, 600])
    test_scenario(engine, "7. Operator + Pedestrian", {7: "OPERATOR_ON_VEHICLE", 8: "INDEPENDENT_PEDESTRIAN"}, [p7_op, p7_ped], [f])

if __name__ == "__main__":
    main()
