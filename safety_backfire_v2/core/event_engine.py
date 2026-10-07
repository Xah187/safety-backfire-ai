"""
Phase 1 — Event Reconstruction Engine

Converts frame-based spatial risk detections into discrete, continuous Interaction Events.
Prevents the system from recording 20 separate near-misses for a single 20-frame interaction.
"""
from typing import Dict, List, Any, Optional
import numpy as np

class InteractionEvent:
    """Represents a continuous interaction between a specific person and forklift."""
    def __init__(self, event_id: str, person_id: int, forklift_id: int, start_frame: int, start_time: float):
        self.event_id = event_id
        self.person_id = person_id
        self.forklift_id = forklift_id
        
        # Lifecycle
        self.status = "NEW"  # NEW -> ACTIVE -> ENDED
        self.start_frame = start_frame
        self.end_frame = start_frame
        self.start_time = start_time
        self.end_time = start_time
        self.duration_sec = 0.0
        
        # History
        self.distances_m: List[float] = []
        self.approach_speeds: List[float] = []
        self.zones: List[str] = []
        
        # Aggregated Metrics
        self.min_distance_m: Optional[float] = None
        self.median_distance_m: Optional[float] = None
        self.min_distance_frame: Optional[int] = None
        self.peak_approach_speed: Optional[float] = None
        self.dominant_zone: str = "SAFE"
        
    def update(self, frame_idx: int, time_sec: float, distance_m: float, approach_speed: float, zone: str):
        self.status = "ACTIVE"
        self.end_frame = frame_idx
        self.end_time = time_sec
        self.duration_sec = round(self.end_time - self.start_time, 3)
        
        self.distances_m.append(distance_m)
        self.approach_speeds.append(approach_speed)
        self.zones.append(zone)
        
        if self.min_distance_m is None or distance_m < self.min_distance_m:
            self.min_distance_m = distance_m
            self.min_distance_frame = frame_idx
            
    def end(self):
        self.status = "ENDED"
        if self.distances_m:
            self.median_distance_m = round(float(np.median(self.distances_m)), 3)
            self.min_distance_m = round(self.min_distance_m, 3)
        if self.approach_speeds:
            self.peak_approach_speed = round(max(self.approach_speeds), 3)
            
        # Dominant zone is the highest risk zone encountered during the event
        if "DANGER" in self.zones:
            self.dominant_zone = "DANGER"
        elif "CAUTION" in self.zones:
            self.dominant_zone = "CAUTION"
            
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
            "min_distance_frame": self.min_distance_frame,
            "peak_approach_speed": self.peak_approach_speed,
            "zone": self.dominant_zone
        }

class EventEngine:
    def __init__(self, max_gap_frames: int = 15):
        # max_gap_frames allows an event to continue even if tracking is lost for a few frames
        self.max_gap_frames = max_gap_frames
        self.active_events: Dict[str, InteractionEvent] = {}  # key: "P{pid}_F{fid}"
        self.historical_events: List[InteractionEvent] = []
        self._event_counter = 0
        
    def _get_pair_key(self, person_id: int, forklift_id: int) -> str:
        return f"P{person_id}_F{forklift_id}"
        
    def process_frame_interactions(self, frame_idx: int, time_sec: float, frame_interactions: List[Dict[str, Any]]):
        """
        Takes the raw per-frame pairwise interactions and updates/creates Events.
        """
        seen_pairs = set()
        
        for interaction in frame_interactions:
            p_id = interaction["person_id"]
            f_id = interaction["forklift_id"]
            dist_m = interaction.get("distance_meters")
            if dist_m is None: continue  # requires metric distance
            
            speed = interaction.get("approach_speed_px_s", 0.0)
            zone = interaction.get("zone_status", "SAFE")
            
            pair_key = self._get_pair_key(p_id, f_id)
            seen_pairs.add(pair_key)
            
            if pair_key in self.active_events:
                event = self.active_events[pair_key]
                if frame_idx - event.end_frame > self.max_gap_frames:
                    # Gap too large! Close the old event and remove it
                    event.end()
                    self.historical_events.append(event)
                    del self.active_events[pair_key]
            
            if pair_key not in self.active_events:
                self._event_counter += 1
                evt_id = f"EVT_{self._event_counter:04d}"
                event = InteractionEvent(evt_id, p_id, f_id, frame_idx, time_sec)
                self.active_events[pair_key] = event
            
            # Update the event
            self.active_events[pair_key].update(frame_idx, time_sec, dist_m, speed, zone)
            
        # Check for events that have ended (not seen in this frame)
        keys_to_remove = []
        for pair_key, event in self.active_events.items():
            if pair_key not in seen_pairs:
                frames_since_last_seen = frame_idx - event.end_frame
                if frames_since_last_seen > self.max_gap_frames:
                    event.end()
                    self.historical_events.append(event)
                    keys_to_remove.append(pair_key)
                    
        for k in keys_to_remove:
            del self.active_events[k]

    def close_all_events(self):
        """Forces all active events to close at the end of the video."""
        for pair_key, event in list(self.active_events.items()):
            event.end()
            self.historical_events.append(event)
            del self.active_events[pair_key]
            
    def get_all_events(self) -> List[Dict[str, Any]]:
        return [e.to_dict() for e in self.historical_events]
