"""
V3.1 Safety Ontology — Mobile Equipment & Vehicle Taxonomy
"""
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field

from safety_backfire_v3.ontology.entities.base import EntityBase, EntityCategory
from safety_backfire_v3.ontology.states.states import MotionState

class VehicleType(str, Enum):
    FORKLIFT = "FORKLIFT"
    REACH_TRUCK = "REACH_TRUCK"
    PALLET_JACK = "PALLET_JACK"
    ORDER_PICKER = "ORDER_PICKER"
    TUGGER = "TUGGER"
    AGV = "AGV"
    AMR = "AMR"
    TRUCK = "TRUCK"
    TRAILER = "TRAILER"
    OTHER_MOBILE_EQUIPMENT = "OTHER_MOBILE_EQUIPMENT"
    UNKNOWN_VEHICLE = "UNKNOWN_VEHICLE"

@dataclass
class VehicleEntity(EntityBase):
    """
    Represents mobile industrial equipment, material handlers, AGVs, or road vehicles.
    """
    category: EntityCategory = EntityCategory.VEHICLE
    vehicle_type: VehicleType = VehicleType.FORKLIFT
    motion_state: MotionState = MotionState.UNKNOWN
    heading_deg: Optional[float] = None
    turning_rate_deg_s: float = 0.0
    is_reversing: bool = False
    fork_height_m: float = 0.0
    has_load: bool = False
    attached_load_id: Optional[str] = None
    active_operator_id: Optional[str] = None
    cabin_roi_2d: Optional[List[float]] = None # Normalized cabin ROI [x1, y1, x2, y2]
    length_m: float = 2.4
    width_m: float = 1.2
    mass_kg: float = 3500.0

    def __post_init__(self):
        self.subtype = self.vehicle_type.value

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({
            "vehicle_type": self.vehicle_type.value,
            "motion_state": self.motion_state.value,
            "heading_deg": round(self.heading_deg, 1) if self.heading_deg is not None else None,
            "is_reversing": self.is_reversing,
            "fork_height_m": round(self.fork_height_m, 2),
            "has_load": self.has_load,
            "attached_load_id": self.attached_load_id,
            "active_operator_id": self.active_operator_id,
            "dimensions_m": {"length": self.length_m, "width": self.width_m}
        })
        return d
