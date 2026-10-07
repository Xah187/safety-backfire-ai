"""
V2.8 — Uncertainty-Aware Event Engine

Implements the Safety Matrix to decouple Relation State from Event State.
Prevents UNKNOWN relationships from instantly triggering CONFIRMED_EVENTs, 
instead holding them as CANDIDATE_EVENTs until strong temporal evidence is gathered.
"""
from typing import Dict, List, Any, Optional
import numpy as np

class InteractionEventV2:
    def __init__(self, event_id: str, person_id: int, forklift_id: int, start_frame: int, start_time: float, initial_relation: str):
        self.event_id = event_id
        self.person_id = person_id
        self.forklift_id = forklift_id
        
        # Lifecycle
        self.status = "ACTIVE"
        self.start_frame = start_frame
        self.end_frame = start_frame
        self.start_time = start_time
        self.end_time = start_time
        self.duration_sec = 0.0
        
        self.relation_state = initial_relation
        self.event_state = "CANDIDATE_EVENT"
        self.safety_state = "INSUFFICIENT_EVIDENCE" # Default safety semantics
        self.alert_state = "NONE" # NONE, PENDING, ALERTED, REVOKED
        self.confirmed_frames = 0
        self.risk_frames = 0
        self.reason = "initialized"
        self.requires_review = False
        self.promotion_evidence = {}
        self.revision_history = []
        
        # EMA Smoothing
        self.smoothed_distance_m = None
        
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
        
        # History
        self.distances_m: List[float] = []
        self.times_sec: List[float] = []
        self.zones: List[str] = []
        self.smoothed_distances_m: List[float] = []
        
        # Aggregated Metrics
        self.min_distance_m: Optional[float] = None
        self.median_distance_m: Optional[float] = None
        self.peak_approach_speed: Optional[float] = None
        self.dominant_zone: str = "SAFE"
        
    def update(self, frame_idx: int, time_sec: float, distance_m: float, zone: str, relation: str):
        self.end_frame = frame_idx
        self.end_time = time_sec
        self.duration_sec = round(self.end_time - self.start_time, 3)
        
        self.distances_m.append(distance_m)
        self.times_sec.append(time_sec)
        self.zones.append(zone)
        
        if self.min_distance_m is None or distance_m < self.min_distance_m:
            self.min_distance_m = distance_m
            
        if self.smoothed_distance_m is None:
            self.smoothed_distance_m = distance_m
        else:
            self.smoothed_distance_m = 0.7 * self.smoothed_distance_m + 0.3 * distance_m
            
        if zone in ["DANGER", "CAUTION"]:
            self.risk_frames += 1
            
        # V2.8.2: Compute Approach Speed & TTC with EMA Smoothing
        approach_speed_m_s = 0.0
        ttc = float('inf')
        
        self.smoothed_distances_m.append(self.smoothed_distance_m)
        
        if len(self.smoothed_distances_m) >= 5:
            past_dist = self.smoothed_distances_m[-5]
            past_time = self.times_sec[-5]
            dt = time_sec - past_time
            if dt > 0:
                # Trajectory Stability Check: In real motion, most frame-to-frame diffs are negative (getting closer).
                # In jitter, they oscillate (approx 50% positive, 50% negative).
                if len(self.distances_m) >= 15:
                    recent_dists = self.distances_m[-15:]
                    negative_steps = sum(1 for i in range(1, 15) if recent_dists[i] < recent_dists[i-1])
                    
                    if negative_steps >= 10: # At least 66% of the steps must be actively closing the distance
                        speed = -(self.smoothed_distance_m - past_dist) / dt
                        if 0 < speed < 10.0:
                            approach_speed_m_s = speed
                
        if approach_speed_m_s > 0.0:
            if self.peak_approach_speed is None or approach_speed_m_s > self.peak_approach_speed:
                self.peak_approach_speed = round(approach_speed_m_s, 2)

        if approach_speed_m_s > 0.5: # Needs to be moving towards the vehicle at > 0.5 m/s
            ttc = self.smoothed_distance_m / approach_speed_m_s
            
        # V2.8.2: Safety Matrix Promotion Logic & Alert Lifecycle
        
        if relation == "OPERATOR_ON_VEHICLE" and self.event_state != "SUPPRESSED_OPERATOR_EVENT":
            # Retroactive Correction
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
            
        if self.event_state == "SUPPRESSED_OPERATOR_EVENT":
            return
            
        # Promote INDEPENDENT_PEDESTRIAN if there is risk evidence
        if self.relation_state == "INDEPENDENT_PEDESTRIAN":
            if zone in ["DANGER", "CAUTION"]:
                self.event_state = "CONFIRMED_EVENT"
                self.safety_state = "UNSAFE"
                self.reason = "confirmed_pedestrian_risk"
                
        # Promote UNKNOWN only via Evidence Promotion Matrix
        if self.relation_state == "UNKNOWN" and self.event_state == "CANDIDATE_EVENT":
            if zone in ["DANGER", "CAUTION"] and ttc < 3.0:
                self.event_state = "CONFIRMED_EVENT"
                self.safety_state = "UNSAFE"
                self.reason = "unknown_escalated_due_to_dangerous_trajectory"
                self.promotion_evidence = {
                    "ttc": round(ttc, 2),
                    "approach_speed_m_s": round(approach_speed_m_s, 2),
                    "zone": zone
                }
            else:
                self.reason = "operator_ambiguity_retained"
                
        # Manage Alert Lifecycle
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
            
        # Determine SAFE vs INSUFFICIENT_EVIDENCE
        if self.event_state == "CANDIDATE_EVENT":
            if self.risk_frames == 0 and len(self.distances_m) >= 15:
                # Tracked for a long time, zero risk frames -> Proven Safe
                self.event_state = "DISMISSED"
                self.safety_state = "SAFE"
                self.reason = "stable_separation_safe"
                self.requires_review = False
            elif self.risk_frames == 0:
                # Tracked briefly, no risk -> Dismissed as event with insufficient evidence to claim permanent safety
                self.event_state = "DISMISSED"
                self.safety_state = "INSUFFICIENT_EVIDENCE"
                self.reason = "no_risk_evidence"
                self.requires_review = False
            
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "person_id": self.person_id,
            "forklift_id": self.forklift_id,
            "status": self.status,
            "start_frame": self.start_frame,
            "end_frame": self.end_frame,
            "duration_sec": self.duration_sec,
            "min_distance_m": self.min_distance_m,
            "median_distance_m": self.median_distance_m,
            "peak_approach_speed": self.peak_approach_speed,
            "zone": self.dominant_zone,
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

class EventEngineV2:
    def __init__(self, max_gap_frames: int = 15):
        self.max_gap_frames = max_gap_frames
        self.active_events: Dict[str, InteractionEventV2] = {}
        self.historical_events: List[InteractionEventV2] = []
        self._event_counter = 0
        
    def _get_pair_key(self, person_id: int, forklift_id: int) -> str:
        return f"P{person_id}_F{forklift_id}"
        
    def process_frame_interactions(self, frame_idx: int, time_sec: float, frame_interactions: List[Dict[str, Any]]):
        seen_pairs = set()
        
        for interaction in frame_interactions:
            p_id = interaction["person_id"]
            f_id = interaction["forklift_id"]
            dist_m = interaction.get("distance_meters")
            if dist_m is None: continue
            
            zone = interaction.get("zone_status", "SAFE")
            relation = interaction.get("relation", "UNKNOWN")
            
            pair_key = self._get_pair_key(p_id, f_id)
            seen_pairs.add(pair_key)
            
            if pair_key in self.active_events:
                event = self.active_events[pair_key]
                if frame_idx - event.end_frame > self.max_gap_frames:
                    event.end()
                    self.historical_events.append(event)
                    del self.active_events[pair_key]
            
            if pair_key not in self.active_events:
                self._event_counter += 1
                evt_id = f"EVT_{self._event_counter:04d}"
                event = InteractionEventV2(evt_id, p_id, f_id, frame_idx, time_sec, relation)
                self.active_events[pair_key] = event
            
            self.active_events[pair_key].update(frame_idx, time_sec, dist_m, zone, relation)
            
        keys_to_remove = []
        for pair_key, event in self.active_events.items():
            if pair_key not in seen_pairs:
                if frame_idx - event.end_frame > self.max_gap_frames:
                    event.end()
                    self.historical_events.append(event)
                    keys_to_remove.append(pair_key)
                    
        for k in keys_to_remove:
            del self.active_events[k]

    def close_all_events(self):
        for pair_key, event in list(self.active_events.items()):
            event.end()
            self.historical_events.append(event)
            del self.active_events[pair_key]
            
    def get_all_events(self) -> List[Dict[str, Any]]:
        return [e.to_dict() for e in self.historical_events]
