"""
V2.5 — Operator-Vehicle Relation Engine

Classifies each person-forklift pair as:
  OPERATOR_ON_VEHICLE    — person is riding/operating the forklift
  INDEPENDENT_PEDESTRIAN — person is separate from the forklift
  UNKNOWN                — insufficient evidence to decide

Uses 4 weighted signals:
  1. Spatial Containment   (weight=0.30) — person bbox inside forklift bbox
  2. Operator ROI Match    (weight=0.25) — person center in operator seat region
  3. Temporal Consistency   (weight=0.25) — coupling sustained over N frames
  4. Motion Similarity      (weight=0.20) — similar velocity/direction

Decision thresholds:
  score >= 0.65 → OPERATOR_ON_VEHICLE
  score <= 0.35 → INDEPENDENT_PEDESTRIAN
  otherwise     → UNKNOWN

IMPORTANT: This engine does NOT delete person detections.
           It only annotates them with relation metadata.
"""
import math
from typing import Dict, List, Tuple, Any, Optional
from collections import defaultdict


class RelationEvidence:
    """Stores the evidence for a single person-forklift relation decision."""
    def __init__(self):
        self.spatial_containment: float = 0.0
        self.operator_roi_match: float = 0.0
        self.temporal_consistency: float = 0.0
        self.motion_similarity: float = 0.0
        self.weighted_score: float = 0.0
        self.decision: str = "UNKNOWN"
        self.confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "spatial_containment": round(self.spatial_containment, 3),
            "operator_roi_match": round(self.operator_roi_match, 3),
            "temporal_consistency": round(self.temporal_consistency, 3),
            "motion_similarity": round(self.motion_similarity, 3),
            "weighted_score": round(self.weighted_score, 3),
            "decision": self.decision,
            "confidence": round(self.confidence, 3),
        }


class OperatorVehicleRelationEngine:
    """
    Classifies person-forklift pairs into OPERATOR_ON_VEHICLE,
    INDEPENDENT_PEDESTRIAN, or UNKNOWN based on multi-signal analysis.
    """

    # Signal weights
    W_SPATIAL = 0.30
    W_ROI = 0.25
    W_TEMPORAL = 0.25
    W_MOTION = 0.20

    # Decision thresholds
    OPERATOR_THRESHOLD = 0.65
    PEDESTRIAN_THRESHOLD = 0.35

    # Temporal consistency parameters
    TEMPORAL_WINDOW = 5  # frames of consistent coupling required
    TEMPORAL_MEMORY = 15  # frames to remember coupling history

    # Operator ROI: rear portion of forklift bbox
    OPERATOR_ROI_X_START = 0.3   # start at 30% from left of forklift bbox
    OPERATOR_ROI_X_END = 1.0     # extend to right edge
    OPERATOR_ROI_Y_START = 0.2   # start at 20% from top
    OPERATOR_ROI_Y_END = 0.9     # extend to 90% from top

    def __init__(self):
        # Coupling history: (person_id, forklift_id) -> list of frame_idx where coupled
        self._coupling_history: Dict[Tuple[int, int], List[int]] = defaultdict(list)
        # Per-frame relation results for audit trail
        self._frame_relations: Dict[int, List[Dict]] = {}

    def _compute_containment_ratio(self, person_bbox: List[int],
                                    forklift_bbox: List[int]) -> float:
        """
        Compute what fraction of the person bbox area lies inside the forklift bbox.
        This is NOT IoU — it measures containment of person within forklift.
        Returns 0.0 to 1.0.
        """
        px1, py1, px2, py2 = person_bbox
        fx1, fy1, fx2, fy2 = forklift_bbox

        # Intersection
        ix1 = max(px1, fx1)
        iy1 = max(py1, fy1)
        ix2 = min(px2, fx2)
        iy2 = min(py2, fy2)

        inter_area = max(0, ix2 - ix1) * max(0, iy2 - iy1)
        person_area = max(1, (px2 - px1) * (py2 - py1))

        return inter_area / person_area

    def _compute_operator_roi_score(self, person_bbox: List[int],
                                     forklift_bbox: List[int]) -> float:
        """
        Check if the person's center falls within the estimated operator
        seat region of the forklift.
        Returns 0.0 or 1.0 (binary) with distance-based soft margin.
        """
        # Person center
        pcx = (person_bbox[0] + person_bbox[2]) / 2.0
        pcy = (person_bbox[1] + person_bbox[3]) / 2.0

        # Forklift dimensions
        fw = forklift_bbox[2] - forklift_bbox[0]
        fh = forklift_bbox[3] - forklift_bbox[1]

        if fw <= 0 or fh <= 0:
            return 0.0

        # Operator ROI in absolute coordinates
        roi_x1 = forklift_bbox[0] + fw * self.OPERATOR_ROI_X_START
        roi_x2 = forklift_bbox[0] + fw * self.OPERATOR_ROI_X_END
        roi_y1 = forklift_bbox[1] + fh * self.OPERATOR_ROI_Y_START
        roi_y2 = forklift_bbox[1] + fh * self.OPERATOR_ROI_Y_END

        # Check if person center is inside ROI
        if roi_x1 <= pcx <= roi_x2 and roi_y1 <= pcy <= roi_y2:
            return 1.0

        # Soft margin: compute normalized distance to ROI center
        roi_cx = (roi_x1 + roi_x2) / 2.0
        roi_cy = (roi_y1 + roi_y2) / 2.0
        max_dist = 1000  # Increased to allow for very long EPJ vehicles
        roi_diag = max_dist

        if roi_diag <= 0:
            return 0.0

        dist_to_roi = math.hypot(pcx - roi_cx, pcy - roi_cy)
        # Score decays linearly outside ROI, reaches 0 at 2x ROI diagonal
        score = max(0.0, 1.0 - (dist_to_roi / (roi_diag * 2.0)))
        return score

    def _compute_temporal_consistency(self, person_id: int, forklift_id: int,
                                       frame_idx: int) -> float:
        """
        Check how consistently this person-forklift pair has been
        spatially coupled over recent frames.
        Returns 0.0 to 1.0.
        """
        key = (person_id, forklift_id)
        history = self._coupling_history[key]

        if not history:
            return 0.0

        # Count recent consecutive frames with coupling
        # Look back up to TEMPORAL_MEMORY frames
        recent = [f for f in history if frame_idx - f <= self.TEMPORAL_MEMORY]

        if not recent:
            return 0.0

        # Count frames within the window that are consecutive or near-consecutive
        consecutive = 0
        for i in range(len(recent) - 1, -1, -1):
            if frame_idx - recent[i] <= (len(recent) - i + 1):
                consecutive += 1
            else:
                break

        # Normalize by temporal window
        score = min(1.0, consecutive / self.TEMPORAL_WINDOW)
        return score

    def _compute_motion_similarity(self, person_vel: Tuple[float, float],
                                    forklift_vel: Tuple[float, float]) -> float:
        """
        Compare velocity vectors of person and forklift.
        High similarity → likely same moving unit.
        Returns 0.0 to 1.0.
        """
        pvx, pvy = person_vel
        fvx, fvy = forklift_vel

        p_speed = math.hypot(pvx, pvy)
        f_speed = math.hypot(fvx, fvy)

        # If both are nearly stationary, motion similarity is ambiguous
        if p_speed < 0.1 and f_speed < 0.1:
            return 0.5  # Neutral — can't determine from motion alone

        # If only one is moving, they are likely independent
        if (p_speed < 0.1) != (f_speed < 0.1):
            return 0.1

        # Speed ratio (closer to 1.0 = more similar)
        max_speed = max(p_speed, f_speed)
        min_speed = min(p_speed, f_speed)
        speed_ratio = min_speed / max_speed if max_speed > 0 else 0.0

        # Direction similarity (cosine similarity)
        dot = pvx * fvx + pvy * fvy
        cos_sim = dot / (p_speed * f_speed) if (p_speed > 0 and f_speed > 0) else 0.0
        # Normalize from [-1, 1] to [0, 1]
        direction_sim = (cos_sim + 1.0) / 2.0

        # Combined motion score
        return 0.5 * speed_ratio + 0.5 * direction_sim

    def classify_frame(self, persons: List[Dict], forklifts: List[Dict],
                       frame_idx: int) -> List[Dict[str, Any]]:
        """
        Classify all person-forklift pairs in a single frame.

        Each person/forklift dict should have:
          id: int (track_id)
          bbox: [x1, y1, x2, y2]
          vel: (vx, vy) — world velocity
          px: (cx, foot_y) — pixel footpoint

        Returns list of relation records:
          {
            "person_id": int,
            "forklift_id": int,
            "relation": str,
            "confidence": float,
            "evidence": dict,
          }
        """
        relations = []

        for p in persons:
            best_score = -1.0
            best_relation = None

            for f in forklifts:
                evidence = RelationEvidence()

                # Signal 1: Spatial containment
                containment = self._compute_containment_ratio(p["bbox"], f["bbox"])
                evidence.spatial_containment = containment

                # Signal 2: Operator ROI
                roi_score = self._compute_operator_roi_score(p["bbox"], f["bbox"])
                evidence.operator_roi_match = roi_score

                # Signal 3: Temporal consistency
                # First update coupling history based on spatial signal
                if containment > 0.3:
                    self._coupling_history[(p["id"], f["id"])].append(frame_idx)
                    # Trim old entries
                    key = (p["id"], f["id"])
                    self._coupling_history[key] = [
                        fr for fr in self._coupling_history[key]
                        if frame_idx - fr <= self.TEMPORAL_MEMORY
                    ]

                temporal = self._compute_temporal_consistency(p["id"], f["id"], frame_idx)
                evidence.temporal_consistency = temporal

                # Signal 4: Motion similarity
                motion = self._compute_motion_similarity(
                    p.get("vel", (0, 0)), f.get("vel", (0, 0))
                )
                evidence.motion_similarity = motion

                # Weighted score
                score = (
                    self.W_SPATIAL * containment +
                    self.W_ROI * roi_score +
                    self.W_TEMPORAL * temporal +
                    self.W_MOTION * motion
                )
                evidence.weighted_score = score

                # Decision
                # Fast-track: if spatial containment is high and ROI is at least moderate,
                # immediately classify as operator. (Crucial for EPJ where operators move around)
                if containment > 0.7 and roi_score > 0.6:
                    evidence.decision = "OPERATOR_ON_VEHICLE"
                    evidence.confidence = 1.0
                elif score >= self.OPERATOR_THRESHOLD:
                    evidence.decision = "OPERATOR_ON_VEHICLE"
                    evidence.confidence = min(1.0, score / self.OPERATOR_THRESHOLD)
                elif score <= self.PEDESTRIAN_THRESHOLD:
                    evidence.decision = "INDEPENDENT_PEDESTRIAN"
                    evidence.confidence = min(1.0, (1.0 - score) / (1.0 - self.PEDESTRIAN_THRESHOLD))
                else:
                    evidence.decision = "UNKNOWN"
                    # Confidence for UNKNOWN is low by definition
                    evidence.confidence = 0.3

                if score > best_score:
                    best_score = score
                    best_relation = {
                        "person_id": p["id"],
                        "forklift_id": f["id"],
                        "relation": evidence.decision,
                        "confidence": round(evidence.confidence, 3),
                        "evidence": evidence.to_dict(),
                    }

            if best_relation is not None:
                relations.append(best_relation)
            else:
                # Person with no forklift nearby → independent by default
                relations.append({
                    "person_id": p["id"],
                    "forklift_id": None,
                    "relation": "INDEPENDENT_PEDESTRIAN",
                    "confidence": 1.0,
                    "evidence": {
                        "spatial_containment": 0.0,
                        "operator_roi_match": 0.0,
                        "temporal_consistency": 0.0,
                        "motion_similarity": 0.0,
                        "weighted_score": 0.0,
                        "decision": "INDEPENDENT_PEDESTRIAN",
                        "confidence": 1.0,
                    }
                })

        self._frame_relations[frame_idx] = relations
        return relations

    def get_person_relation(self, person_id: int, forklift_id: int,
                            frame_idx: int) -> Optional[str]:
        """Get the relation for a specific person-forklift pair at a frame."""
        frame_rels = self._frame_relations.get(frame_idx, [])
        for r in frame_rels:
            if r["person_id"] == person_id and r["forklift_id"] == forklift_id:
                return r["relation"]
        return None

    def get_all_relations(self) -> Dict[int, List[Dict]]:
        """Return all frame-level relation records for audit."""
        return dict(self._frame_relations)

    def get_summary(self) -> Dict[str, int]:
        """Summary statistics across all processed frames."""
        counts = {"OPERATOR_ON_VEHICLE": 0, "INDEPENDENT_PEDESTRIAN": 0, "UNKNOWN": 0}
        for frame_rels in self._frame_relations.values():
            for r in frame_rels:
                rel = r["relation"]
                if rel in counts:
                    counts[rel] += 1
        return counts
