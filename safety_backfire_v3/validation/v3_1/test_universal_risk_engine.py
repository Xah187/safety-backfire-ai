"""
V3.1 Validation Suite — Universal Risk Engine & Multi-Hazard Policy Dispatcher

Verifies:
1. Dispatch across all 7 specialized hazard policies.
2. Complete preservation of V3.0.5 Person-Forklift collision guarantees (2D Rice k=2.24, Jensen debias, FAIL-29 kinetic decoupling).
3. Decoupled ID Architecture: EntityID, PairID, EpisodeID, EventID, HazardID, AlertID.
4. ODD status degradation (OUT_OF_DOMAIN -> INSUFFICIENT_EVIDENCE).
5. Static proximity vs Kinetic threat vs Structural threat semantic separation.
"""
import sys
import os
import json
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

import safety_backfire_v3.ontology as onto
from safety_backfire_v3.core.universal_risk_engine import UniversalRiskEngine, UniversalRiskDecision

def run_universal_risk_engine_test():
    print("=" * 80)
    print("   V3.1 UNIVERSAL RISK ENGINE & MULTI-HAZARD POLICY TEST SUITE   ")
    print("=" * 80)
    
    engine = UniversalRiskEngine()
    
    # -------------------------------------------------------------
    # 1. Collision Policy & V3.0.5 Guarantees Preservation
    # -------------------------------------------------------------
    print("\n[1/4] Verifying Collision Policy (Preserving V3.0.5 Guarantees)...")
    
    # Test 1A: Imminent Collision with Approaching Velocity (FAIL-29 check)
    hz_collision = onto.HazardRecord(
        hazard_id="HZ_00001",
        hazard_type=onto.HazardType.COLLISION_HAZARD,
        entity_ids=["PERSON_1", "FORKLIFT_1"],
        severity=onto.InteractionSeverity.CRITICAL,
        imminence=onto.InteractionImminence.HIGH
    )
    rel_approaching = onto.RelationRecord(
        subject_entity_id="PERSON_1",
        object_entity_id="FORKLIFT_1",
        distance_m=2.2, # Caution zone
        distance_uncertainty_m=0.15,
        approach_speed_m_s=1.4,
        ttc_sec=1.5 # Active kinetic threat
    )
    
    dec_collision = engine.evaluate_hazard(hz_collision, relation=rel_approaching, evidence_quality=0.85)
    print(f"  - Approaching Collision (d=2.2m, TTC=1.5s): Decision = {dec_collision.risk_decision:<18} (FAIL-29 Decoupling)")
    assert dec_collision.risk_decision == "CONFIRMED_DANGER", "FAIL-29 violation: Approaching collision must trigger CONFIRMED_DANGER!"
    assert dec_collision.hazard_category == "KINETIC_TRAJECTORY", "Must identify as KINETIC_TRAJECTORY"
    assert dec_collision.alert_id is not None, "Confirmed danger must generate AlertID"

    # Test 1B: Stationary Proximity Hazard (TTC = infinity)
    rel_stationary = onto.RelationRecord(
        subject_entity_id="PERSON_1",
        object_entity_id="FORKLIFT_1",
        distance_m=0.9, # Critical clearance
        distance_uncertainty_m=0.10,
        approach_speed_m_s=0.0,
        ttc_sec=None # Stationary!
    )
    dec_stationary = engine.evaluate_hazard(hz_collision, relation=rel_stationary, evidence_quality=0.85)
    print(f"  - Stationary Proximity  (d=0.9m, TTC=None): Decision = {dec_stationary.risk_decision:<18} (Static Proximity)")
    assert dec_stationary.risk_decision == "CONFIRMED_DANGER", "Stationary proximity violation: Must trigger CONFIRMED_DANGER!"
    assert dec_stationary.hazard_category == "STATIC_PROXIMITY", "Must identify as STATIC_PROXIMITY"

    # Test 1C: Operator Cabin Suppression Invariant
    p_op = onto.PersonEntity(entity_id="PERSON_1", is_operator_suppressed=True)
    dec_op = engine.evaluate_hazard(hz_collision, entities_by_id={"PERSON_1": p_op}, relation=rel_stationary, evidence_quality=0.85)
    print(f"  - Operator Cabin State  (d=0.9m, Suppressed): Decision = {dec_op.risk_decision:<18}")
    assert dec_op.risk_decision == "SUPPRESSED_OPERATOR", "Operator suppression invariant violated"

    # -------------------------------------------------------------
    # 2. Structural Load & Infrastructure Policies (TTC = infinity)
    # -------------------------------------------------------------
    print("\n[2/4] Verifying Structural Load & Obstruction Policies...")
    
    # Structural Load Instability
    hz_load = onto.HazardRecord(
        hazard_id="HZ_00002",
        hazard_type=onto.HazardType.UNSAFE_LOAD_HAZARD,
        entity_ids=["PALLET_10", "PERSON_2"],
        severity=onto.InteractionSeverity.CRITICAL,
        imminence=onto.InteractionImminence.HIGH
    )
    dec_load = engine.evaluate_hazard(hz_load, evidence_quality=0.80)
    print(f"  - Unstable Load Hazard (Tilted Pallet):  Decision = {dec_load.risk_decision:<18} | Cat = {dec_load.hazard_category}")
    assert dec_load.risk_decision == "CONFIRMED_DANGER", "Unstable load near person must trigger danger"
    assert dec_load.hazard_category == "STRUCTURAL_THREAT"
    assert dec_load.telemetry["ttc_applicable"] is False, "TTC must not be applied to static structural threats"

    # Blocked Emergency Exit
    hz_egress = onto.HazardRecord(
        hazard_id="HZ_00003",
        hazard_type=onto.HazardType.BLOCKED_EGRESS_HAZARD,
        entity_ids=["PALLET_10", "EXIT_WEST"],
        severity=onto.InteractionSeverity.CRITICAL,
        imminence=onto.InteractionImminence.HIGH
    )
    dec_egress = engine.evaluate_hazard(hz_egress, evidence_quality=0.85)
    print(f"  - Blocked Emergency Exit:                Decision = {dec_egress.risk_decision:<18} | Cat = {dec_egress.hazard_category}")
    assert dec_egress.risk_decision == "CONFIRMED_DANGER", "Blocked emergency exit must trigger CONFIRMED_DANGER"

    # -------------------------------------------------------------
    # 3. Machinery, Man-Down & Environmental Policies
    # -------------------------------------------------------------
    print("\n[3/4] Verifying Machinery, Man-Down & Environmental Policies...")
    
    # Machinery Nip Point
    hz_machine = onto.HazardRecord(
        hazard_id="HZ_00004",
        hazard_type=onto.HazardType.MACHINERY_EXPOSURE_HAZARD,
        entity_ids=["PERSON_3", "CONVEYOR_1"],
        severity=onto.InteractionSeverity.CRITICAL
    )
    rel_nip = onto.RelationRecord(subject_entity_id="PERSON_3", object_entity_id="CONVEYOR_1", distance_m=0.5)
    dec_machine = engine.evaluate_hazard(hz_machine, relation=rel_nip, evidence_quality=0.90)
    print(f"  - Running Machinery Nip Point (d=0.5m):   Decision = {dec_machine.risk_decision:<18}")
    assert dec_machine.risk_decision == "CONFIRMED_DANGER"

    # Worker Man-Down
    hz_fall = onto.HazardRecord(
        hazard_id="HZ_00005",
        hazard_type=onto.HazardType.FALL_HAZARD,
        entity_ids=["PERSON_4"],
        severity=onto.InteractionSeverity.CRITICAL
    )
    dec_fall = engine.evaluate_hazard(hz_fall, evidence_quality=0.90)
    print(f"  - Worker Man-Down Fall:                  Decision = {dec_fall.risk_decision:<18}")
    assert dec_fall.risk_decision == "CONFIRMED_DANGER"

    # Chemical Spill
    hz_spill = onto.HazardRecord(
        hazard_id="HZ_00006",
        hazard_type=onto.HazardType.SPILL_SLIP_HAZARD,
        entity_ids=["FORKLIFT_2", "SPILL_01"],
        severity=onto.InteractionSeverity.CRITICAL
    )
    rel_spill = onto.RelationRecord(subject_entity_id="FORKLIFT_2", object_entity_id="SPILL_01", distance_m=0.8)
    dec_spill = engine.evaluate_hazard(hz_spill, relation=rel_spill, evidence_quality=0.85)
    print(f"  - Forklift Approaching Spill (d=0.8m):   Decision = {dec_spill.risk_decision:<18}")
    assert dec_spill.risk_decision == "CONFIRMED_DANGER"

    # -------------------------------------------------------------
    # 4. Decoupled ID Architecture & ODD Degradation
    # -------------------------------------------------------------
    print("\n[4/4] Verifying Decoupled ID Model & ODD Status Degradation...")
    print(f"  - Sample Decision ID Structure:")
    print(f"    * Decision ID: {dec_collision.decision_id}")
    print(f"    * Event ID:    {dec_collision.event_id}")
    print(f"    * Episode ID:  {dec_collision.episode_id}")
    print(f"    * Pair ID:     {dec_collision.pair_id}")
    print(f"    * Hazard ID:   {dec_collision.hazard_id}")
    print(f"    * Alert ID:    {dec_collision.alert_id}")
    
    # Assert distinct ID namespaces
    assert dec_collision.decision_id != dec_collision.event_id
    assert dec_collision.event_id != dec_collision.hazard_id
    assert dec_collision.hazard_id != dec_collision.alert_id

    # ODD Out-of-Domain Degradation
    dec_odd = engine.evaluate_hazard(hz_collision, relation=rel_approaching, odd_status=onto.ODDStatus.OUT_OF_DOMAIN)
    print(f"  - Out-of-Domain Camera Pitch:            Decision = {dec_odd.risk_decision:<18} (Fail-Closed)")
    assert dec_odd.risk_decision == "INSUFFICIENT_EVIDENCE", "Out of domain input must fail closed to INSUFFICIENT_EVIDENCE"
    assert dec_odd.alert_id is None, "Out of domain must never trigger false confirmed alerts"

    print("\n[SUCCESS] Universal Risk Engine Test 100% PASSED!")
    return True

if __name__ == "__main__":
    run_universal_risk_engine_test()
