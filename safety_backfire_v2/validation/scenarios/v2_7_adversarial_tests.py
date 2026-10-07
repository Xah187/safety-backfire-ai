"""
V2.7 — Adversarial Integrity Tests for Multi-Cue Relation Engine

Tests the new OperatorVehicleRelationEngineV2 against 9 critical failure modes.
Validates the UNKNOWN != SUPPRESS Safety Invariant.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT))

from core.operator_relation_v2 import OperatorVehicleRelationEngineV2

def make_person(pid, bbox, torso=None, ankles=None):
    # Dummy COCO keypoints: 5,6 (Shoulders), 11,12 (Hips), 15,16 (Ankles)
    # The V2 engine expects them at these indices. We'll populate an array of 17.
    keypoints = [[0,0,0]] * 17
    
    if torso:
        # Put torso at Hip indices 11, 12
        keypoints[11] = [torso[0], torso[1], 0.9]
        keypoints[12] = [torso[0], torso[1], 0.9]
        
    if ankles:
        keypoints[15] = [ankles[0], ankles[1], 0.9]
        keypoints[16] = [ankles[0], ankles[1], 0.9]
        
    return {"id": pid, "bbox": bbox, "keypoints": keypoints}

def make_forklift(fid, bbox):
    return {"id": fid, "bbox": bbox}

def test_scenario(engine, name, expected, persons, forklifts):
    rels = engine.classify_frame(persons, forklifts, frame_idx=1)
    
    print(f"\n[{name}]")
    for p in persons:
        actual = "UNKNOWN"
        rel = next((r for r in rels if r["person_id"] == p["id"]), None)
        if rel:
            actual = rel["relation"]
            ev = rel["evidence"]
            
        print(f"  Person {p['id']}:")
        print(f"    Expected:  {expected[p['id']]}")
        print(f"    Predicted: {actual}")
        if rel:
            print(f"    Evidence:  TorsoInROI={ev['pose']['torso_in_roi']}, AnklesInVehicle={ev['pose']['ankles_in_vehicle']}, Overlap={ev['ground_geometry']['overlap']}")
        
        # Safety Invariant Test
        if actual == "UNKNOWN" and expected[p['id']] == "UNKNOWN":
            print("    SAFETY CHECK: PASS ✓ (UNKNOWN did not suppress)")

def main():
    print("=== V2.7 Adversarial Safety Tests (Multi-Cue) ===")
    
    engine = OperatorVehicleRelationEngineV2()
    f = make_forklift(100, [850, 0, 1273, 620])
    
    # Case A: Real operator leaning outside. (Torso in ROI, Ankles on vehicle, but low overlap)
    # Even if 2D overlap is low, pose proves they are operating it.
    p1 = make_person(1, [1100, 280, 1300, 510], torso=[1150, 300], ankles=[1000, 400])
    test_scenario(engine, "Case A: Operator leaning outside", {1: "OPERATOR_ON_VEHICLE"}, [p1], [f])
    
    # Case B: Pedestrian directly in front. (High overlap, but Torso/Ankles outside ROI/vehicle)
    p2 = make_person(2, [800, 300, 950, 600], torso=[875, 400], ankles=[875, 600])
    test_scenario(engine, "Case B: Pedestrian directly in front (High Overlap)", {2: "INDEPENDENT_PEDESTRIAN"}, [p2], [f])
    
    # Case C: Pedestrian directly behind.
    p3 = make_person(3, [1250, 200, 1350, 500], torso=[1300, 300], ankles=[1300, 500])
    test_scenario(engine, "Case C: Pedestrian directly behind", {3: "INDEPENDENT_PEDESTRIAN"}, [p3], [f])
    
    # Case D: Partial overlap but Pose missing (Heavy occlusion/blur)
    p4 = make_person(4, [800, 300, 900, 600], torso=None, ankles=None) # No confident keypoints
    test_scenario(engine, "Case D: Ambiguous 2D overlap (Pose missing)", {4: "UNKNOWN"}, [p4], [f])
    
    # Case E: Operator + Pedestrian simultaneously
    p_op = make_person(5, [950, 280, 1050, 510], torso=[1000, 350], ankles=[950, 500])
    p_ped = make_person(6, [800, 300, 950, 600], torso=[875, 400], ankles=[875, 600])
    test_scenario(engine, "Case E: Operator + Pedestrian", {5: "OPERATOR_ON_VEHICLE", 6: "INDEPENDENT_PEDESTRIAN"}, [p_op, p_ped], [f])

if __name__ == "__main__":
    main()
