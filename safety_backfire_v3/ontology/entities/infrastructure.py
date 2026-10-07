"""
V3.1 Safety Ontology — Infrastructure & Workplace Zones
"""
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field

from safety_backfire_v3.ontology.entities.base import EntityBase, EntityCategory
from safety_backfire_v3.ontology.states.states import ZoneOccupancyState

class InfraType(str, Enum):
    AISLE = "AISLE"
    PEDESTRIAN_LANE = "PEDESTRIAN_LANE"
    VEHICLE_LANE = "VEHICLE_LANE"
    LOADING_DOCK = "LOADING_DOCK"
    DOCK_DOOR = "DOCK_DOOR"
    EMERGENCY_EXIT = "EMERGENCY_EXIT"
    EMERGENCY_ROUTE = "EMERGENCY_ROUTE"
    FIRE_EQUIPMENT_ZONE = "FIRE_EQUIPMENT_ZONE"
    RESTRICTED_ZONE = "RESTRICTED_ZONE"
    WORKSTATION = "WORKSTATION"
    FLOOR_AREA = "FLOOR_AREA"
    DOORWAY = "DOORWAY"
    BARRIER = "BARRIER"
    GUARDRAIL = "GUARDRAIL"
    UNKNOWN_INFRASTRUCTURE = "UNKNOWN_INFRASTRUCTURE"

@dataclass
class InfrastructureEntity(EntityBase):
    """
    Represents physical layout features, walkways, loading bays, emergency paths, and barriers.
    """
    category: EntityCategory = EntityCategory.INFRASTRUCTURE
    infra_type: InfraType = InfraType.AISLE
    occupancy_state: ZoneOccupancyState = ZoneOccupancyState.CLEAR
    polygon_vertices_m: List[Tuple[float, float]] = field(default_factory=list) # 2D Ground footprint
    speed_limit_m_s: Optional[float] = None
    is_egress_path: bool = False
    is_pedestrian_only: bool = False
    is_vehicle_only: bool = False
    is_restricted_access: bool = False
    width_clearance_m: float = 3.0
    min_required_clearance_m: float = 1.2 # OSHA/ISO minimum egress width

    def __post_init__(self):
        self.subtype = self.infra_type.value

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({
            "infra_type": self.infra_type.value,
            "occupancy_state": self.occupancy_state.value,
            "polygon_vertices_m": [list(v) for v in self.polygon_vertices_m],
            "is_egress_path": self.is_egress_path,
            "is_pedestrian_only": self.is_pedestrian_only,
            "is_restricted_access": self.is_restricted_access,
            "width_clearance_m": round(self.width_clearance_m, 2)
        })
        return d
