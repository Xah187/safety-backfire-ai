"""
V2.5 — Synthetic Operator/Pedestrian Scenarios

9 controlled scenarios with mathematically known ground truth.
Tests the OperatorVehicleRelationEngine in isolation.
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


def scenario_a():
    """Independent pedestrian far from forklift."""
    engine = OperatorVehicleRelationEngine()
    p = make_person(1, [100, 300, 150, 480])
    f = make_forklift(2, [800, 100, 1200, 600])
    rels = engine.classify_frame([p], [f], frame_idx=1)
    return "A", "Independent pedestrian far from forklift", \
           "INDEPENDENT_PEDESTRIAN", rels[0]["relation"], rels[0]

def scenario_b():
    """Operator riding forklift — person bbox inside forklift bbox, sustained over 10 frames."""
    engine = OperatorVehicleRelationEngine()
    # Simulate 10 consecutive frames of coupled movement
    for frame in range(1, 11):
        offset = frame * 5  # forklift moving right
        p = make_person(1, [900+offset, 300, 1050+offset, 500], vel=(2.0, 0.0))
        f = make_forklift(2, [850+offset, 50, 1250+offset, 620], vel=(2.0, 0.0))
        rels = engine.classify_frame([p], [f], frame_idx=frame)
    return "B", "Operator riding forklift (10 frames coupled)", \
           "OPERATOR_ON_VEHICLE", rels[0]["relation"], rels[0]

def scenario_c():
    """Operator + separate independent pedestrian near same forklift."""
    engine = OperatorVehicleRelationEngine()
    for frame in range(1, 8):
        offset = frame * 3
        operator = make_person(1, [950+offset, 320, 1060+offset, 500], vel=(1.5, 0))
        pedestrian = make_person(3, [400, 350, 450, 500], vel=(0.5, -0.3))
        forklift = make_forklift(2, [880+offset, 60, 1270+offset, 610], vel=(1.5, 0))
        rels = engine.classify_frame([operator, pedestrian], [forklift], frame_idx=frame)

    operator_rel = next(r for r in rels if r["person_id"] == 1)
    pedestrian_rel = next(r for r in rels if r["person_id"] == 3)
    return "C", "Operator (id=1) + independent pedestrian (id=3)", \
           "OPERATOR=OV, PEDESTRIAN=IP", \
           f"op={operator_rel['relation']}, ped={pedestrian_rel['relation']}", \
           {"operator": operator_rel, "pedestrian": pedestrian_rel}

def scenario_d():
    """Pedestrian crossing near forklift — independent motion, minimal overlap."""
    engine = OperatorVehicleRelationEngine()
    for frame in range(1, 8):
        # Person walks left-to-right well below forklift, different direction
        px = 400 + frame * 60
        p = make_person(1, [px, 450, px+50, 550], vel=(4.0, 0.0))
        # Forklift is above and stationary
        f = make_forklift(2, [600, 50, 900, 350], vel=(0.0, 0.0))
        rels = engine.classify_frame([p], [f], frame_idx=frame)
    return "D", "Pedestrian crossing near stationary forklift", \
           "INDEPENDENT_PEDESTRIAN", rels[0]["relation"], rels[0]

def scenario_e():
    """Heavy occlusion — person partially hidden behind forklift."""
    engine = OperatorVehicleRelationEngine()
    # Person is behind the forklift, only top portion visible
    p = make_person(1, [850, 200, 950, 350], vel=(0.0, 0.0))
    f = make_forklift(2, [800, 100, 1200, 600], vel=(0.0, 0.0))
    rels = engine.classify_frame([p], [f], frame_idx=1)
    # With only 1 frame, temporal is 0. Result should be UNKNOWN or INDEPENDENT
    return "E", "Heavy occlusion (person behind forklift, 1 frame)", \
           "INDEPENDENT_PEDESTRIAN or UNKNOWN", rels[0]["relation"], rels[0]

def scenario_f():
    """Partial bbox overlap — person approaching forklift side."""
    engine = OperatorVehicleRelationEngine()
    # Person bbox overlaps ~30% with forklift side
    p = make_person(1, [780, 350, 860, 500], vel=(1.0, 0.0))
    f = make_forklift(2, [850, 100, 1200, 600], vel=(0.0, 0.0))
    rels = engine.classify_frame([p], [f], frame_idx=1)
    return "F", "Partial bbox overlap (person approaching side)", \
           "INDEPENDENT_PEDESTRIAN", rels[0]["relation"], rels[0]

def scenario_g():
    """Operator exits forklift — transition from coupled to independent."""
    engine = OperatorVehicleRelationEngine()
    results = []
    # Phase 1: Riding (frames 1-8)
    for frame in range(1, 9):
        p = make_person(1, [950, 320, 1060, 500], vel=(1.0, 0.0))
        f = make_forklift(2, [880, 60, 1270, 610], vel=(1.0, 0.0))
        rels = engine.classify_frame([p], [f], frame_idx=frame)
        results.append(("riding", frame, rels[0]["relation"]))

    # Phase 2: Exiting — person moves away from forklift (frames 9-16)
    for frame in range(9, 17):
        px = 950 - (frame - 8) * 50  # Person walks away left
        p = make_person(1, [px, 320, px+110, 500], vel=(-2.0, 0.0))
        f = make_forklift(2, [880, 60, 1270, 610], vel=(0.0, 0.0))  # Forklift stops
        rels = engine.classify_frame([p], [f], frame_idx=frame)
        results.append(("exiting", frame, rels[0]["relation"]))

    last_riding = [r for r in results if r[0] == "riding"][-1]
    last_exiting = [r for r in results if r[0] == "exiting"][-1]
    return "G", "Operator exits forklift (transition)", \
           "OPERATOR→INDEPENDENT", \
           f"riding={last_riding[2]}, exiting={last_exiting[2]}", \
           {"phases": results}

def scenario_h():
    """Pedestrian temporarily enters operator ROI but remains independent."""
    engine = OperatorVehicleRelationEngine()
    results = []
    for frame in range(1, 12):
        # Person walks through the forklift area frames 4-7, then exits
        if 4 <= frame <= 7:
            px = 950
        else:
            px = 500 + frame * 30
        p = make_person(1, [px, 350, px+60, 500], vel=(2.0, 0.0))
        f = make_forklift(2, [880, 60, 1270, 610], vel=(0.0, 0.0))  # Stationary forklift
        rels = engine.classify_frame([p], [f], frame_idx=frame)
        results.append((frame, rels[0]["relation"]))

    # After exiting, should be INDEPENDENT
    return "H", "Pedestrian temporarily enters ROI (4 frames)", \
           "INDEPENDENT_PEDESTRIAN (after exit)", results[-1][1], \
           {"trajectory": results}

def scenario_i():
    """Two people near one forklift — one operator, one pedestrian."""
    engine = OperatorVehicleRelationEngine()
    for frame in range(1, 10):
        offset = frame * 4
        op = make_person(1, [960+offset, 330, 1060+offset, 490], vel=(1.5, 0))
        ped = make_person(5, [600, 400, 660, 550], vel=(0.0, 0.5))
        fk = make_forklift(2, [890+offset, 70, 1270+offset, 600], vel=(1.5, 0))
        rels = engine.classify_frame([op, ped], [fk], frame_idx=frame)

    op_rel = next(r for r in rels if r["person_id"] == 1)
    ped_rel = next(r for r in rels if r["person_id"] == 5)
    return "I", "Two people: operator (1) + pedestrian (5) near forklift", \
           "1=OPERATOR, 5=INDEPENDENT", \
           f"1={op_rel['relation']}, 5={ped_rel['relation']}", \
           {"operator": op_rel, "pedestrian": ped_rel}


def run_all():
    print("=" * 65)
    print("  V2.5 Synthetic Operator/Pedestrian Scenarios")
    print("=" * 65)

    scenarios = [
        scenario_a, scenario_b, scenario_c, scenario_d,
        scenario_e, scenario_f, scenario_g, scenario_h, scenario_i
    ]

    results = []
    passed = 0
    failed = 0

    for fn in scenarios:
        label, desc, expected, actual, detail = fn()

        # Determine pass/fail
        if label in ("C", "I"):
            # Multi-person scenarios — check both
            ok = "OPERATOR" in actual and "INDEPENDENT" in actual
        elif label == "G":
            ok = "OPERATOR" in actual and "INDEPENDENT" in actual
        elif label == "E":
            ok = actual in ("INDEPENDENT_PEDESTRIAN", "UNKNOWN")
        elif label == "H":
            ok = actual in ("INDEPENDENT_PEDESTRIAN", "UNKNOWN")
        else:
            ok = actual == expected

        status = "PASS ✓" if ok else "FAIL ✗"
        if ok:
            passed += 1
        else:
            failed += 1

        print(f"\n  Scenario {label}: {desc}")
        print(f"    Expected: {expected}")
        print(f"    Actual:   {actual}")
        print(f"    Status:   {status}")

        results.append({
            "scenario": label,
            "description": desc,
            "expected": expected,
            "actual": actual,
            "status": "PASS" if ok else "FAIL"
        })

    print(f"\n{'=' * 65}")
    print(f"  RESULTS: {passed} PASS, {failed} FAIL out of {len(scenarios)}")
    print(f"{'=' * 65}")

    return results, passed, failed


if __name__ == "__main__":
    results, passed, failed = run_all()
    sys.exit(0 if failed == 0 else 1)
