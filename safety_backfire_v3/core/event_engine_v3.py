"""
V3.0 Core — Durable Event Engine & Interaction Lifecycle

Decouples Event Identity from transient ByteTrack IDs (P{pid}_F{fid}).
Keys events by durable Entity IDs: (person_entity_id, forklift_entity_id).
Preserves unbroken event continuity across tracker ID switches (P10 -> P11).
Maintains complete provenance and lineage history.
"""
import math
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

class InteractionEventV3:
    """
    Represents an ongoing or completed safety interaction between two durable entities.
    Tracks lineage across ID switches and provides unified safety metrics.
    """
    def __init__(
        self,
        event_id: str,
        person_entity_id: str,
        forklift_entity_id: str,
        start_frame: int,
        start_time: float,
        initial_relation: str,
        initial_track_pair: Tuple[int, int]
    ):
        self.event_id = event_id
        self.person_entity_id = person_entity_id
        self.forklift_entity_id = forklift_entity_id
        self.track_pair_lineage: List[Tuple[int, int]] = [initial_track_pair]
        
        # Lifecycle
        self.status = "ACTIVE" # ACTIVE, RESOLVED, DISMISSED
        self.start_frame = start_frame
        self.end_frame = start_frame
        self.start_time = start_time
        self.end_time = start_time
        self.duration_sec = 0.0
        
        self.relation_state = initial_relation
        self.event_state = "CANDIDATE_EVENT" # CANDIDATE_EVENT, CONFIRMED_EVENT, SUPPRESSED_OPERATOR_EVENT, DISMISSED
        self.safety_state = "SAFE" if initial_relation == "OPERATOR_ON_VEHICLE" else "INSUFFICIENT_EVIDENCE"
        self.alert_state = "NONE" # NONE, PENDING, ALERTED, REVOKED
        
        self.confirmed_frames = 0
        self.risk_frames = 0
        self.reason = "initialized"
        self.requires_review = False
        self.promotion_evidence: Dict[str, Any] = {}
        self.revision_history: List[Dict[str, Any]] = []
        
        # Distance & Kinematics Time-Series
        self.distances_m: List[float] = []
        self.times_sec: List[float] = []
        self.zones: List[str] = []
        self.smoothed_distances_m: List[float] = []
        self.smoothed_distance_m: Optional[float] = None
        
        # Uncertainty-Aware Risk Telemetry (FAIL-22)
        self.distance_uncertainty_m: Optional[float] = None
        self.distance_interval_m: Optional[Tuple[float, float]] = None
        self.nominal_risk: Optional[str] = None
        self.uncertainty_level: Optional[str] = None
        self.risk_decision: Optional[str] = None

        # Aggregated Metrics (Full Schema Parity with RiskEngine)
        self.min_distance_m: Optional[float] = None
        self.median_distance_m: Optional[float] = None
        self.peak_approach_speed: Optional[float] = None
        self.dominant_zone: str = "SAFE"

        if self.relation_state == "OPERATOR_ON_VEHICLE":
            self.event_state = "SUPPRESSED_OPERATOR_EVENT"
            self.safety_state = "SAFE"
            self.reason = "operator_rule"
        elif self.relation_state == "UNKNOWN":
            self.event_state = "CANDIDATE_EVENT"
            self.safety_state = "INSUFFICIENT_EVIDENCE"
            self.reason = "operator_ambiguity"
            self.requires_review = True
        elif self.relation_state == "INDEPENDENT_PEDESTRIAN":
            self.event_state = "CANDIDATE_EVENT"
            self.safety_state = "INSUFFICIENT_EVIDENCE"
            self.reason = "pedestrian_candidate"

    def update(
        self,
        frame_idx: int,
        time_sec: float,
        distance_m: float,
        zone: str,
        relation: str,
        current_track_pair: Tuple[int, int],
        cpa_miss_distance_m: Optional[float] = None,
        ttc_sec: Optional[float] = None,
        distance_uncertainty_m: Optional[float] = None,
        distance_interval_m: Optional[Tuple[float, float]] = None,
        nominal_risk: Optional[str] = None,
        uncertainty_level: Optional[str] = None,
        risk_decision: Optional[str] = None
    ):
        if self.status == "ENDED":
            raise RuntimeError(f"Illegal state modification: Cannot update closed event episode {self.event_id}")

        self.end_frame = frame_idx
        self.end_time = time_sec
        self.duration_sec = round(self.end_time - self.start_time, 3)
        
        if current_track_pair not in self.track_pair_lineage:
            self.track_pair_lineage.append(current_track_pair)
            self.revision_history.append({
                "frame": frame_idx,
                "event": "TRACK_ID_SWITCH_ABSORBED",
                "new_track_pair": current_track_pair
            })

        self.distances_m.append(distance_m)
        self.times_sec.append(time_sec)
        self.zones.append(zone)
        
        if self.min_distance_m is None or distance_m < self.min_distance_m:
            self.min_distance_m = distance_m
            
        if self.smoothed_distance_m is None:
            self.smoothed_distance_m = distance_m
        else:
            self.smoothed_distance_m = 0.7 * self.smoothed_distance_m + 0.3 * distance_m
        self.smoothed_distances_m.append(self.smoothed_distance_m)
        
        if zone in ["DANGER", "CAUTION"]:
            self.risk_frames += 1
            
        # Kinematic Velocity Calculation
        approach_speed_m_s = 0.0
        if len(self.smoothed_distances_m) >= 5:
            past_dist = self.smoothed_distances_m[-5]
            past_time = self.times_sec[-5]
            dt = time_sec - past_time
            if dt > 0:
                speed = -(self.smoothed_distance_m - past_dist) / dt
                if 0 < speed < 10.0:
                    approach_speed_m_s = speed
                    if self.peak_approach_speed is None or speed > self.peak_approach_speed:
                        self.peak_approach_speed = round(speed, 2)

        # Operator Suppression Override
        if relation == "OPERATOR_ON_VEHICLE" and self.event_state != "SUPPRESSED_OPERATOR_EVENT":
            if self.alert_state == "ALERTED":
                self.revision_history.append({
                    "frame": frame_idx,
                    "initial_state": self.event_state,
                    "final_state": "SUPPRESSED_OPERATOR_EVENT",
                    "revision_reason": "operator_relation_recovered"
                })
                self.alert_state = "REVOKED"
            
            self.relation_state = "OPERATOR_ON_VEHICLE"
            self.event_state = "SUPPRESSED_OPERATOR_EVENT"
            self.safety_state = "SAFE"
            self.reason = "operator_rule_promoted"
            self.requires_review = False
            self.confirmed_frames = 0

        if distance_uncertainty_m is not None:
            self.distance_uncertainty_m = distance_uncertainty_m
        if distance_interval_m is not None:
            self.distance_interval_m = distance_interval_m
        if nominal_risk is not None:
            self.nominal_risk = nominal_risk
        if uncertainty_level is not None:
            self.uncertainty_level = uncertainty_level
        if risk_decision is not None:
            self.risk_decision = risk_decision

        if self.event_state == "SUPPRESSED_OPERATOR_EVENT":
            return

        # Uncertainty-Aware Decision Integration (FAIL-22)
        if risk_decision == "CONFIRMED_DANGER":
            self.event_state = "CONFIRMED_EVENT"
            self.safety_state = "UNSAFE"
            self.reason = "confirmed_danger_with_high_evidence"
            self.requires_review = False
        elif risk_decision == "HIGH_PRIORITY_CANDIDATE":
            self.event_state = "CANDIDATE_EVENT"
            self.safety_state = "POTENTIAL_HAZARD"
            self.requires_review = True
            self.reason = "caution_with_plausible_danger_under_uncertainty"
        elif risk_decision == "INSUFFICIENT_EVIDENCE":
            self.event_state = "CANDIDATE_EVENT"
            self.safety_state = "INSUFFICIENT_EVIDENCE"
            self.requires_review = True
            self.reason = "spatial_uncertainty_masks_evidence"
        elif risk_decision == "CANDIDATE_REVIEW":
            self.event_state = "CANDIDATE_EVENT"
            self.safety_state = "INSUFFICIENT_EVIDENCE"
            self.requires_review = True
            self.reason = "review_needed_under_high_measurement_noise"
        elif risk_decision == "SAFE":
            if self.event_state == "CANDIDATE_EVENT":
                self.safety_state = "SAFE"
                self.reason = "clear_spatial_and_kinematic_separation"
        elif self.relation_state == "INDEPENDENT_PEDESTRIAN":
            # Fallback legacy branch
            if zone in ["DANGER", "CAUTION"]:
                self.event_state = "CONFIRMED_EVENT"
                self.safety_state = "UNSAFE"
                self.reason = "confirmed_pedestrian_risk"

        # Ambiguous Unknown Escalation (with CPA Miss-Distance Filter)
        if self.relation_state == "UNKNOWN" and self.event_state == "CANDIDATE_EVENT" and risk_decision is None:
            is_real_collision = (ttc_sec is not None and ttc_sec < 3.0)
            if cpa_miss_distance_m is not None and cpa_miss_distance_m > 1.8:
                is_real_collision = False # Crossing cleared

            if zone in ["DANGER", "CAUTION"] and is_real_collision:
                self.event_state = "CONFIRMED_EVENT"
                self.safety_state = "UNSAFE"
                self.reason = "unknown_escalated_due_to_dangerous_trajectory"
                self.promotion_evidence = {
                    "ttc": round(ttc_sec, 2) if ttc_sec else None,
                    "cpa_miss_m": round(cpa_miss_distance_m, 2) if cpa_miss_distance_m else None,
                    "zone": zone
                }

        # Alert Lifecycle
        if self.event_state == "CONFIRMED_EVENT":
            self.confirmed_frames += 1
            if self.alert_state == "NONE":
                self.alert_state = "PENDING"
            if self.confirmed_frames >= 3 and self.alert_state == "PENDING":
                self.alert_state = "ALERTED"

    def end(self):
        self.status = "ENDED"
        if self.distances_m:
            self.min_distance_m = round(self.min_distance_m, 3)
            self.median_distance_m = round(float(np.median(self.distances_m)), 3)
            
        if "DANGER" in self.zones:
            self.dominant_zone = "DANGER"
        elif "CAUTION" in self.zones:
            self.dominant_zone = "CAUTION"
            
        # Clean state resolution
        if self.event_state == "CANDIDATE_EVENT":
            if self.risk_frames == 0:
                self.event_state = "DISMISSED"
                self.safety_state = "SAFE" if len(self.distances_m) >= 15 else "INSUFFICIENT_EVIDENCE"
                self.reason = "separation_safe" if len(self.distances_m) >= 15 else "no_risk_evidence"
                self.requires_review = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "person_entity_id": self.person_entity_id,
            "forklift_entity_id": self.forklift_entity_id,
            "track_pair_lineage": self.track_pair_lineage,
            "status": self.status,
            "start_frame": self.start_frame,
            "end_frame": self.end_frame,
            "duration_sec": self.duration_sec,
            "min_distance_m": self.min_distance_m,
            "median_distance_m": self.median_distance_m,
            "peak_approach_speed": self.peak_approach_speed,
            "zone": self.dominant_zone,
            "distance_uncertainty_m": self.distance_uncertainty_m,
            "distance_interval_m": list(self.distance_interval_m) if self.distance_interval_m else None,
            "nominal_risk": self.nominal_risk,
            "uncertainty_level": self.uncertainty_level,
            "risk_decision": self.risk_decision,
            "relation_state": self.relation_state,
            "event_state": self.event_state,
            "alert_state": self.alert_state,
            "safety_state": self.safety_state,
            "reason": self.reason,
            "promotion_evidence": self.promotion_evidence,
            "revision_history": self.revision_history,
            "suppression_allowed": (self.event_state == "SUPPRESSED_OPERATOR_EVENT"),
            "requires_review": self.requires_review
        }


class EventEngineV3:
    """
    Event Engine indexed by durable Entity IDs.
    Absorbs ByteTrack ID switches without fragmenting active hazard encounters.
    """
    def __init__(self, max_gap_frames: int = 15):
        self.max_gap_frames = max_gap_frames
        self.active_events: Dict[str, InteractionEventV3] = {} # Key: "{p_entity}__{f_entity}"
        self.historical_events: List[InteractionEventV3] = []
        self._event_counter = 0

    def _get_entity_pair_key(self, p_ent: str, f_ent: str) -> str:
        return f"{p_ent}__{f_ent}"

    def process_frame_interactions(
        self,
        frame_idx: int,
        time_sec: float,
        frame_interactions: List[Dict[str, Any]]
    ):
        seen_keys = set()

        for interaction in frame_interactions:
            # Must use entity_id if available, falling back to raw id if not yet assigned
            p_ent = interaction.get("person_entity_id", f"P_RAW_{interaction['person_id']}")
            f_ent = interaction.get("forklift_entity_id", f"F_RAW_{interaction['forklift_id']}")
            raw_pair = (interaction["person_id"], interaction["forklift_id"])
            
            dist_m = interaction.get("distance_meters")
            if dist_m is None:
                continue

            zone = interaction.get("zone_status", "SAFE")
            relation = interaction.get("relation", "UNKNOWN")
            cpa_miss = interaction.get("cpa_miss_distance_m")
            ttc = interaction.get("ttc_sec")

            pair_key = self._get_entity_pair_key(p_ent, f_ent)
            seen_keys.add(pair_key)

            if pair_key in self.active_events:
                event = self.active_events[pair_key]
                if frame_idx - event.end_frame > self.max_gap_frames:
                    event.end()
                    self.historical_events.append(event)
                    del self.active_events[pair_key]

            if pair_key not in self.active_events:
                self._event_counter += 1
                evt_id = f"EPISODE_{self._event_counter:04d}__{p_ent}_vs_{f_ent}"
                event = InteractionEventV3(
                    evt_id, p_ent, f_ent, frame_idx, time_sec, relation, raw_pair
                )
                self.active_events[pair_key] = event

            self.active_events[pair_key].update(
                frame_idx=frame_idx,
                time_sec=time_sec,
                distance_m=dist_m,
                zone=zone,
                relation=relation,
                current_track_pair=raw_pair,
                cpa_miss_distance_m=cpa_miss,
                ttc_sec=ttc,
                distance_uncertainty_m=interaction.get("distance_uncertainty_m"),
                distance_interval_m=interaction.get("distance_interval_m"),
                nominal_risk=interaction.get("nominal_risk"),
                uncertainty_level=interaction.get("uncertainty_level"),
                risk_decision=interaction.get("risk_decision")
            )

        # Close inactive events exceeding gap frames
        keys_to_remove = []
        for pair_key, event in self.active_events.items():
            if pair_key not in seen_keys:
                if frame_idx - event.end_frame > self.max_gap_frames:
                    event.end()
                    self.historical_events.append(event)
                    keys_to_remove.append(pair_key)

        for k in keys_to_remove:
            del self.active_events[k]

    def process_interaction(
        self,
        frame_idx: int,
        time_sec: float,
        person_entity_id: str,
        forklift_entity_id: str,
        distance_m: float,
        zone: str,
        relation: str,
        person_track_id: int,
        forklift_track_id: int,
        cpa_miss_distance_m: Optional[float] = None,
        ttc_sec: Optional[float] = None
    ) -> InteractionEventV3:
        """Helper to process a single interaction directly and return the active event object."""
        pair_key = self._get_entity_pair_key(person_entity_id, forklift_entity_id)
        raw_pair = (person_track_id, forklift_track_id)
        
        if pair_key in self.active_events:
            event = self.active_events[pair_key]
            if frame_idx - event.end_frame > self.max_gap_frames:
                event.end()
                self.historical_events.append(event)
                del self.active_events[pair_key]

        if pair_key not in self.active_events:
            self._event_counter += 1
            evt_id = f"EPISODE_{self._event_counter:04d}__{person_entity_id}_vs_{forklift_entity_id}"
            event = InteractionEventV3(
                evt_id, person_entity_id, forklift_entity_id, frame_idx, time_sec, relation, raw_pair
            )
            self.active_events[pair_key] = event

        ev = self.active_events[pair_key]
        ev.update(frame_idx, time_sec, distance_m, zone, relation, raw_pair, cpa_miss_distance_m, ttc_sec)
        return ev

    def get_confirmed_events(self) -> List[InteractionEventV3]:
        confirmed = [e for e in self.active_events.values() if e.event_state == "CONFIRMED_EVENT"]
        confirmed += [e for e in self.historical_events if e.event_state == "CONFIRMED_EVENT"]
        return confirmed

    def close_all_events(self):
        for pair_key, event in list(self.active_events.items()):
            event.end()
            self.historical_events.append(event)
            del self.active_events[pair_key]

    def get_all_events(self) -> List[Dict[str, Any]]:
        all_evts = list(self.historical_events) + list(self.active_events.values())
        return [e.to_dict() for e in all_evts]
