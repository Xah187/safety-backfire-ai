from typing import Dict, List, Any, Optional, Tuple

class ObservationValidity:
    VALID = "VALID"
    WEAK = "WEAK"
    INVALID = "INVALID"


class ObservationDecision(str):
    """
    Subclasses str to remain 100% backward compatible with existing code
    that checks `decision == ObservationValidity.VALID` or `decision in [...]`,
    while enriching each decision with multi-cue evidence and safety eligibility.
    """
    def __new__(cls, validity: str, safety_eligible: bool, evidence: Dict[str, Any], reason: str):
        instance = super().__new__(cls, validity)
        instance.validity = validity
        instance.safety_eligible = safety_eligible
        instance.evidence = evidence
        instance.reason = reason
        return instance

    def to_dict(self) -> Dict[str, Any]:
        return {
            "observation_validity": self.validity,
            "safety_eligible": self.safety_eligible,
            "evidence": self.evidence,
            "reason": self.reason
        }


class ObservationIntegrityGate:
    """
    Evaluates multi-cue physical, visual, geometric, and temporal evidence 
    of an observation.
    
    Prevents false detections (e.g. forklift parts, reflections) from entering 
    the safety engine, while rigorously preserving real persons with weak evidence 
    (occluded, distant, missing pose) to prevent safety-critical false negatives.
    """
    def __init__(self, 
                 min_valid_kpts: int = 2, 
                 max_vehicle_hallucination_area: int = 150000, 
                 min_human_aspect: float = 1.0, 
                 max_human_aspect: float = 4.5):
        self.min_valid_kpts = min_valid_kpts
        self.max_vehicle_hallucination_area = max_vehicle_hallucination_area
        self.min_human_aspect = min_human_aspect
        self.max_human_aspect = max_human_aspect

    def evaluate(self, 
                 obj_class: str, 
                 bbox: list, 
                 keypoints: list = None,
                 conf: float = 0.5,
                 track_history: Optional[Dict[str, Any]] = None,
                 spatial_context: Optional[Dict[str, Any]] = None) -> ObservationDecision:
        """
        Evaluates the multi-cue evidence of an observation.
        Returns an ObservationDecision string with attached evidence.
        """
        # 1. Non-person classes (forklifts, etc.) are valid by definition
        if obj_class != "person":
            ev = {"class": obj_class, "reason": "non_person_entity"}
            return ObservationDecision(ObservationValidity.VALID, True, ev, "Non-person object is valid by default")

        x1, y1, x2, y2 = bbox
        width = max(1.0, float(x2 - x1))
        height = max(1.0, float(y2 - y1))
        area = width * height
        aspect_ratio = height / width

        # A. Pose Evidence
        visible_kpts = 0
        if keypoints is not None:
            for kpt in keypoints:
                if len(kpt) >= 3 and kpt[2] > 0.4:
                    visible_kpts += 1

        if visible_kpts >= self.min_valid_kpts:
            pose_status = "strong"
        elif visible_kpts == 1:
            pose_status = "partial"
        else:
            pose_status = "none"

        # B. Geometric Evidence
        if aspect_ratio < self.min_human_aspect:
            geo_status = "incompatible_horizontal"
        elif aspect_ratio > self.max_human_aspect:
            geo_status = "incompatible_needle"
        elif aspect_ratio >= 1.3:
            geo_status = "compatible_slender"
        else:
            geo_status = "compatible_compact"

        # C. Temporal / Track History Evidence
        temporal_status = "new_observation"
        prior_pose_count = 0
        track_age = 0
        if track_history:
            track_age = track_history.get("track_age", 0)
            prior_pose_count = track_history.get("prior_pose_count", 0)
            if prior_pose_count > 0:
                temporal_status = "established_human_track"
            elif track_age >= 5:
                temporal_status = "persistent_track"

        # D. Spatial Context (Vehicle Overlap / Coupling)
        spatial_status = "independent"
        is_vehicle_overlap = False
        vehicle_overlap_ratio = 0.0
        if spatial_context:
            vehicle_overlap_ratio = spatial_context.get("vehicle_overlap", 0.0)
            if vehicle_overlap_ratio > 0.6:
                is_vehicle_overlap = True
                spatial_status = "heavy_vehicle_overlap"

        evidence = {
            "pose": pose_status,
            "visible_kpts": visible_kpts,
            "geometry": geo_status,
            "aspect_ratio": round(aspect_ratio, 2),
            "area_px": int(area),
            "temporal": temporal_status,
            "track_age": track_age,
            "spatial": spatial_status,
            "conf": round(conf, 3)
        }

        # --- MULTI-CUE INTEGRITY DECISION MATRIX ---

        # Rule 1: Strong Pose Evidence -> VALID
        # Visible human joints form indisputable proof of a human body
        if pose_status == "strong":
            return ObservationDecision(
                ObservationValidity.VALID, 
                True, 
                evidence, 
                f"Confirmed human pose ({visible_kpts} visible keypoints)"
            )

        # Rule 2: Established Human Track under Temporary Occlusion -> VALID / WEAK
        # If this track already had confirmed pose in previous frames, a momentary occlusion
        # does NOT invalidate the person!
        if temporal_status == "established_human_track":
            validity = ObservationValidity.VALID if pose_status == "partial" else ObservationValidity.WEAK
            return ObservationDecision(
                validity,
                True,
                evidence,
                "Temporarily occluded person with confirmed prior track history"
            )

        # Rule 3: Extreme Geometry Filtering & Man-Down Protection
        # Needle-like vertical artifacts (aspect > 4.5) without pose are mast/pole hallucinations -> INVALID
        if geo_status == "incompatible_needle":
            return ObservationDecision(
                ObservationValidity.INVALID,
                False,
                evidence,
                f"Impossible vertical needle aspect ratio ({aspect_ratio:.2f}) with no pose"
            )
            
        # Horizontal aspect ratio (< 1.0):
        # If heavily coupled with a vehicle chassis -> INVALID (wheel/shadow ghost)
        # BUT if independent on the floor -> WEAK with safety_eligible = True (Man Down / Fallen Worker!)
        if geo_status == "incompatible_horizontal":
            if is_vehicle_overlap or area > 80000:
                return ObservationDecision(
                    ObservationValidity.INVALID,
                    False,
                    evidence,
                    f"Horizontal vehicle artifact/shadow on chassis (aspect={aspect_ratio:.2f})"
                )
            else:
                return ObservationDecision(
                    ObservationValidity.WEAK,
                    True,
                    evidence,
                    f"Fallen or crouching worker candidate (Man Down aspect={aspect_ratio:.2f}); preserved for safety"
                )

        # Rule 4: Massive Vehicle Body Hallucination -> INVALID
        # A large detection with zero pose, boxy/wide aspect ratio, and no prior pose history
        # is a hallucination of the vehicle chassis (e.g. P18, P89, P108)
        if pose_status == "none" and temporal_status != "established_human_track":
            # Condition A: Boxy aspect ratio (< 1.7) AND large size (height > 350 or area > 100k px)
            is_large_boxy = (aspect_ratio < 1.7 and (height > 350 or area > 100000))
            # Condition B: High overlap with vehicle
            is_rigid_vehicle_ghost = (is_vehicle_overlap and (area > 50000 or aspect_ratio < 1.5))
            
            if is_large_boxy or is_rigid_vehicle_ghost:
                return ObservationDecision(
                    ObservationValidity.INVALID,
                    False,
                    evidence,
                    f"Vehicle body / bulky artifact without pose (area={int(area)}px, aspect={aspect_ratio:.2f})"
                )

        # Rule 5: Real Human with Weak Evidence (Occlusion, Distant, Facing Away) -> WEAK
        # Human proportion is maintained (aspect >= 1.0, not a forklift body)
        # MUST remain safety eligible (safety_eligible = True) to prevent false negatives!
        return ObservationDecision(
            ObservationValidity.WEAK,
            True,
            evidence,
            f"Human-compatible geometry ({aspect_ratio:.2f}) with weak/occluded pose; eligible for safety"
        )

    def evaluate_detection(self, 
                           detection: Dict[str, Any], 
                           track_info: Optional[Dict[str, Any]] = None, 
                           spatial_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Public contract API returning explicit decoupled dictionary:
        {
          "class": "PERSON",
          "observation_validity": "WEAK",
          "safety_eligible": true,
          "evidence": {...},
          "reason": "..."
        }
        """
        decision = self.evaluate(
            obj_class=detection.get("class", "person"),
            bbox=detection.get("bbox", [0, 0, 10, 10]),
            keypoints=detection.get("keypoints"),
            conf=detection.get("conf", 0.5),
            track_history=track_info,
            spatial_context=spatial_context
        )
        return {
            "class": detection.get("class", "person").upper(),
            "observation_validity": decision.validity,
            "safety_eligible": decision.safety_eligible,
            "evidence": decision.evidence,
            "reason": decision.reason
        }

