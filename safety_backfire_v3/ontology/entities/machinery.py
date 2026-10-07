"""
V3.1 Safety Ontology — Industrial Machinery & Fixed Equipment
"""
from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from safety_backfire_v3.ontology.entities.base import EntityBase, EntityCategory
from safety_backfire_v3.ontology.states.states import OperationalState

class MachineType(str, Enum):
    CONVEYOR = "CONVEYOR"
    PRODUCTION_MACHINE = "PRODUCTION_MACHINE"
    COMPACTOR = "COMPACTOR"
    AUTOMATED_SYSTEM = "AUTOMATED_SYSTEM"
    CHARGING_STATION = "CHARGING_STATION"
    MAINTENANCE_EQUIPMENT = "MAINTENANCE_EQUIPMENT"
    UNKNOWN_MACHINE = "UNKNOWN_MACHINE"

@dataclass
class MachineEntity(EntityBase):
    """
    Represents fixed warehouse machines, conveyors, packaging stations, and compactors.
    """
    category: EntityCategory = EntityCategory.MACHINE
    machine_type: MachineType = MachineType.CONVEYOR
    operational_state: OperationalState = OperationalState.UNKNOWN
    has_physical_guard: bool = True
    has_e_stop_accessible: bool = True
    speed_m_s: float = 0.0 # Conveyor belt or actuator speed
    danger_zone_radius_m: float = 1.0

    def __post_init__(self):
        self.subtype = self.machine_type.value

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({
            "machine_type": self.machine_type.value,
            "operational_state": self.operational_state.value,
            "has_physical_guard": self.has_physical_guard,
            "danger_zone_radius_m": self.danger_zone_radius_m
        })
        return d
