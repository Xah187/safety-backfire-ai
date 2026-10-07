"""
V3.1 Safety Ontology — Intervention Taxonomy & Window Contract

Enforces:
1. Immutable intervention timestamp (T_intervention).
2. Zero baseline contamination (frames with t >= T_intervention can never alter baseline).
"""
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field

class InterventionType(str, Enum):
    PHYSICAL_BARRIER_ADDED = "PHYSICAL_BARRIER_ADDED"
    SPEED_LIMIT_CHANGED = "SPEED_LIMIT_CHANGED"
    PEDESTRIAN_ROUTE_REROUTED = "PEDESTRIAN_ROUTE_REROUTED"
    RACK_GUARD_INSTALLED = "RACK_GUARD_INSTALLED"
    STORAGE_REARRANGED = "STORAGE_REARRANGED"
    PROCESS_CHANGED = "PROCESS_CHANGED"
    RESTRICTED_ZONE_CREATED = "RESTRICTED_ZONE_CREATED"
    SIGNAGE_ALERT_ADDED = "SIGNAGE_ALERT_ADDED"
    UNKNOWN_INTERVENTION = "UNKNOWN_INTERVENTION"

@dataclass(frozen=True)
class InterventionRecord:
    """
    Immutable specification of a physical or policy safety intervention.
    """
    intervention_id: str
    intervention_type: InterventionType
    zone_id: str
    timestamp: float # Exact cutoff wall-clock or video PTS timestamp
    intended_hazards: Tuple[str, ...]
    description: str = "safety_intervention"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intervention_id": self.intervention_id,
            "type": self.intervention_type.value,
            "zone": self.zone_id,
            "timestamp": round(self.timestamp, 4),
            "intended_hazards": list(self.intended_hazards),
            "description": self.description,
            "metadata": self.metadata
        }
