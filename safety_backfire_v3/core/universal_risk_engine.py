"""
V3.1 Core — Universal Risk Engine & Multi-Hazard Policy Dispatcher

Evolves the V3.0.5 single-pair collision engine into an entity-agnostic warehouse safety intelligence architecture.
Preserves:
  1. 2D Rice non-central chi calibration (k=2.24) and second-order Jensen debiasing.
  2. FAIL-29 resolution: Kinetic trajectory threats in caution zones trigger CONFIRMED_DANGER.
  3. Stationary proximity hazard preservation: TTC=infinity at d <= 1.5m triggers CURRENT_PROXIMITY_HAZARD.
  4. Operator cabin suppression invariant with strict temporal skew (<=150ms) and source age (<=350ms) contracts.
  5. Decoupled ID model: EntityID, PairID, EpisodeID, EventID, HazardID, AlertID.
  6. Strict safety semantics: UNKNOWN != SAFE, INSUFFICIENT_EVIDENCE != SAFE.
"""
import math
import time
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass, field

from safety_backfire_v3.ontology.hazards.taxonomy import HazardRecord, HazardType, HazardLifecycleState
from safety_backfire_v3.ontology.interactions.types import InteractionRecord, InteractionType, InteractionSeverity, InteractionImminence
from safety_backfire_v3.ontology.relations.types import RelationRecord, SpatialRelationType, KinematicRelationType
from safety_backfire_v3.ontology.entities.base import EntityBase, EntityCategory
from safety_backfire_v3.ontology.evidence.contracts import ProvenanceRecord, ODDStatus
from safety_backfire_v3.core.uncertainty_risk_engine import UncertaintyAwareRiskEngine, RiskEvaluationResult

@dataclass
class UniversalRiskDecision:
    """
    Decoupled, versioned safety decision from the Universal Risk Engine.
    """
    decision_id: str
    hazard_id: str
    event_id: str
    episode_id: str
    pair_id: Optional[str]
    entity_ids: List[str]
    hazard_type: str
    risk_decision: str               # SAFE, CAUTION, CANDIDATE_REVIEW, HIGH_PRIORITY_CANDIDATE, CONFIRMED_DANGER, INSUFFICIENT_EVIDENCE, SUPPRESSED_OPERATOR
    risk_score: float                # Monotonic continuous score [0.0..1.0]
    hazard_category: str             # STATIC_PROXIMITY, KINETIC_TRAJECTORY, STRUCTURAL_THREAT, ENVIRONMENTAL_THREAT, ZONE_VIOLATION, BENIGN
    imminence: str
    severity: str
    evidence_quality: float
    confidence_weight: float
    provenance: Optional[ProvenanceRecord]
    reason: str
    alert_id: Optional[str] = None
    telemetry: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "hazard_id": self.hazard_id,
            "event_id": self.event_id,
            "episode_id": self.episode_id,
            "pair_id": self.pair_id,
            "entity_ids": self.entity_ids,
            "hazard_type": self.hazard_type,
            "risk_decision": self.risk_decision,
            "risk_score": round(self.risk_score, 3),
            "hazard_category": self.hazard_category,
            "imminence": self.imminence,
            "severity": self.severity,
            "evidence_quality": round(self.evidence_quality, 3),
            "reason": self.reason,
            "alert_id": self.alert_id,
            "telemetry": self.telemetry
        }


class UniversalRiskEngine:
    """
    Universal Risk Reasoning Engine for Industrial Warehouses.
    Dispatches to specialized hazard policies while enforcing global invariants.
    """
    _decision_counter = 0
    _event_counter = 0
    _episode_counter = 0
    _alert_counter = 0

    def __init__(
        self,
        danger_distance_m: float = 1.5,
        caution_distance_m: float = 3.0,
        critical_clearance_m: float = 1.0,
        coverage_factor_k: float = 2.24
    ):
        # Retain validated V3.0.5 Person-Forklift collision engine
        self._v3_collision_engine = UncertaintyAwareRiskEngine(
            danger_distance_m=danger_distance_m,
            caution_distance_m=caution_distance_m,
            critical_clearance_zone_m=critical_clearance_m,
            coverage_factor_k=coverage_factor_k
        )

    def evaluate_hazard(
        self,
        hazard: HazardRecord,
        entities_by_id: Optional[Dict[str, EntityBase]] = None,
        relation: Optional[RelationRecord] = None,
        interaction: Optional[InteractionRecord] = None,
        evidence_quality: Optional[float] = None,
        odd_status: ODDStatus = ODDStatus.VALID
    ) -> UniversalRiskDecision:
        """
        Entity-agnostic risk evaluation entry point.
        Dispatches to appropriate hazard policy based on hazard_type.
        """
        self._decision_counter += 1
        self._event_counter += 1
        dec_id = f"DEC_{self._decision_counter:06d}"
        evt_id = f"EVT_{self._event_counter:06d}"
        ep_id = f"EP_{self._episode_counter:05d}"
        
        ent_ids = hazard.entity_ids
        pair_id = f"PAIR_{ent_ids[0]}_{ent_ids[1]}" if len(ent_ids) >= 2 else None
        
        ev_qual = evidence_quality if evidence_quality is not None else hazard.evidence_quality
        
        # 1. Global ODD Guard (Degraded / Out-of-Domain Safety Invariant)
        if odd_status == ODDStatus.OUT_OF_DOMAIN:
            return UniversalRiskDecision(
                decision_id=dec_id,
                hazard_id=hazard.hazard_id,
                event_id=evt_id,
                episode_id=ep_id,
                pair_id=pair_id,
                entity_ids=ent_ids,
                hazard_type=hazard.hazard_type.value,
                risk_decision="INSUFFICIENT_EVIDENCE",
                risk_score=0.10,
                hazard_category="OUT_OF_DOMAIN",
                imminence="NONE",
                severity=hazard.severity.value,
                evidence_quality=0.10,
                confidence_weight=0.10,
                provenance=hazard.provenance,
                reason="system_outside_validated_odd_boundary",
                telemetry={"odd_status": odd_status.value}
            )

        # 2. Insufficient Evidence Guard (Rule: INSUFFICIENT_EVIDENCE != SAFE)
        if ev_qual < 0.40:
            return UniversalRiskDecision(
                decision_id=dec_id,
                hazard_id=hazard.hazard_id,
                event_id=evt_id,
                episode_id=ep_id,
                pair_id=pair_id,
                entity_ids=ent_ids,
                hazard_type=hazard.hazard_type.value,
                risk_decision="INSUFFICIENT_EVIDENCE",
                risk_score=0.15,
                hazard_category="UNKNOWN_HAZARD",
                imminence="LOW",
                severity=hazard.severity.value,
                evidence_quality=ev_qual,
                confidence_weight=ev_qual,
                provenance=hazard.provenance,
                reason="sensory_evidence_quality_below_confidence_floor"
            )

        # 3. Policy Dispatcher by Hazard Family
        hz_type = hazard.hazard_type
        
        # Policy A: Collision Hazard (Preserves V3.0.5 Collision Engine)
        if hz_type in [HazardType.COLLISION_HAZARD, HazardType.STRUCK_BY_HAZARD]:
            return self._dispatch_collision_policy(dec_id, evt_id, ep_id, pair_id, hazard, relation, ev_qual, entities_by_id)

        # Policy B: Structural / Collapse / Unsafe Load Hazard (Static threat, TTC = infinity)
        elif hz_type in [HazardType.COLLAPSE_HAZARD, HazardType.UNSAFE_LOAD_HAZARD, HazardType.FALLING_OBJECT_HAZARD]:
            return self._dispatch_structural_load_policy(dec_id, evt_id, ep_id, pair_id, hazard, relation, ev_qual, entities_by_id)

        # Policy C: Infrastructure Obstruction & Blocked Egress Hazard
        elif hz_type in [HazardType.BLOCKED_EGRESS_HAZARD, HazardType.BLOCKED_AISLE_HAZARD, HazardType.FIRE_ACCESS_HAZARD]:
            return self._dispatch_obstruction_policy(dec_id, evt_id, ep_id, pair_id, hazard, relation, ev_qual)

        # Policy D: Machinery & Entrapment Exposure Hazard
        elif hz_type in [HazardType.MACHINERY_EXPOSURE_HAZARD, HazardType.ENTRAPMENT_HAZARD]:
            return self._dispatch_machinery_policy(dec_id, evt_id, ep_id, pair_id, hazard, relation, ev_qual)

        # Policy E: Zone Intrusion Hazard (Pedestrian or Vehicle)
        elif hz_type in [HazardType.PEDESTRIAN_ZONE_INTRUSION, HazardType.VEHICLE_ZONE_INTRUSION]:
            return self._dispatch_zone_intrusion_policy(dec_id, evt_id, ep_id, pair_id, hazard, ev_qual)

        # Policy F: Fall / Worker Man-Down Hazard
        elif hz_type == HazardType.FALL_HAZARD:
            return self._dispatch_man_down_policy(dec_id, evt_id, ep_id, pair_id, hazard, ev_qual)

        # Policy G: Environmental Hazard (Spills, Dock Edge)
        elif hz_type in [HazardType.SPILL_SLIP_HAZARD, HazardType.DOCK_EDGE_HAZARD]:
            return self._dispatch_environmental_policy(dec_id, evt_id, ep_id, pair_id, hazard, relation, ev_qual)

        # Fallback Policy: Unknown Hazard (Rule: UNKNOWN != SAFE)
        return UniversalRiskDecision(
            decision_id=dec_id,
            hazard_id=hazard.hazard_id,
            event_id=evt_id,
            episode_id=ep_id,
            pair_id=pair_id,
            entity_ids=ent_ids,
            hazard_type=hz_type.value,
            risk_decision="CANDIDATE_REVIEW",
            risk_score=0.30,
            hazard_category="UNKNOWN_HAZARD",
            imminence=hazard.imminence.value,
            severity=hazard.severity.value,
            evidence_quality=ev_qual,
            confidence_weight=ev_qual,
            provenance=hazard.provenance,
            reason="unclassified_hazard_requiring_candidate_review"
        )

    # -------------------------------------------------------------
    # Specialized Hazard Policy Modules
    # -------------------------------------------------------------
    def _dispatch_collision_policy(
        self, dec_id: str, evt_id: str, ep_id: str, pair_id: Optional[str],
        hazard: HazardRecord, relation: Optional[RelationRecord],
        ev_qual: float, entities_by_id: Optional[Dict[str, Any]]
    ) -> UniversalRiskDecision:
        """Collision Hazard Policy: delegates to validated V3.0.5 UncertaintyAwareRiskEngine."""
        dist = relation.distance_m if (relation and relation.distance_m is not None) else 2.0
        dist_unc = relation.distance_uncertainty_m if (relation and relation.distance_uncertainty_m is not None) else 0.20
        ttc = relation.ttc_sec if relation else None
        approach_speed = relation.approach_speed_m_s if relation else 0.0

        # Check operator suppression invariant
        rel_state = "INDEPENDENT_PEDESTRIAN"
        if entities_by_id:
            for ent_id in hazard.entity_ids:
                ent = entities_by_id.get(ent_id)
                if ent and getattr(ent, "is_operator_suppressed", False):
                    rel_state = "OPERATOR_ON_VEHICLE"
                    break

        v3_res = self._v3_collision_engine.evaluate(
            nominal_distance_m=dist,
            distance_uncertainty_m=dist_unc,
            evidence_quality=ev_qual,
            ttc_sec=ttc,
            approach_speed_m_s=approach_speed,
            relation_state=rel_state,
            coverage_factor=2.24
        )

        hazard_cat = "KINETIC_TRAJECTORY" if v3_res.predictive_collision_hazard else (
            "STATIC_PROXIMITY" if v3_res.proximity_hazard else "BENIGN"
        )

        alert_id = None
        if v3_res.risk_decision == "CONFIRMED_DANGER":
            self._alert_counter += 1
            alert_id = f"ALT_{self._alert_counter:05d}"

        return UniversalRiskDecision(
            decision_id=dec_id,
            hazard_id=hazard.hazard_id,
            event_id=evt_id,
            episode_id=ep_id,
            pair_id=pair_id,
            entity_ids=hazard.entity_ids,
            hazard_type=hazard.hazard_type.value,
            risk_decision=v3_res.risk_decision,
            risk_score=v3_res.risk_score,
            hazard_category=hazard_cat,
            imminence=hazard.imminence.value,
            severity=hazard.severity.value,
            evidence_quality=ev_qual,
            confidence_weight=v3_res.confidence_weight,
            provenance=hazard.provenance,
            reason=v3_res.reason,
            alert_id=alert_id,
            telemetry=v3_res.to_dict()
        )

    def _dispatch_structural_load_policy(
        self, dec_id: str, evt_id: str, ep_id: str, pair_id: Optional[str],
        hazard: HazardRecord, relation: Optional[RelationRecord],
        ev_qual: float, entities_by_id: Optional[Dict[str, Any]]
    ) -> UniversalRiskDecision:
        """Structural Load Policy: Unstable load or rack collapse threat (TTC is undefined/infinity)."""
        dist = relation.distance_m if (relation and relation.distance_m is not None) else 1.0
        
        # Imminent danger if person is near an unstable/tilted load
        if hazard.severity.value in ["CATASTROPHIC", "CRITICAL"]:
            decision = "CONFIRMED_DANGER"
            score = 0.85
            self._alert_counter += 1
            alert_id = f"ALT_{self._alert_counter:05d}"
            reason = "unstable_load_or_structure_with_personnel_exposure"
        else:
            decision = "CANDIDATE_REVIEW"
            score = 0.50
            alert_id = None
            reason = "potential_load_instability_under_observation"

        return UniversalRiskDecision(
            decision_id=dec_id,
            hazard_id=hazard.hazard_id,
            event_id=evt_id,
            episode_id=ep_id,
            pair_id=pair_id,
            entity_ids=hazard.entity_ids,
            hazard_type=hazard.hazard_type.value,
            risk_decision=decision,
            risk_score=score,
            hazard_category="STRUCTURAL_THREAT",
            imminence="HIGH",
            severity=hazard.severity.value,
            evidence_quality=ev_qual,
            confidence_weight=ev_qual,
            provenance=hazard.provenance,
            reason=reason,
            alert_id=alert_id,
            telemetry={"static_threat": True, "ttc_applicable": False}
        )

    def _dispatch_obstruction_policy(
        self, dec_id: str, evt_id: str, ep_id: str, pair_id: Optional[str],
        hazard: HazardRecord, relation: Optional[RelationRecord], ev_qual: float
    ) -> UniversalRiskDecision:
        """Infrastructure Obstruction Policy: Egress and aisle blockage."""
        is_egress = (hazard.hazard_type == HazardType.BLOCKED_EGRESS_HAZARD or hazard.hazard_type == HazardType.FIRE_ACCESS_HAZARD)
        if is_egress:
            decision = "CONFIRMED_DANGER"
            score = 0.90
            self._alert_counter += 1
            alert_id = f"ALT_{self._alert_counter:05d}"
            reason = "critical_emergency_egress_or_fire_route_blocked"
        else:
            decision = "CAUTION"
            score = 0.45
            alert_id = None
            reason = "traffic_aisle_clearance_obstructed"

        return UniversalRiskDecision(
            decision_id=dec_id,
            hazard_id=hazard.hazard_id,
            event_id=evt_id,
            episode_id=ep_id,
            pair_id=pair_id,
            entity_ids=hazard.entity_ids,
            hazard_type=hazard.hazard_type.value,
            risk_decision=decision,
            risk_score=score,
            hazard_category="ZONE_VIOLATION",
            imminence="HIGH" if is_egress else "MEDIUM",
            severity=hazard.severity.value,
            evidence_quality=ev_qual,
            confidence_weight=ev_qual,
            provenance=hazard.provenance,
            reason=reason,
            alert_id=alert_id
        )

    def _dispatch_machinery_policy(
        self, dec_id: str, evt_id: str, ep_id: str, pair_id: Optional[str],
        hazard: HazardRecord, relation: Optional[RelationRecord], ev_qual: float
    ) -> UniversalRiskDecision:
        """Machinery Exposure Policy: Nip points, conveyor entrapment."""
        dist = relation.distance_m if (relation and relation.distance_m is not None) else 1.0
        if dist <= 0.8:
            decision = "CONFIRMED_DANGER"
            score = 0.95
            self._alert_counter += 1
            alert_id = f"ALT_{self._alert_counter:05d}"
            reason = "direct_proximity_to_active_machinery_nip_point"
        else:
            decision = "HIGH_PRIORITY_CANDIDATE"
            score = 0.65
            alert_id = None
            reason = "worker_near_running_machinery_envelope"

        return UniversalRiskDecision(
            decision_id=dec_id,
            hazard_id=hazard.hazard_id,
            event_id=evt_id,
            episode_id=ep_id,
            pair_id=pair_id,
            entity_ids=hazard.entity_ids,
            hazard_type=hazard.hazard_type.value,
            risk_decision=decision,
            risk_score=score,
            hazard_category="STATIC_PROXIMITY",
            imminence="IMMINENT" if dist <= 0.8 else "HIGH",
            severity=hazard.severity.value,
            evidence_quality=ev_qual,
            confidence_weight=ev_qual,
            provenance=hazard.provenance,
            reason=reason,
            alert_id=alert_id
        )

    def _dispatch_zone_intrusion_policy(
        self, dec_id: str, evt_id: str, ep_id: str, pair_id: Optional[str],
        hazard: HazardRecord, ev_qual: float
    ) -> UniversalRiskDecision:
        """Restricted Zone Intrusion Policy."""
        decision = "CONFIRMED_DANGER" if hazard.hazard_type == HazardType.PEDESTRIAN_ZONE_INTRUSION else "HIGH_PRIORITY_CANDIDATE"
        score = 0.80
        self._alert_counter += 1
        alert_id = f"ALT_{self._alert_counter:05d}"
        return UniversalRiskDecision(
            decision_id=dec_id,
            hazard_id=hazard.hazard_id,
            event_id=evt_id,
            episode_id=ep_id,
            pair_id=pair_id,
            entity_ids=hazard.entity_ids,
            hazard_type=hazard.hazard_type.value,
            risk_decision=decision,
            risk_score=score,
            hazard_category="ZONE_VIOLATION",
            imminence="HIGH",
            severity=hazard.severity.value,
            evidence_quality=ev_qual,
            confidence_weight=ev_qual,
            provenance=hazard.provenance,
            reason="unauthorized_presence_in_restricted_zone",
            alert_id=alert_id
        )

    def _dispatch_man_down_policy(
        self, dec_id: str, evt_id: str, ep_id: str, pair_id: Optional[str],
        hazard: HazardRecord, ev_qual: float
    ) -> UniversalRiskDecision:
        """Worker Man-Down / Fall Policy."""
        self._alert_counter += 1
        return UniversalRiskDecision(
            decision_id=dec_id,
            hazard_id=hazard.hazard_id,
            event_id=evt_id,
            episode_id=ep_id,
            pair_id=pair_id,
            entity_ids=hazard.entity_ids,
            hazard_type=hazard.hazard_type.value,
            risk_decision="CONFIRMED_DANGER",
            risk_score=0.90,
            hazard_category="STATIC_PROXIMITY",
            imminence="HIGH",
            severity="CRITICAL",
            evidence_quality=ev_qual,
            confidence_weight=ev_qual,
            provenance=hazard.provenance,
            reason="worker_fallen_man_down_requiring_immediate_assistance",
            alert_id=f"ALT_{self._alert_counter:05d}"
        )

    def _dispatch_environmental_policy(
        self, dec_id: str, evt_id: str, ep_id: str, pair_id: Optional[str],
        hazard: HazardRecord, relation: Optional[RelationRecord], ev_qual: float
    ) -> UniversalRiskDecision:
        """Environmental Hazard Policy (Spills, Dock Edge)."""
        dist = relation.distance_m if (relation and relation.distance_m is not None) else 1.5
        if dist <= 1.0:
            decision = "CONFIRMED_DANGER"
            score = 0.85
            self._alert_counter += 1
            alert_id = f"ALT_{self._alert_counter:05d}"
            reason = "personnel_or_vehicle_breached_environmental_hazard_buffer"
        else:
            decision = "CAUTION"
            score = 0.40
            alert_id = None
            reason = "environmental_hazard_in_proximity"

        return UniversalRiskDecision(
            decision_id=dec_id,
            hazard_id=hazard.hazard_id,
            event_id=evt_id,
            episode_id=ep_id,
            pair_id=pair_id,
            entity_ids=hazard.entity_ids,
            hazard_type=hazard.hazard_type.value,
            risk_decision=decision,
            risk_score=score,
            hazard_category="ENVIRONMENTAL_THREAT",
            imminence="MEDIUM",
            severity=hazard.severity.value,
            evidence_quality=ev_qual,
            confidence_weight=ev_qual,
            provenance=hazard.provenance,
            reason=reason,
            alert_id=alert_id
        )
