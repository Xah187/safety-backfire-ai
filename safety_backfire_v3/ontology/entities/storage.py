"""
V3.1 Safety Ontology — Storage Structures & Material Loads
"""
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field

from safety_backfire_v3.ontology.entities.base import EntityBase, EntityCategory
from safety_backfire_v3.ontology.states.states import StructuralState

class StorageType(str, Enum):
    RACK = "RACK"
    RACK_UPRIGHT = "RACK_UPRIGHT"
    BEAM = "BEAM"
    RACK_GUARD = "RACK_GUARD"
    SHELF = "SHELF"
    UNKNOWN_STORAGE = "UNKNOWN_STORAGE"

class LoadType(str, Enum):
    PALLET = "PALLET"
    PACKAGE = "PACKAGE"
    CONTAINER = "CONTAINER"
    STACKED_MATERIAL = "STACKED_MATERIAL"
    LOOSE_MATERIAL = "LOOSE_MATERIAL"
    UNKNOWN_LOAD = "UNKNOWN_LOAD"

@dataclass
class StorageStructureEntity(EntityBase):
    """
    Represents stationary warehouse racking, upright frames, crossbeams, or crash guards.
    """
    category: EntityCategory = EntityCategory.STORAGE_STRUCTURE
    storage_type: StorageType = StorageType.RACK
    structural_state: StructuralState = StructuralState.UNKNOWN
    aisle_id: Optional[str] = None
    bays_count: int = 1
    levels_count: int = 4
    has_impact_guard: bool = True
    load_capacity_kg: Optional[float] = None

    def __post_init__(self):
        self.subtype = self.storage_type.value

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({
            "storage_type": self.storage_type.value,
            "structural_state": self.structural_state.value,
            "aisle_id": self.aisle_id,
            "has_impact_guard": self.has_impact_guard
        })
        return d

@dataclass
class LoadEntity(EntityBase):
    """
    Represents material loads, pallets, stacked boxes, or carried containers.
    """
    category: EntityCategory = EntityCategory.LOAD
    load_type: LoadType = LoadType.PALLET
    structural_state: StructuralState = StructuralState.UNKNOWN
    carrier_vehicle_id: Optional[str] = None
    supporting_rack_id: Optional[str] = None
    stack_height_m: float = 1.4
    tilt_angle_deg: float = 0.0
    overhang_distance_m: float = 0.0 # Protrusion beyond pallet or rack beam

    def __post_init__(self):
        self.subtype = self.load_type.value

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({
            "load_type": self.load_type.value,
            "structural_state": self.structural_state.value,
            "carrier_vehicle_id": self.carrier_vehicle_id,
            "supporting_rack_id": self.supporting_rack_id,
            "tilt_angle_deg": round(self.tilt_angle_deg, 1),
            "overhang_distance_m": round(self.overhang_distance_m, 2)
        })
        return d
