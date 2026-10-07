"""
V3.1 Safety Ontology — Relation Taxonomy
"""
from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

class SpatialRelationType(str, Enum):
    NEAR = "NEAR"
    FAR = "FAR"
    TOUCHING = "TOUCHING"
    ABOVE = "ABOVE"
    BELOW = "BELOW"
    ADJACENT_TO = "ADJACENT_TO"
    OVERLAPPING_2D = "OVERLAPPING_2D"

class KinematicRelationType(str, Enum):
    APPROACHING = "APPROACHING"
    MOVING_TOWARD = "MOVING_TOWARD"
    RECEDING = "RECEDING"
    CROSSING = "CROSSING"
    PARALLEL = "PARALLEL"
    INTERSECTING_TRAJECTORY = "INTERSECTING_TRAJECTORY"
    STATIONARY_PAIR = "STATIONARY_PAIR"
    UNKNOWN_KINEMATICS = "UNKNOWN_KINEMATICS"

class TopologicalRelationType(str, Enum):
    INSIDE_ZONE = "INSIDE_ZONE"
    ENTERING_ZONE = "ENTERING_ZONE"
    EXITING_ZONE = "EXITING_ZONE"
    STRADDLING_BOUNDARY = "STRADDLING_BOUNDARY"
    OUTSIDE_ZONE = "OUTSIDE_ZONE"

class StructuralRelationType(str, Enum):
    SUPPORTING = "SUPPORTING"
    LOADED_ON = "LOADED_ON"
    CARRYING = "CARRYING"
    BLOCKING = "BLOCKING"
    IMPACTING = "IMPACTING"
    DETACHED = "DETACHED"
    UNKNOWN_STRUCTURAL = "UNKNOWN_STRUCTURAL"

@dataclass
class RelationRecord:
    """
    Structured instance of a detected relation between subject and object entities.
    """
    subject_entity_id: str
    object_entity_id: str
    spatial_relation: SpatialRelationType = SpatialRelationType.FAR
    kinematic_relation: KinematicRelationType = KinematicRelationType.UNKNOWN_KINEMATICS
    topological_relation: Optional[TopologicalRelationType] = None
    structural_relation: Optional[StructuralRelationType] = None
    distance_m: Optional[float] = None
    distance_uncertainty_m: Optional[float] = None
    approach_speed_m_s: Optional[float] = None
    ttc_sec: Optional[float] = None
    confidence: float = 0.8
    start_timestamp: float = 0.0
    end_timestamp: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subject_id": self.subject_entity_id,
            "object_id": self.object_entity_id,
            "spatial": self.spatial_relation.value,
            "kinematic": self.kinematic_relation.value,
            "topological": self.topological_relation.value if self.topological_relation else None,
            "structural": self.structural_relation.value if self.structural_relation else None,
            "distance_m": round(self.distance_m, 3) if self.distance_m is not None else None,
            "uncertainty_m": round(self.distance_uncertainty_m, 3) if self.distance_uncertainty_m is not None else None,
            "approach_speed_m_s": round(self.approach_speed_m_s, 2) if self.approach_speed_m_s is not None else None,
            "ttc_sec": round(self.ttc_sec, 2) if self.ttc_sec is not None else None,
            "confidence": round(self.confidence, 3)
        }
