"""
V3.1 Safety Ontology — Human Entity Taxonomy
"""
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field

from safety_backfire_v3.ontology.entities.base import EntityBase, EntityCategory
from safety_backfire_v3.ontology.states.states import PostureState, PPEProfile

class PersonSubtype(str, Enum):
    PEDESTRIAN = "PEDESTRIAN"
    OPERATOR = "OPERATOR"
    MAINTENANCE_WORKER = "MAINTENANCE_WORKER"
    SUPERVISOR = "SUPERVISOR"
    VISITOR = "VISITOR"
    UNKNOWN_PERSON = "UNKNOWN_PERSON"

@dataclass
class PersonEntity(EntityBase):
    """
    Represents a human worker, operator, visitor, or unclassified person in the warehouse.
    """
    category: EntityCategory = EntityCategory.PERSON
    person_subtype: PersonSubtype = PersonSubtype.UNKNOWN_PERSON
    posture: PostureState = PostureState.UNKNOWN
    ppe: PPEProfile = field(default_factory=PPEProfile)
    keypoints_coco: Optional[List[List[float]]] = None # 17 COCO keypoints [x, y, conf]
    associated_vehicle_id: Optional[str] = None # When coupled as operator
    is_operator_suppressed: bool = False
    torso_angle_deg: Optional[float] = None
    man_down_candidate: bool = False

    def __post_init__(self):
        self.subtype = self.person_subtype.value

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({
            "person_subtype": self.person_subtype.value,
            "posture": self.posture.value,
            "ppe": self.ppe.to_dict(),
            "associated_vehicle_id": self.associated_vehicle_id,
            "is_operator_suppressed": self.is_operator_suppressed,
            "torso_angle_deg": round(self.torso_angle_deg, 1) if self.torso_angle_deg is not None else None,
            "man_down_candidate": self.man_down_candidate
        })
        return d
