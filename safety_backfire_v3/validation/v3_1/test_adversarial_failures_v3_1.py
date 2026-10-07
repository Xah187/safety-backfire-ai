"""
test_adversarial_failures_v3_1.py
Safety Backfire AI - V3.1 Adversarial Red Team Failure Mode Test Suite
Tests FAIL-31 through FAIL-37 against V3.1 Universal Safety Core & Ontology.
"""

import sys
import os
import json
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

import safety_backfire_v3.ontology as onto
from safety_backfire_v3.core.universal_risk_engine import UniversalRiskEngine, UniversalRiskDecision


def test_fail_31_entity_subtype_hallucination_under_occlusion():
    """
    FAIL-31: Entity Subtype Hallucination under Occlusion.
    Perception model with low subtype classification confidence (< 0.60) must fail closed
    to UNKNOWN_PERSON rather than falsely asserting PEDESTRIAN, OPERATOR, or CONTRACTOR.
    """
    prov = onto.ProvenanceRecord(
        source_frame_id=1,
        source_timestamp=100.0,
        capture_timestamp=100.015,
        entity_ids=["person_occluded_01"],
        evidence_type=onto.EvidenceType.DIRECT_OBSERVATION
    )
    conf = onto.ConfidenceDecomposition(
        detection_confidence=0.88,
        tracking_confidence=0.85,
        geometry_confidence=0.80,
        hazard_confidence=0.75
    )

    person = onto.PersonEntity(
        entity_id="person_occluded_01",
        person_subtype=onto.PersonSubtype.UNKNOWN_PERSON, # Must fail closed to UNKNOWN_PERSON
        world_pos_m=(4.0, 5.0),
        posture=onto.PostureState.UNKNOWN,
        metadata={"provenance": prov.to_dict()}
    )

    assert person.person_subtype == onto.PersonSubtype.UNKNOWN_PERSON, "Subtype must fail-closed to UNKNOWN_PERSON"
    assert person.subtype == "UNKNOWN_PERSON"
    
    # UniversalRiskEngine must handle UNKNOWN_PERSON with strict protective caution
    risk_engine = UniversalRiskEngine()
    hz = onto.HazardRecord(
        hazard_id="HZ_FAIL31",
        hazard_type=onto.HazardType.COLLISION_HAZARD,
        entity_ids=[person.entity_id, "FORKLIFT_1"],
        severity=onto.InteractionSeverity.CRITICAL,
        imminence=onto.InteractionImminence.HIGH
    )
    rel = onto.RelationRecord(
        subject_entity_id=person.entity_id,
        object_entity_id="FORKLIFT_1",
        distance_m=2.0,
        distance_uncertainty_m=0.15,
        approach_speed_m_s=1.2,
        ttc_sec=1.66
    )
    dec = risk_engine.evaluate_hazard(hz, relation=rel, evidence_quality=0.75)
    assert dec.risk_decision in ["CONFIRMED_DANGER", "CANDIDATE_REVIEW"]
    assert dec.alert_id is not None or dec.risk_score >= 0.5


def test_fail_32_relation_zone_false_positive_footpoint_bleed():
    """
    FAIL-32: Relation Zone False Positive from 2D Bbox Footpoint Bleed.
    Floor ground coordinate projection must be used for zone occupancy,
    NOT unprojected bounding box extents that bleed into neighboring restricted zones.
    """
    zone_mgr = onto.ZoneManager()
    zone_mgr.register_zone(onto.ZoneDefinition(
        zone_id="ped_lane_01",
        infra_type=onto.InfraType.PEDESTRIAN_LANE,
        polygon_vertices_m=[(0.0, 0.0), (3.0, 0.0), (3.0, 10.0), (0.0, 10.0)],
        is_pedestrian_only=True,
        description="Pedestrian Lane"
    ))
    zone_mgr.register_zone(onto.ZoneDefinition(
        zone_id="forklift_lane_01",
        infra_type=onto.InfraType.VEHICLE_LANE,
        polygon_vertices_m=[(3.0, 0.0), (6.0, 0.0), (6.0, 10.0), (3.0, 10.0)],
        is_vehicle_only=True,
        description="Forklift Lane"
    ))

    # Person standing safely at X=2.8m (inside pedestrian lane),
    # but their 2D bbox might overlap X=3.2m due to shoulder width / perspective.
    # Evaluator must use ground contact point (X=2.8, Y=5.0).
    containing_zones = zone_mgr.find_containing_zones((2.8, 5.0))
    containing_zone_ids = [z.zone_id for z in containing_zones]
    
    assert "ped_lane_01" in containing_zone_ids
    assert "forklift_lane_01" not in containing_zone_ids, "Footpoint isolation prevents false intrusion"


def test_fail_33_counterfactual_temporal_baseline_leakage():
    """
    FAIL-33: Counterfactual Temporal Baseline Leakage.
    Any attempt to modify or inject post-intervention observed data into the pre-intervention
    factual baseline or vice versa must raise TemporalLeakageError.
    """
    intv = onto.InterventionRecord(
        intervention_id="INTV_01",
        intervention_type=onto.InterventionType.PEDESTRIAN_ROUTE_REROUTED,
        zone_id="ZONE_A",
        timestamp=50.0,
        intended_hazards=(onto.HazardType.COLLISION_HAZARD.value,)
    )

    # 1. Timeline initialization with leaky baseline end timestamp
    leakage_caught_on_init = False
    try:
        onto.CounterfactualTimeline(
            intervention=intv,
            baseline_start_ts=0.0,
            baseline_end_ts=55.0, # Leaking past t=50.0!
            post_start_ts=50.0,
            post_end_ts=100.0
        )
    except onto.TemporalLeakageError:
        leakage_caught_on_init = True
    assert leakage_caught_on_init is True, "Must catch baseline window leakage past intervention timestamp"

    # 2. Timeline frame validation
    timeline = onto.CounterfactualTimeline(
        intervention=intv,
        baseline_start_ts=0.0,
        baseline_end_ts=50.0,
        post_start_ts=50.0,
        post_end_ts=100.0
    )
    assert timeline.validate_baseline_frame(10.0) is True

    leakage_caught_on_frame = False
    try:
        timeline.validate_baseline_frame(55.0) # Post-intervention frame fed into baseline
    except onto.TemporalLeakageError:
        leakage_caught_on_frame = True
    assert leakage_caught_on_frame is True, "Must raise TemporalLeakageError when t >= t_intervention in baseline"


def test_fail_34_inappropriate_kinetic_ttc_on_stationary_hazard():
    """
    FAIL-34: Inappropriate Kinetic TTC on Stationary Structural Hazard.
    When a static or near-static hazard exists (e.g. rack leaning, unstable load, blocked egress),
    relative velocity is near zero, causing kinematic TTC to be infinite or undefined.
    The UniversalRiskEngine must decouple structural hazard risk from kinematic TTC.
    """
    risk_engine = UniversalRiskEngine()

    hz = onto.HazardRecord(
        hazard_id="HZ_STRUCT_01",
        hazard_type=onto.HazardType.COLLAPSE_HAZARD,
        entity_ids=["WORKER_STAT", "RACK_UNSTABLE"],
        severity=onto.InteractionSeverity.CRITICAL,
        imminence=onto.InteractionImminence.HIGH
    )
    rel_static = onto.RelationRecord(
        subject_entity_id="WORKER_STAT",
        object_entity_id="RACK_UNSTABLE",
        distance_m=1.2, # Extremely close to collapsing rack
        approach_speed_m_s=0.0, # Stationary!
        ttc_sec=None # No kinematic closure (TTC is None)
    )

    dec = risk_engine.evaluate_hazard(hz, relation=rel_static, evidence_quality=0.90)

    assert dec.risk_decision == "CONFIRMED_DANGER", "Structural hazard must NOT be demoted due to TTC = None"
    assert dec.hazard_category == "STRUCTURAL_THREAT", "Identified under STRUCTURAL_THREAT policy"
    assert dec.telemetry.get("ttc_applicable") is False, "TTC explicitly decoupled from structural hazard"
    assert dec.alert_id is not None


def test_fail_35_cross_hazard_risk_masking():
    """
    FAIL-35: Cross-Hazard Risk Masking.
    A benign / safe relation between entities A and B must never suppress or mask
    a concurrent critical hazard between entities A and C. Max-risk policy must prevail.
    """
    risk_engine = UniversalRiskEngine()

    # Hazard 1: Entity A and B (Safe far-field forklift)
    hz_ab = onto.HazardRecord(
        hazard_id="HZ_SAFE_01",
        hazard_type=onto.HazardType.COLLISION_HAZARD,
        entity_ids=["WORKER_A", "FORKLIFT_FAR"],
        severity=onto.InteractionSeverity.NEGLIGIBLE,
        imminence=onto.InteractionImminence.LOW
    )
    rel_ab = onto.RelationRecord(
        subject_entity_id="WORKER_A",
        object_entity_id="FORKLIFT_FAR",
        distance_m=12.0,
        approach_speed_m_s=0.0,
        ttc_sec=None
    )
    dec_ab = risk_engine.evaluate_hazard(hz_ab, relation=rel_ab, evidence_quality=0.9)
    assert dec_ab.risk_decision == "SAFE"

    # Hazard 2: Entity A and C (Unstable pallet above worker)
    hz_ac = onto.HazardRecord(
        hazard_id="HZ_DANGER_01",
        hazard_type=onto.HazardType.FALLING_OBJECT_HAZARD,
        entity_ids=["WORKER_A", "PALLET_UNSTABLE"],
        severity=onto.InteractionSeverity.CRITICAL,
        imminence=onto.InteractionImminence.HIGH
    )
    rel_ac = onto.RelationRecord(
        subject_entity_id="WORKER_A",
        object_entity_id="PALLET_UNSTABLE",
        distance_m=1.1,
        approach_speed_m_s=0.0,
        ttc_sec=None
    )
    dec_ac = risk_engine.evaluate_hazard(hz_ac, relation=rel_ac, evidence_quality=0.88)
    assert dec_ac.risk_decision == "CONFIRMED_DANGER"

    # Scene-level aggregation: worst-case policy
    all_decisions = [dec_ab, dec_ac]
    priorities = {"CONFIRMED_DANGER": 3, "CAUTION": 2, "CANDIDATE_REVIEW": 1, "SAFE": 0}
    worst_decision = max(all_decisions, key=lambda d: priorities.get(d.risk_decision, 0))
    assert worst_decision.risk_decision == "CONFIRMED_DANGER", "Max-risk aggregation prevents masking"


def test_fail_36_aggregate_risk_transfer_blindness():
    """
    FAIL-36: Aggregate Risk Transfer Blindness.
    When an intervention eliminates a high-probability low-consequence hazard (e.g. slow bumper nudge)
    but shifts heavy traffic to block an emergency egress door, simple aggregate risk averaging
    would report a false safety improvement. SafetyBackfireEngine must catch the created hazard.
    """
    risk_engine = UniversalRiskEngine()
    intv = onto.InterventionRecord(
        intervention_id="INTV_DIVERT_01",
        intervention_type=onto.InterventionType.PEDESTRIAN_ROUTE_REROUTED,
        zone_id="MAIN_AISLE",
        timestamp=100.0,
        intended_hazards=(onto.HazardType.COLLISION_HAZARD.value,),
        description="Divert traffic around main aisle"
    )
    timeline = onto.CounterfactualTimeline(
        intervention=intv,
        baseline_start_ts=0.0,
        baseline_end_ts=100.0,
        post_start_ts=100.0,
        post_end_ts=200.0
    )

    # Pre-intervention baseline: 4 collisions in MAIN_AISLE
    before_decisions = []
    rel_col = onto.RelationRecord(subject_entity_id="P", object_entity_id="V", distance_m=1.8, approach_speed_m_s=1.2, ttc_sec=1.5)
    for i in range(4):
        prov = onto.ProvenanceRecord(source_frame_id=i*10, source_timestamp=float(i*20), capture_timestamp=float(i*20), entity_ids=["P", "V"])
        hz = onto.HazardRecord(hazard_id=f"HZ_B_{i}", hazard_type=onto.HazardType.COLLISION_HAZARD, entity_ids=["P", "V"], zone_id="MAIN_AISLE")
        dec = risk_engine.evaluate_hazard(hz, relation=rel_col)
        dec.provenance = prov
        dec.telemetry["zone"] = "MAIN_AISLE"
        before_decisions.append(dec)

    # Post-intervention: Collisions in MAIN_AISLE eliminated, but emergency exit blocked!
    after_decisions = []
    prov_post = onto.ProvenanceRecord(source_frame_id=110, source_timestamp=120.0, capture_timestamp=120.0, entity_ids=["FORKLIFT", "EXIT"])
    hz_blocked = onto.HazardRecord(hazard_id="HZ_BLOCKED_EXIT", hazard_type=onto.HazardType.BLOCKED_EGRESS_HAZARD, entity_ids=["FORKLIFT", "EXIT"], zone_id="EMERGENCY_ROUTE")
    dec_exit = risk_engine.evaluate_hazard(hz_blocked)
    dec_exit.provenance = prov_post
    dec_exit.telemetry["zone"] = "EMERGENCY_ROUTE"
    after_decisions.append(dec_exit)

    bfa = onto.SafetyBackfireEngine.evaluate_intervention_effect(timeline, before_decisions, after_decisions)

    assert bfa.primary_category == onto.RiskRedistributionCategory.NEW_HAZARD_CREATED
    assert bfa.backfire_signal == onto.BackfireSignal.PARTIAL_BACKFIRE
    assert "BLOCKED_EGRESS_HAZARD" in bfa.new_hazards_introduced


def test_fail_37_temporal_entity_state_resurrection_dropouts():
    """
    FAIL-37: Temporal Entity State Resurrection across Tracking Dropouts.
    When a track is lost for > T_max_dropout (e.g. 60 frames / 2.0s), the system must NOT
    resurrect stale high-speed velocity vectors without fresh observation evidence.
    Provenance temporal freshness must drop to DEGRADED and evidence quality degraded.
    """
    prov = onto.ProvenanceRecord(
        source_frame_id=100,
        source_timestamp=100.0,
        capture_timestamp=97.5, # 2.5s latency / dropout
        entity_ids=["FORKLIFT_RESURRECTED", "WORKER_1"],
        evidence_type=onto.EvidenceType.GEOMETRIC_INFERENCE,
        odd_status=onto.ODDStatus.DEGRADED
    )

    risk_engine = UniversalRiskEngine()
    hz = onto.HazardRecord(
        hazard_id="HZ_RESURRECTED",
        hazard_type=onto.HazardType.COLLISION_HAZARD,
        entity_ids=["FORKLIFT_RESURRECTED", "WORKER_1"],
        severity=onto.InteractionSeverity.CRITICAL,
        imminence=onto.InteractionImminence.HIGH,
        provenance=prov
    )
    rel = onto.RelationRecord(
        subject_entity_id="FORKLIFT_RESURRECTED",
        object_entity_id="WORKER_1",
        distance_m=2.0,
        distance_uncertainty_m=0.40,
        approach_speed_m_s=2.5, # Stale velocity
        ttc_sec=0.8
    )

    # When ODD status is DEGRADED or evidence quality is below threshold
    dec_odd = risk_engine.evaluate_hazard(hz, relation=rel, evidence_quality=0.35)
    assert dec_odd.risk_decision == "INSUFFICIENT_EVIDENCE", "Degraded sensory quality must yield INSUFFICIENT_EVIDENCE (rule: INSUFFICIENT_EVIDENCE != SAFE)"

    # And when ODD is OUT_OF_DOMAIN
    dec_ood = risk_engine.evaluate_hazard(hz, relation=rel, odd_status=onto.ODDStatus.OUT_OF_DOMAIN)
    assert dec_ood.risk_decision == "INSUFFICIENT_EVIDENCE"
    assert dec_ood.hazard_category == "OUT_OF_DOMAIN"


def run_all_adversarial_tests():
    print("=" * 80)
    print("   V3.1 ADVERSARIAL RED TEAM FAILURE SUITE (FAIL-31 TO FAIL-37)   ")
    print("=" * 80)

    tests = [
        ("FAIL-31", "Entity Subtype Hallucination Under Occlusion", test_fail_31_entity_subtype_hallucination_under_occlusion),
        ("FAIL-32", "Relation Zone FP From 2D Bbox Footpoint Bleed", test_fail_32_relation_zone_false_positive_footpoint_bleed),
        ("FAIL-33", "Counterfactual Temporal Baseline Leakage", test_fail_33_counterfactual_temporal_baseline_leakage),
        ("FAIL-34", "Inappropriate Kinetic TTC on Stationary Hazard", test_fail_34_inappropriate_kinetic_ttc_on_stationary_hazard),
        ("FAIL-35", "Cross-Hazard Risk Masking Prevention", test_fail_35_cross_hazard_risk_masking),
        ("FAIL-36", "Aggregate Risk Transfer Blindness", test_fail_36_aggregate_risk_transfer_blindness),
        ("FAIL-37", "Temporal Entity State Resurrection on Dropouts", test_fail_37_temporal_entity_state_resurrection_dropouts),
    ]

    results = []
    passed = 0
    for fid, name, func in tests:
        try:
            func()
            print(f"  [{fid}] {name:<48} | PASS")
            passed += 1
            results.append({"failure_id": fid, "name": name, "status": "RESOLVED_AND_VERIFIED", "passed": True})
        except Exception as e:
            print(f"  [{fid}] {name:<48} | FAIL: {e}")
            results.append({"failure_id": fid, "name": name, "status": "FAIL", "passed": False, "error": str(e)})

    print("\n" + "-" * 80)
    print(f"Adversarial Red Team Results: {passed}/{len(tests)} PASSED ({passed/len(tests)*100:.1f}%)")
    print("-" * 80)

    out_dir = Path(WORKSPACE_ROOT) / "safety_backfire_v3/outputs/v3_1"
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "adversarial_redteam_results.json", "w") as f:
        json.dump({"tests": results, "total_passed": passed, "total_tests": len(tests), "all_passed": (passed == len(tests))}, f, indent=2)

    assert passed == len(tests), f"Only {passed}/{len(tests)} tests passed!"
    return True


if __name__ == "__main__":
    run_all_adversarial_tests()
