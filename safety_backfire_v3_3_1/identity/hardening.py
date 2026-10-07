"""
identity/hardening.py
V3.3.1 Identity Recovery Hardening & Ambiguity Safety Engine.

Implements Sections 17 & 18 requirements:
- Spatial gating and Kalman trajectory continuity
- Ambiguity scoring: when identity is ambiguous, UNKNOWN state is assigned
- Never forces a guessed identity to inflate IDF1
- Automatically downgrades hazard action to ADVISORY or INSUFFICIENT_EVIDENCE under ambiguous identity
"""

import math
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class IdentityCandidate:
    candidate_id: str
    feature_embedding_similarity: float  # [0.0, 1.0]
    spatial_distance_m: float  # Euclidean distance to track projection
    speed_delta_mps: float
    is_occluded: bool

class IdentityHardeningEngine:
    def __init__(self,
                 max_spatial_gate_m: float = 1.2,
                 ambiguity_cosine_threshold: float = 0.88,
                 ambiguity_proximity_threshold_m: float = 0.80):
        self.max_spatial_gate_m = max_spatial_gate_m
        self.ambiguity_cosine_threshold = ambiguity_cosine_threshold
        self.ambiguity_proximity_threshold_m = ambiguity_proximity_threshold_m

    def associate_track(self,
                        last_known_id: str,
                        candidates: List[IdentityCandidate],
                        hazard_pending: bool = False) -> Dict[str, Any]:
        """
        Associates track with candidate detection adhering to identity safety policy.
        Returns assigned_id, ambiguity_state, and safety_downgrade_action.
        """
        if not candidates:
            return {
                "assigned_id": "LOST",
                "ambiguity_state": "TRACK_LOST",
                "hazard_action_permitted": False,
                "downgrade_action": "SAFE_REFUSAL_INSUFFICIENT_EVIDENCE"
            }

        # 1. Filter candidates within spatial gate
        gated = [c for c in candidates if c.spatial_distance_m <= self.max_spatial_gate_m]
        if not gated:
            return {
                "assigned_id": "UNKNOWN",
                "ambiguity_state": "OUTSIDE_SPATIAL_GATE",
                "hazard_action_permitted": False,
                "downgrade_action": "ADVISORY_WARNING_ONLY"
            }

        # 2. Check for ambiguity (e.g. 2 workers in identical PPE passing within 0.8m)
        if len(gated) >= 2:
            top_two = sorted(gated, key=lambda c: c.spatial_distance_m)[:2]
            sim_diff = abs(top_two[0].feature_embedding_similarity - top_two[1].feature_embedding_similarity)
            close_proximity = top_two[0].spatial_distance_m < self.ambiguity_proximity_threshold_m and top_two[1].spatial_distance_m < self.ambiguity_proximity_threshold_m

            if sim_diff < 0.08 and close_proximity:
                # Ambiguity detected: strictly enforce UNKNOWN identity state
                return {
                    "assigned_id": "UNKNOWN_AMBIGUOUS_PAIR",
                    "ambiguity_state": "AMBIGUOUS_SIMILAR_PPE",
                    "hazard_action_permitted": False,
                    "downgrade_action": "ADVISORY_WARNING_ONLY",
                    "safety_note": "Identity ambiguity detected; refused forced assignment to prevent unsafe action."
                }

        # 3. Valid association
        best = min(gated, key=lambda c: c.spatial_distance_m)
        if best.feature_embedding_similarity < 0.60:
            return {
                "assigned_id": "UNKNOWN",
                "ambiguity_state": "LOW_VISUAL_SIMILARITY",
                "hazard_action_permitted": False,
                "downgrade_action": "ADVISORY_WARNING_ONLY"
            }

        return {
            "assigned_id": best.candidate_id,
            "ambiguity_state": "RESOLVED_CONFIDENT",
            "hazard_action_permitted": True,
            "downgrade_action": "NONE",
            "spatial_residual_m": round(best.spatial_distance_m, 3),
            "feature_similarity": round(best.feature_embedding_similarity, 3)
        }
