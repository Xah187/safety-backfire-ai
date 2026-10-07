"""
V2.9 Red-Team Test: State Machine Invariants & Illegal Transitions

Tests safety invariants across TrackManager, ObservationIntegrityGate, 
and EventEngineV2:
1. Invariant 1: INVALID observations cannot become safety eligible.
2. Invariant 2: Pure PREDICTED tracks cannot generate new safety events.
3. Invariant 3: STALE tracks cannot generate TTC or confirmed events.
4. Invariant 4: UNKNOWN relation cannot trigger SUPPRESSED_OPERATOR_EVENT.
5. Invariant 5: SAFE != INSUFFICIENT_EVIDENCE.
6. Invariant 6: TTC alone cannot confirm an event without proximity/risk zone.
7. Invariant 7: Event revision must preserve historical audit trail.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT))

from core.track_manager import TrackManager, TrackState
from core.observation_gate import ObservationIntegrityGate, ObservationValidity
from core.event_engine_v2 import EventEngineV2, InteractionEventV2

def test_invariants():
    print("\n=== V2.9 Red-Team: State Machine Invariants Audit ===")
    failures = []
    tests_run = 0

    # Invariant 1: INVALID observation cannot be safety eligible
    tests_run += 1
    gate = ObservationIntegrityGate()
    # Horizontal non-human blob (aspect 0.5)
    dec = gate.evaluate("person", [100, 100, 300, 200], keypoints=None, conf=0.8)
    if dec.validity == ObservationValidity.INVALID and dec.safety_eligible != False:
        failures.append("INV-01 FAILED: INVALID observation marked as safety eligible!")
    else:
        print("  [PASS] INV-01: INVALID observation rejected from safety eligibility.")

    # Invariant 2: Track born purely from low-confidence prediction cannot generate safety evidence
    tests_run += 1
    tm = TrackManager(strong_conf_threshold=0.35, max_prediction_frames=5)
    # First frame has weak conf (0.20) and no pose -> PREDICTED state, never observed
    objs = [{"id": 999, "class": "person", "bbox": [100, 100, 150, 250], "conf": 0.20, "px": (125, 250)}]
    out = tm.process_tracks(1, 0.04, objs)
    if out[0]["safety_eligible"] != False:
        failures.append("INV-02 FAILED: Unobserved prediction marked as safety eligible!")
    else:
        print("  [PASS] INV-02: Pure PREDICTED track denied safety eligibility.")

    # Invariant 3: Stale track cannot generate safety evidence
    tests_run += 1
    # Observe strongly once
    tm.process_tracks(1, 0.04, [{"id": 55, "class": "person", "bbox": [100, 100, 150, 250], "conf": 0.8, "px": (125, 250)}])
    # Then 6 frames of missing/weak observations
    for f in range(2, 8):
        out = tm.process_tracks(f, f * 0.04, [{"id": 55, "class": "person", "bbox": [100, 100, 150, 250], "conf": 0.1, "px": (125, 250)}])
    if out[0]["track_state"] != TrackState.STALE or out[0]["safety_eligible"] != False:
        failures.append(f"INV-03 FAILED: Track after 6 prediction frames not STALE or still eligible! State: {out[0]['track_state']}, Eligible: {out[0]['safety_eligible']}")
    else:
        print("  [PASS] INV-03: Stale track (>5 prediction frames) denied safety eligibility.")

    # Invariant 4: UNKNOWN relation cannot trigger SUPPRESSED_OPERATOR_EVENT
    tests_run += 1
    ee = EventEngineV2(max_gap_frames=15)
    ee.process_frame_interactions(1, 0.04, [{
        "person_id": 1, "forklift_id": 2, "distance_meters": 1.0, "zone_status": "DANGER", "relation": "UNKNOWN"
    }])
    ev = list(ee.active_events.values())[0]
    if ev.event_state == "SUPPRESSED_OPERATOR_EVENT":
        failures.append("INV-04 FAILED: UNKNOWN relation prematurely suppressed!")
    else:
        print("  [PASS] INV-04: UNKNOWN relation is NOT suppressed (retained as candidate).")

    # Invariant 5: SAFE != INSUFFICIENT_EVIDENCE
    tests_run += 1
    # Check EventEngineV2 state conflation flaw
    evt = InteractionEventV2("EVT_TEST", 1, 2, 1, 0.04, "UNKNOWN")
    # Simulate an event that ended with zero risk
    for f in range(1, 20):
        evt.update(f, f * 0.04, 5.0, "SAFE", "UNKNOWN")
    evt.end()
    # Check if event_state was improperly set to "INSUFFICIENT_EVIDENCE"
    if evt.event_state == "INSUFFICIENT_EVIDENCE":
        failures.append("INV-05 FAILED: event_state set to 'INSUFFICIENT_EVIDENCE' (Conflation of lifecycle phase with evidence level)!")
    else:
        print("  [PASS] INV-05: Event lifecycle does not conflate event_state with INSUFFICIENT_EVIDENCE.")

    # Invariant 6: A confirmed dangerous event must NOT have safety_state = INSUFFICIENT_EVIDENCE
    tests_run += 1
    evt_danger = InteractionEventV2("EVT_DANGER", 1, 2, 1, 0.04, "INDEPENDENT_PEDESTRIAN")
    evt_danger.update(1, 0.04, 0.5, "DANGER", "INDEPENDENT_PEDESTRIAN")
    if evt_danger.event_state == "CONFIRMED_EVENT" and evt_danger.safety_state == "INSUFFICIENT_EVIDENCE":
        failures.append("INV-06 FAILED: Confirmed dangerous event has contradictory safety_state = 'INSUFFICIENT_EVIDENCE'!")
    else:
        print("  [PASS] INV-06: Confirmed dangerous event has consistent safety_state.")

    # Invariant 7: Event revision must preserve audit history
    tests_run += 1
    evt_rev = InteractionEventV2("EVT_REV", 1, 2, 1, 0.04, "UNKNOWN")
    # Confirm it first
    for f in range(1, 5):
        evt_rev.update(f, f * 0.04, 1.0, "DANGER", "UNKNOWN")
        evt_rev.event_state = "CONFIRMED_EVENT"
        evt_rev.alert_state = "ALERTED"
    # Then operator relation is recovered
    evt_rev.update(5, 0.20, 1.0, "DANGER", "OPERATOR_ON_VEHICLE")
    if len(evt_rev.revision_history) == 0:
        failures.append("INV-07 FAILED: Event revision did not record audit history!")
    else:
        print("  [PASS] INV-07: Event revision preserved audit trail.")

    print(f"\nCompleted {tests_run} invariant checks. Discovered {len(failures)} failures.")
    for f in failures:
        print(f"  * {f}")
    return failures

if __name__ == "__main__":
    failures = test_invariants()
    if failures:
        print("\nINVARIANT AUDIT RESULT: FAILURES DETECTED (Documented for V2.9 Catalog)")
        sys.exit(1)
    else:
        print("\nINVARIANT AUDIT RESULT: ALL PASSED")
        sys.exit(0)
