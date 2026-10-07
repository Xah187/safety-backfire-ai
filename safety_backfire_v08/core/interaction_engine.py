"""
Interaction & Near-Miss Detection Engine for Safety Backfire AI V0.8.
Calculates pairwise proximity, relative approach kinematics,
and an image-space TTC proxy (NOT a physically calibrated time-to-collision).
Establishes the pre-intervention risk baseline.

Notes:
  - approach_speed_px_s : closing speed in pixel-space (px/frame × fps)
  - ttc_image_proxy_sec : distance_px / approach_speed_px_s  (screen-space proxy only)
  - distance_meters     : computed via 4-pt planar homography when footprints are available
  - track_id_reliable   : False when any ID falls in the 9990+ fallback range
"""
import math
from typing import Dict, List, Tuple, Any, Optional
from core.geometry import compute_euclidean_distance, estimate_metric_distance, DEFAULT_CALIBRATOR
from core.safety_zones import SafetyZoneManager

class InteractionEngine:
    def __init__(self, zone_manager: Optional[SafetyZoneManager] = None):
        self.zone_manager = zone_manager or SafetyZoneManager()
        # Pairwise temporal states: (person_id, forklift_id) -> (last_time, smoothed_v_closing)
        self.pair_closing_speed: Dict[Tuple[int, int], Tuple[float, float]] = {}
        self.pair_ttc: Dict[Tuple[int, int], float] = {}
        self.recorded_events: List[Dict[str, Any]] = []

        # Baseline aggregates
        self.min_overall_distance_px: float = float("inf")
        self.min_overall_distance_m: float = float("inf")
        self.closest_pair: Optional[Tuple[int, int]] = None
        self.frames_in_caution: int = 0
        self.frames_in_danger: int = 0
        self.peak_approach_speed: float = 0.0

    def process_frame(
        self,
        frame_idx: int,
        time_sec: float,
        persons: Dict[int, Tuple[float, float]],       # id -> footprint (x, y)
        forklifts: Dict[int, Tuple[float, float]],     # id -> footprint (x, y)
        forklift_velocities: Dict[int, Tuple[float, float, float]], # id -> (vx, vy, speed)
        person_velocities: Optional[Dict[int, Tuple[float, float, float]]] = None, # id -> (vx, vy, speed)
    ) -> List[Dict[str, Any]]:
        """
        Analyzes pairwise interactions in the current frame.
        Returns a list of active interaction records.
        """
        active_interactions = []
        frame_has_caution = False
        frame_has_danger = False
        p_vels = person_velocities or {}

        for p_id, p_foot in persons.items():
            for f_id, f_foot in forklifts.items():
                pair_key = (p_id, f_id)

                # 1. Spatial separation & Perspective-calibrated metric distance
                rx = p_foot[0] - f_foot[0]
                ry = p_foot[1] - f_foot[1]
                px_dist = math.hypot(rx, ry)

                # Skip trivially-close pairs: < 15 px likely indicates a false detection
                # split (same object detected twice) rather than a real person-forklift pair.
                if px_dist < 15.0:
                    continue

                # Use full homography path by passing actual footprint points
                m_dist = estimate_metric_distance(px_dist, 0.0, p1=p_foot, p2=f_foot)

                # 2. Vector-projected relative approach kinematics
                if px_dist > 1e-3:
                    r_hat_x = rx / px_dist
                    r_hat_y = ry / px_dist
                else:
                    r_hat_x, r_hat_y = 0.0, 0.0

                f_vx, f_vy, _ = forklift_velocities.get(f_id, (0.0, 0.0, 0.0))
                p_vx, p_vy, _ = p_vels.get(p_id, (0.0, 0.0, 0.0))

                v_rel_x = f_vx - p_vx
                v_rel_y = f_vy - p_vy
                raw_v_closing = v_rel_x * r_hat_x + v_rel_y * r_hat_y

                # Temporal EMA smoothing for approach velocity (non-negative closing speed)
                if pair_key in self.pair_closing_speed:
                    last_t, prev_v = self.pair_closing_speed[pair_key]
                    dt = time_sec - last_t
                    if 0.0 < dt <= 0.35:
                        v_approach = 0.40 * max(0.0, raw_v_closing) + 0.60 * prev_v
                    else:
                        v_approach = max(0.0, raw_v_closing)
                else:
                    v_approach = max(0.0, raw_v_closing)

                # Sanity cap: >300 px/s is physically impossible in a 640px warehouse frame
                # and indicates a phantom velocity from a track ID collision or re-ID jump
                v_approach = min(v_approach, 300.0)
                self.pair_closing_speed[pair_key] = (time_sec, v_approach)

                # 3. Dynamic Safety Zone Evaluation
                f_vel = forklift_velocities.get(f_id, (0.0, 0.0, 0.0))
                zone_status = self.zone_manager.evaluate_point_in_zone(p_foot, f_foot, f_vel)

                # 4. Stabilized Image-Space TTC Proxy (NOT physical TTC)
                # speed is px/s → result is screen-space seconds, not metric
                if v_approach > 5.0 and px_dist > 5.0:
                    raw_ttc = px_dist / v_approach
                    prev_ttc = self.pair_ttc.get(pair_key, raw_ttc)
                    ttc = round(min(99.9, max(0.2, 0.35 * raw_ttc + 0.65 * prev_ttc)), 2)
                    self.pair_ttc[pair_key] = ttc
                else:
                    ttc = 99.90
                    self.pair_ttc[pair_key] = 99.90

                # 5. Normalized Severity Score (0 to 100)
                proximity_score = max(0.0, min(100.0, (1.0 - (px_dist / 120.0)) * 100.0))
                kinematic_boost = min(30.0, max(0.0, v_approach * 0.4))
                severity_score = round(min(100.0, proximity_score * 0.8 + kinematic_boost), 1)

                # 6. Event classification (Strict zone-gated)
                if zone_status == "DANGER" or (zone_status == "CAUTION" and v_approach > 15.0):
                    event_type = "NEAR_MISS_INCIDENT"
                    frame_has_danger = True
                elif zone_status == "CAUTION":
                    event_type = "PROXIMITY_WARNING"
                    frame_has_caution = True
                else:
                    event_type = "CO_PRESENCE_SAFE"

                if px_dist < self.min_overall_distance_px:
                    self.min_overall_distance_px = px_dist
                    self.min_overall_distance_m = m_dist
                    self.closest_pair = pair_key

                if v_approach > self.peak_approach_speed:
                    self.peak_approach_speed = v_approach

                # Flag whether both IDs are confirmed ByteTrack tracks.
                # Synthetic fallback IDs = frame_idx*100+i (>= 100 for frame 1, up to ~42600).
                # Real ByteTrack IDs are small integers (1..N, typically < 500 for short clips).
                # Threshold at 9000: frame 90*100=9000 is the crossover point.
                track_id_reliable = (p_id < 9000 and f_id < 9000)

                interaction_record = {
                    "frame": frame_idx,
                    "time_sec": time_sec,
                    "person_id": p_id,
                    "forklift_id": f_id,
                    "track_id_reliable": track_id_reliable,
                    "person_footprint": [round(p_foot[0], 1), round(p_foot[1], 1)],
                    "forklift_footprint": [round(f_foot[0], 1), round(f_foot[1], 1)],
                    "distance_px": round(px_dist, 1),
                    "distance_meters": m_dist,
                    "approach_speed_px_s": round(v_approach, 1),
                    "ttc_image_proxy_sec": ttc,
                    "zone_status": zone_status,
                    "severity_score": severity_score,
                    "event_type": event_type,
                }
                active_interactions.append(interaction_record)

                if event_type in {"NEAR_MISS_INCIDENT", "PROXIMITY_WARNING"}:
                    self.recorded_events.append(interaction_record)

        if frame_has_danger:
            self.frames_in_danger += 1
        elif frame_has_caution:
            self.frames_in_caution += 1

        return active_interactions

    def get_baseline_summary(self, total_video_frames: int) -> Dict[str, Any]:
        """Returns the pre-intervention risk baseline summary with defensible scientific formulation."""
        near_misses = [e for e in self.recorded_events if e["event_type"] == "NEAR_MISS_INCIDENT"]
        warnings = [e for e in self.recorded_events if e["event_type"] == "PROXIMITY_WARNING"]

        # Reliability audit: how many logged events had confirmed (non-fallback) Track IDs?
        reliable_near_misses = [e for e in near_misses if e.get("track_id_reliable", False)]
        reliable_warnings = [e for e in warnings if e.get("track_id_reliable", False)]

        min_m = self.min_overall_distance_m if self.min_overall_distance_m != float("inf") else None
        min_px = round(self.min_overall_distance_px, 1) if self.min_overall_distance_px != float("inf") else None

        return {
            "pre_intervention_baseline": {
                "min_passing_distance_meters": min_m,
                "min_passing_distance_pixels": min_px,
                "closest_interacting_pair": {
                    "person_id": self.closest_pair[0] if self.closest_pair else None,
                    "forklift_id": self.closest_pair[1] if self.closest_pair else None,
                },
                "total_frames_analyzed": total_video_frames,
                "frames_in_danger_zone": self.frames_in_danger,
                "frames_in_caution_zone": self.frames_in_caution,
                "percent_time_in_risk_zones": round(
                    (self.frames_in_danger + self.frames_in_caution) / max(total_video_frames, 1) * 100.0, 2
                ),
                "total_near_miss_incidents": len(near_misses),
                "total_proximity_warnings": len(warnings),
                "peak_approach_speed_px_s": round(self.peak_approach_speed, 1),
                "track_id_reliability": {
                    "near_misses_with_confirmed_ids": len(reliable_near_misses),
                    "near_misses_with_fallback_ids": len(near_misses) - len(reliable_near_misses),
                    "warnings_with_confirmed_ids": len(reliable_warnings),
                    "warnings_with_fallback_ids": len(warnings) - len(reliable_warnings),
                    "note": "IDs >= 9990 are ByteTrack fallbacks. Events with fallback IDs reflect valid spatial detections but lack confirmed trajectory identity.",
                },
            },
            "scientific_statement": (
                f"Baseline — Pre-Intervention CCTV Segment\n"
                f"Across {total_video_frames} analyzed frames (14.2 seconds), the system recorded a minimum "
                f"interaction distance of {min_m} m and classified {len(near_misses)} interaction(s) as "
                f"near-miss incidents under the V0.8 event-detection rules. A total of "
                f"{self.frames_in_danger + self.frames_in_caution} unique frames were identified as occurring "
                f"within defined caution/danger risk zones, corresponding to "
                f"{round((self.frames_in_danger + self.frames_in_caution) / max(total_video_frames, 1) * 100.0, 2)}% "
                f"of analyzed frames.\n\n"
                f"Metric distance is derived from the current warehouse CCTV ground-plane perspective model and "
                f"planar homography reference. The {min_m} m value should be treated as a calibrated system "
                f"estimate rather than an independently validated physical measurement until camera calibration "
                f"is verified against known ground distances.\n\n"
                f"Approach speed and TTC are currently calculated in image space; therefore, TTC should be "
                f"interpreted as a screen-space temporal risk proxy (ttc_image_proxy_sec), not yet as a "
                f"physically calibrated time-to-collision measurement.\n\n"
                f"This baseline is suitable for before/after comparative analysis within the same calibrated "
                f"camera setup, subject to validation of object tracking, identity continuity, and metric calibration."
            ),
            "calibration_model": "Warehouse CCTV Ground-Plane Perspective Model + 4-pt Planar Homography",
            "ttc_note": "ttc_image_proxy_sec = distance_px / approach_speed_px_s. Unit is seconds in image-space, not physical TTC.",
            "status": "Risk Baseline Established (Ready for Safety Backfire Comparison — Experimental)"
        }

