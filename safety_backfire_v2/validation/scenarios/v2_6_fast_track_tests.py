"""
V2.6 — Fast-Track Validation Scenarios

Validates the Fast-Track logic in the OperatorVehicleRelationEngine
which immediately classifies a person as OPERATOR_ON_VEHICLE if
spatial containment and ROI match are very strong.

Scenarios:
1: Strong spatial containment + operator ROI (Real Operator)
2: Temporary overlap caused by occlusion (Person behind forklift)
3: Pedestrian crossing directly in front of forklift
4: Pedestrian close to forklift but independent
5: Real operator (but partially outside ROI due to jitter)
6: Operator exits forklift
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


def scenario_1_strong_containment():
    """Scenario 1: Strong spatial containment + operator ROI"""
    engine = OperatorVehicleRelationEngine()
    # Fully inside forklift, in the rear portion
    p = make_person(1, [900, 280, 1060, 510])
    f = make_forklift(2, [850, 0, 1273, 620])
    rels = engine.classify_frame([p], [f], frame_idx=1)
    
    return "S1: Strong Spatial+ROI", "OPERATOR_ON_VEHICLE", rels[0]


def scenario_2_occlusion():
    """Scenario 2: Temporary overlap caused by occlusion (Person behind forklift)"""
    engine = OperatorVehicleRelationEngine()
    # Person is behind forklift. Containment is high (visually), but person is NOT in ROI
    # ROI is rear 30-100%, Person is in front (10-30%)
    p = make_person(1, [880, 100, 950, 400])
    f = make_forklift(2, [850, 0, 1273, 620])
    rels = engine.classify_frame([p], [f], frame_idx=1)
    
    return "S2: Temporary Occlusion", "UNKNOWN or INDEPENDENT", rels[0]


def scenario_3_crossing():
    """Scenario 3: Pedestrian crossing directly in front of forklift"""
    engine = OperatorVehicleRelationEngine()
    # High containment as person crosses in front, but velocity is perpendicular
    # Frame 1: fast track might trigger if in ROI, so let's see. ROI is rear. 
    # Front of forklift is left side (x=850). If person crosses there, ROI=0.
    p = make_person(1, [850, 300, 920, 600], vel=(2.0, 0))
    f = make_forklift(2, [850, 0, 1273, 620], vel=(0, 2.0))
    rels = engine.classify_frame([p], [f], frame_idx=1)
    
    return "S3: Crossing in Front", "UNKNOWN or INDEPENDENT", rels[0]


def scenario_4_close_independent():
    """Scenario 4: Pedestrian close to forklift but independent"""
    engine = OperatorVehicleRelationEngine()
    # Next to forklift, containment = 0, but distance is small
    p = make_person(1, [780, 300, 840, 600])
    f = make_forklift(2, [850, 0, 1273, 620])
    rels = engine.classify_frame([p], [f], frame_idx=1)
    
    return "S4: Close but Independent", "INDEPENDENT_PEDESTRIAN", rels[0]


def scenario_5_jittering_operator():
    """Scenario 5: Real operator (but partially outside ROI due to jitter)"""
    engine = OperatorVehicleRelationEngine()
    # Operator leans forward. Containment > 0.6, ROI is moderate > 0.4
    p = make_person(1, [1000, 250, 1150, 500])
    f = make_forklift(2, [850, 0, 1273, 620])
    rels = engine.classify_frame([p], [f], frame_idx=1)
    
    return "S5: Jittering Operator", "OPERATOR_ON_VEHICLE", rels[0]


def scenario_6_exiting():
    """Scenario 6: Operator exits forklift"""
    engine = OperatorVehicleRelationEngine()
    res = None
    # Operator gets off and walks away
    for i in range(1, 10):
        if i < 4:
            # Riding
            p = make_person(1, [1000, 250, 1150, 500])
        else:
            # Exited, moving away, containment dropping
            px = 1000 + (i-3)*50
            p = make_person(1, [px, 250, px+100, 500])
            
        f = make_forklift(2, [850, 0, 1273, 620])
        rels = engine.classify_frame([p], [f], frame_idx=i)
        if i == 9: res = rels[0]
        
    return "S6: Exiting Forklift (Frame 9)", "UNKNOWN or INDEPENDENT", res


def main():
    print("=== V2.6 Fast-Track Validation Tests ===")
    
    scenarios = [
        scenario_1_strong_containment,
        scenario_2_occlusion,
        scenario_3_crossing,
        scenario_4_close_independent,
        scenario_5_jittering_operator,
        scenario_6_exiting
    ]
    
    passed = 0
    for fn in scenarios:
        name, expected, res = fn()
        actual = res["relation"]
        
        ok = False
        if "UNKNOWN" in expected:
            ok = actual in ("UNKNOWN", "INDEPENDENT_PEDESTRIAN")
        else:
            ok = actual == expected
            
        status = "PASS ✓" if ok else "FAIL ✗"
        if ok: passed += 1
        
        print(f"\n[{name}]")
        print(f"  Expected: {expected}")
        print(f"  Actual:   {actual}")
        print(f"  Status:   {status}")
        print(f"  Evidence: Cont={res['evidence']['spatial_containment']:.2f}, ROI={res['evidence']['operator_roi_match']:.2f}, Temp={res['evidence']['temporal_consistency']:.2f}, Score={res['evidence']['weighted_score']:.2f}")

    print(f"\nTotal: {passed}/{len(scenarios)} Passed.")

if __name__ == "__main__":
    main()
