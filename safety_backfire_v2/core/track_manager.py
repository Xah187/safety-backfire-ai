from typing import Dict, List, Any
import math
from core.observation_gate import ObservationIntegrityGate, ObservationValidity

class TrackState:
    OBSERVED = "OBSERVED"
    PREDICTED = "PREDICTED"
    STALE = "STALE"

class TrackManager:
    """
    Acts as a firewall between raw tracker output and the Safety Engine.
    Ensures Ghost Tracks and Stale Predictions do not influence risk metrics.
    """
    def __init__(self, strong_conf_threshold=0.35, max_prediction_frames=5, max_drift_speed_m_s=8.0):
        self.strong_conf_threshold = strong_conf_threshold
        self.max_prediction_frames = max_prediction_frames
        self.max_drift_speed_m_s = max_drift_speed_m_s
        self.obs_gate = ObservationIntegrityGate()
        
        # track_id -> dict of track info
        self.tracks: Dict[int, Dict[str, Any]] = {}
        
    def process_tracks(self, frame_idx: int, time_sec: float, tracked_objects: List[Dict[str, Any]], calibrator=None) -> List[Dict[str, Any]]:
        """
        Takes raw tracker objects (id, class, bbox, conf, px), updates states, 
        and returns only valid safety objects (OBSERVED or PREDICTED but not STALE).
        """
        valid_objects = []
        current_ids = set()
        
        for obj in tracked_objects:
            t_id = obj["id"]
            current_ids.add(t_id)
            conf = obj.get("conf", 0.0)
            
            is_strong_observation = conf >= self.strong_conf_threshold
            
            # Compute spatial context: overlap with any forklift in current frame
            max_forklift_overlap = 0.0
            if obj["class"] == "person":
                px1, py1, px2, py2 = obj["bbox"]
                p_area = max(1.0, float(px2 - px1) * float(py2 - py1))
                for other in tracked_objects:
                    if other.get("class") == "forklift":
                        ox1, oy1, ox2, oy2 = other["bbox"]
                        ix1, iy1 = max(px1, ox1), max(py1, oy1)
                        ix2, iy2 = min(px2, ox2), min(py2, oy2)
                        inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
                        overlap = inter / p_area
                        if overlap > max_forklift_overlap:
                            max_forklift_overlap = overlap

            spatial_context = {"vehicle_overlap": max_forklift_overlap}
            
            # Retrieve prior track history if exists
            track_history = None
            if t_id in self.tracks:
                prev_track = self.tracks[t_id]
                track_history = {
                    "track_age": prev_track.get("track_age", 1),
                    "prior_pose_count": prev_track.get("prior_pose_count", 0)
                }

            # 1. Gate Check with multi-cue context
            validity = self.obs_gate.evaluate(
                obj["class"], 
                obj["bbox"], 
                obj.get("keypoints"),
                conf=conf,
                track_history=track_history,
                spatial_context=spatial_context
            )
            
            # An observation is strong if confidence is high OR pose is confirmed valid
            is_strong_observation = (conf >= self.strong_conf_threshold) or (validity == ObservationValidity.VALID)
            
            if t_id not in self.tracks:
                self.tracks[t_id] = {
                    "track_id": t_id,
                    "class": obj["class"],
                    "state": TrackState.OBSERVED if is_strong_observation else TrackState.PREDICTED,
                    "last_observed_frame": frame_idx if is_strong_observation else -1,
                    "frames_since_observation": 0 if is_strong_observation else 1,
                    "last_time_sec": time_sec,
                    "last_gp": None,
                    "speed_m_s": 0.0,
                    "validity_history": [],
                    "track_age": 1,
                    "prior_pose_count": 1 if hasattr(validity, "evidence") and validity.evidence.get("pose") == "strong" else 0
                }
            else:
                self.tracks[t_id]["track_age"] = self.tracks[t_id].get("track_age", 0) + 1
                if hasattr(validity, "evidence") and validity.evidence.get("pose") == "strong":
                    self.tracks[t_id]["prior_pose_count"] = self.tracks[t_id].get("prior_pose_count", 0) + 1
            
            track = self.tracks[t_id]
            track["validity_history"].append(validity)
            if len(track["validity_history"]) > 15:
                track["validity_history"].pop(0)
            
            # Drift Detection & Speed Calculation
            is_drift = False
            curr_gp = None
            if calibrator:
                curr_gp = calibrator.pixel_to_world(obj["px"])
                if curr_gp and track["last_gp"]:
                    dist_moved = math.hypot(curr_gp[0] - track["last_gp"][0], curr_gp[1] - track["last_gp"][1])
                    dt = time_sec - track["last_time_sec"]
                    if dt > 0:
                        raw_speed = dist_moved / dt
                        if raw_speed > self.max_drift_speed_m_s:
                            is_drift = True
                        else:
                            prev_speed = track.get("speed_m_s", 0.0)
                            track["speed_m_s"] = 0.6 * prev_speed + 0.4 * raw_speed
            
            if is_drift:
                track["state"] = TrackState.STALE
                track["frames_since_observation"] = self.max_prediction_frames + 1
            else:
                if is_strong_observation:
                    track["state"] = TrackState.OBSERVED
                    track["last_observed_frame"] = frame_idx
                    track["frames_since_observation"] = 0
                else:
                    if track["state"] == TrackState.OBSERVED:
                        track["state"] = TrackState.PREDICTED
                        
                    if track["state"] == TrackState.PREDICTED:
                        track["frames_since_observation"] += 1
                        if track["frames_since_observation"] >= self.max_prediction_frames:
                            track["state"] = TrackState.STALE
                            
            track["last_time_sec"] = time_sec
            track["last_gp"] = curr_gp
            
            # Determine overall validity (smoothing to avoid single-frame flickering)
            current_validity = validity
            
            # Safety Eligibility Contract
            # Section 9: PREDICTED != NEW SAFETY EVIDENCE.
            # A track born purely from low-confidence prediction (< threshold) without any strong observation
            # cannot create safety evidence. But a previously observed track in PREDICTED state retains eligibility.
            safety_eligible = False
            if track["state"] != TrackState.STALE:
                if track["last_observed_frame"] != -1:
                    if current_validity in [ObservationValidity.VALID, ObservationValidity.WEAK]:
                        safety_eligible = True
            
            # Motion State (Moving vs Parked/Static)
            speed_val = round(track.get("speed_m_s", 0.0), 2)
            is_moving = speed_val > 0.25
            
            # Augment object with state, speed, motion state, and full evidence
            obj["track_state"] = track["state"]
            obj["frames_since_observation"] = track["frames_since_observation"]
            obj["observation_validity"] = current_validity
            obj["safety_eligible"] = safety_eligible
            obj["speed_m_s"] = speed_val
            obj["is_moving"] = is_moving
            obj["motion_state"] = "MOVING" if is_moving else "PARKED"
            obj["evidence"] = getattr(validity, "evidence", {})
            obj["reason"] = getattr(validity, "reason", "")
            
            # Pass all tracks (so video can draw them), but safety_eligible controls interaction
            valid_objects.append(obj)
                
        # Clean up lost tracks
        for t_id in list(self.tracks.keys()):
            if t_id not in current_ids:
                del self.tracks[t_id]
                
        return valid_objects
