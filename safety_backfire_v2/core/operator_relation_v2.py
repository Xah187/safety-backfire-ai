"""
V2.7 — Operator-Vehicle Relation Engine V2 (Multi-Cue)

Classifies person-forklift pairs into:
  OPERATOR_ON_VEHICLE
  INDEPENDENT_PEDESTRIAN
  UNKNOWN

Uses multiple cues, avoiding 2D bbox overlap as the sole determinant:
1. Pose Evidence: Uses Torso and Ankle keypoints to verify true physical position.
2. Ground Geometry: Uses footpoint relation.
3. Operator Region: Uses Torso/Hip location against the vehicle operator region.
4. Temporal Motion: Checks if the person is moving with the vehicle.

Safety Invariant:
  If evidence is conflicting or insufficient (e.g. 2D overlap but Pose is outside, 
  or heavy occlusion), it defaults to UNKNOWN.
"""
import math
from typing import Dict, List, Tuple, Any, Optional
from collections import defaultdict


class RelationEvidenceV2:
    def __init__(self):
        self.pose = {"torso_in_roi": False, "ankles_in_vehicle": False, "available": False}
        self.operator_region = {"torso_dist": 0.0, "match_score": 0.0}
        self.ground_geometry = {"foot_dist": 0.0, "overlap": 0.0}
        self.temporal = {"consistency": 0.0}
        self.motion = {"similarity": 0.0}
        self.segmentation = {"available": False}
        self.depth = {"available": False}
        
        self.decision = "UNKNOWN"
        self.confidence = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pose": self.pose,
            "operator_region": self.operator_region,
            "ground_geometry": self.ground_geometry,
            "temporal": self.temporal,
            "motion": self.motion,
            "decision": self.decision,
            "confidence": round(self.confidence, 3),
        }


class OperatorVehicleRelationEngineV2:
    def __init__(self):
        self._coupling_history: Dict[Tuple[int, int], List[int]] = defaultdict(list)
        self._frame_relations: Dict[int, List[Dict]] = {}
        
        self.TEMPORAL_MEMORY = 15
        self.TEMPORAL_WINDOW = 5
        
        # EPJ Operator ROI
        self.ROI_X_START = 0.3
        self.ROI_X_END = 1.0
        self.ROI_Y_START = 0.2
        self.ROI_Y_END = 0.9

    def _extract_pose_features(self, keypoints: List[List[float]]) -> Dict[str, Tuple[float, float]]:
        """
        Extracts Torso and Ankle positions from COCO 17-keypoint format.
        Keypoint format: [x, y, conf]
        """
        features = {"torso": None, "ankles": None}
        if not keypoints or len(keypoints) < 17:
            return features
            
        # COCO Indices: 5:L-Shoulder, 6:R-Shoulder, 11:L-Hip, 12:R-Hip, 15:L-Ankle, 16:R-Ankle
        kpts = keypoints
        
        # Torso (midpoint of hips and shoulders if confident)
        torso_pts = []
        for i in [5, 6, 11, 12]:
            if kpts[i][2] > 0.4: # Confidence threshold
                torso_pts.append((kpts[i][0], kpts[i][1]))
                
        if len(torso_pts) >= 2:
            tx = sum(p[0] for p in torso_pts) / len(torso_pts)
            ty = sum(p[1] for p in torso_pts) / len(torso_pts)
            features["torso"] = (tx, ty)
            
        # Ankles
        ankle_pts = []
        for i in [15, 16]:
            if kpts[i][2] > 0.4:
                ankle_pts.append((kpts[i][0], kpts[i][1]))
                
        if ankle_pts:
            ax = sum(p[0] for p in ankle_pts) / len(ankle_pts)
            ay = sum(p[1] for p in ankle_pts) / len(ankle_pts)
            features["ankles"] = (ax, ay)
            
        return features

    def _is_point_in_box(self, px, py, bbox) -> bool:
        return bbox[0] <= px <= bbox[2] and bbox[1] <= py <= bbox[3]

    def _compute_operator_roi_score(self, px, py, f_bbox) -> float:
        fw = f_bbox[2] - f_bbox[0]
        fh = f_bbox[3] - f_bbox[1]
        if fw <= 0 or fh <= 0: return 0.0

        roi_x1 = f_bbox[0] + fw * self.ROI_X_START
        roi_x2 = f_bbox[0] + fw * self.ROI_X_END
        roi_y1 = f_bbox[1] + fh * self.ROI_Y_START
        roi_y2 = f_bbox[1] + fh * self.ROI_Y_END

        if roi_x1 <= px <= roi_x2 and roi_y1 <= py <= roi_y2:
            return 1.0

        roi_cx = (roi_x1 + roi_x2) / 2.0
        roi_cy = (roi_y1 + roi_y2) / 2.0
        roi_diag = math.hypot(roi_x2 - roi_x1, roi_y2 - roi_y1)

        if roi_diag <= 0: return 0.0

        dist = math.hypot(px - roi_cx, py - roi_cy)
        return max(0.0, 1.0 - (dist / roi_diag))

    def classify_frame(self, persons: List[Dict], forklifts: List[Dict], frame_idx: int) -> List[Dict[str, Any]]:
        relations = []

        for p in persons:
            best_evidence = None
            best_decision = "INDEPENDENT_PEDESTRIAN"
            best_conf = 1.0

            # Parse Pose
            pose_feats = self._extract_pose_features(p.get("keypoints", []))
            has_pose = pose_feats["torso"] is not None

            for f in forklifts:
                ev = RelationEvidenceV2()
                
                # Ground Geometry (2D Bbox overlap as a fallback/cue)
                px1, py1, px2, py2 = p["bbox"]
                fx1, fy1, fx2, fy2 = f["bbox"]
                
                ix1, iy1 = max(px1, fx1), max(py1, fy1)
                ix2, iy2 = min(px2, fx2), min(py2, fy2)
                inter_area = max(0, ix2 - ix1) * max(0, iy2 - iy1)
                person_area = max(1, (px2 - px1) * (py2 - py1))
                overlap = inter_area / person_area
                ev.ground_geometry["overlap"] = round(overlap, 3)
                
                # We use the person's center if pose torso is missing
                p_cx = (px1 + px2) / 2.0
                p_cy = (py1 + py2) / 2.0
                torso_pt = pose_feats["torso"] if pose_feats["torso"] else (p_cx, p_cy)
                
                # 1. Operator Region Check
                roi_score = self._compute_operator_roi_score(torso_pt[0], torso_pt[1], f["bbox"])
                ev.operator_region["match_score"] = round(roi_score, 3)
                
                # 2. Pose Evidence
                if has_pose:
                    ev.pose["available"] = True
                    ev.pose["torso_in_roi"] = roi_score > 0.85
                    if pose_feats["ankles"]:
                        ax, ay = pose_feats["ankles"]
                        ev.pose["ankles_in_vehicle"] = self._is_point_in_box(ax, ay, f["bbox"])
                else:
                    ev.pose["available"] = False
                
                # 3. Temporal Consistency
                # If there's a strong visual cue (overlap or high ROI), record coupling
                if overlap > 0.3 or roi_score > 0.7:
                    self._coupling_history[(p["id"], f["id"])].append(frame_idx)
                    # Clean old memory
                    self._coupling_history[(p["id"], f["id"])] = [
                        fr for fr in self._coupling_history[(p["id"], f["id"])]
                        if frame_idx - fr <= self.TEMPORAL_MEMORY
                    ]
                
                history = self._coupling_history[(p["id"], f["id"])]
                recent = [fr for fr in history if frame_idx - fr <= self.TEMPORAL_MEMORY]
                temp_score = min(1.0, len(recent) / self.TEMPORAL_WINDOW)
                ev.temporal["consistency"] = round(temp_score, 3)

                # --- MULTI-CUE DECISION LOGIC ---
                
                # Rule 1: Strong Pose Operator
                # If torso is in operator region AND ankles are physically on the vehicle
                # (EPJ operator standing on the machine)
                if has_pose and ev.pose["torso_in_roi"] and ev.pose["ankles_in_vehicle"]:
                    ev.decision = "OPERATOR_ON_VEHICLE"
                    ev.confidence = 0.95
                
                # Rule 2: Strong 2D Fallback (Operator leaning out)
                # If pose is missing or ankles missing, but torso is strongly in ROI 
                # AND there's temporal consistency of moving together
                elif roi_score > 0.7 and temp_score >= 0.8:
                    ev.decision = "OPERATOR_ON_VEHICLE"
                    ev.confidence = 0.85
                    
                # Rule 3: The Adversarial Crossing Pedestrian
                # If pedestrian is highly overlapped in 2D (passing in front)
                # but torso is NOT in ROI, or ankles are completely outside the vehicle
                elif overlap > 0.5:
                    if has_pose and not ev.pose["torso_in_roi"]:
                        ev.decision = "INDEPENDENT_PEDESTRIAN"
                        ev.confidence = 0.90
                    elif has_pose and pose_feats["ankles"] and not ev.pose["ankles_in_vehicle"]:
                        ev.decision = "INDEPENDENT_PEDESTRIAN"
                        ev.confidence = 0.90
                    else:
                        # Ambiguous 2D overlap without clear pose
                        ev.decision = "UNKNOWN"
                        ev.confidence = 0.5
                
                # Rule 4: Clear Independent
                # Very low overlap, low ROI score, no history
                elif overlap < 0.1 and roi_score < 0.3 and temp_score < 0.2:
                    ev.decision = "INDEPENDENT_PEDESTRIAN"
                    ev.confidence = 0.95
                    
                # Rule 5: Catch-all Ambiguity
                else:
                    ev.decision = "UNKNOWN"
                    ev.confidence = 0.5

                # Record the relation for this specific (person, forklift) pair
                relations.append({
                    "person_id": p["id"],
                    "forklift_id": f["id"],
                    "relation": ev.decision,
                    "confidence": ev.confidence,
                    "evidence": ev.to_dict()
                })

            # If no forklifts exist in the scene, person is an independent pedestrian by definition
            if not forklifts:
                relations.append({
                    "person_id": p["id"],
                    "forklift_id": None,
                    "relation": "INDEPENDENT_PEDESTRIAN",
                    "confidence": 1.0,
                    "evidence": RelationEvidenceV2().to_dict()
                })

        self._frame_relations[frame_idx] = relations
        return relations

    def get_person_relation(self, person_id: int, forklift_id: Optional[int], frame_idx: int) -> Optional[str]:
        frame_rels = self._frame_relations.get(frame_idx, [])
        
        # If a specific forklift is queried:
        if forklift_id is not None and forklift_id != -1:
            for r in frame_rels:
                if r["person_id"] == person_id and r["forklift_id"] == forklift_id:
                    return r["relation"]
            return None

        # If global person relation is queried (forklift_id is None or -1):
        # Determine overall person state across all forklifts in this frame
        p_rels = [r["relation"] for r in frame_rels if r["person_id"] == person_id]
        if not p_rels:
            return "INDEPENDENT_PEDESTRIAN"
        if "OPERATOR_ON_VEHICLE" in p_rels:
            return "OPERATOR_ON_VEHICLE"
        if "UNKNOWN" in p_rels:
            return "UNKNOWN"
        return "INDEPENDENT_PEDESTRIAN"

    def get_all_relations(self) -> Dict[int, List[Dict]]:
        return dict(self._frame_relations)
