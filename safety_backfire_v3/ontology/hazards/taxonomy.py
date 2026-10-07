"""
V3.1 Safety Ontology — 20-Hazard Controlled Vocabulary
"""
from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from safety_backfire_v3.ontology.interactions.types import InteractionSeverity, InteractionImminence
from safety_backfire_v3.ontology.evidence.contracts import ProvenanceRecord

class HazardType(str, Enum):
    COLLISION_HAZARD = "COLLISION_HAZARD"
    FALL_HAZARD = "FALL_HAZARD"
    FALLING_OBJECT_HAZARD = "FALLING_OBJECT_HAZARD"
    COLLAPSE_HAZARD = "COLLAPSE_HAZARD"
    ENTRAPMENT_HAZARD = "ENTRAPMENT_HAZARD"
    STRUCK_BY_HAZARD = "STRUCK_BY_HAZARD"
    CRUSH_HAZARD = "CRUSH_HAZARD"
    BLOCKED_AISLE_HAZARD = "BLOCKED_AISLE_HAZARD"
    BLOCKED_EGRESS_HAZARD = "BLOCKED_EGRESS_HAZARD"
    FIRE_ACCESS_HAZARD = "FIRE_ACCESS_HAZARD"
    UNSAFE_LOAD_HAZARD = "UNSAFE_LOAD_HAZARD"
    MACHINERY_EXPOSURE_HAZARD = "MACHINERY_EXPOSURE_HAZARD"
    PEDESTRIAN_ZONE_INTRUSION = "PEDESTRIAN_ZONE_INTRUSION"
    VEHICLE_ZONE_INTRUSION = "VEHICLE_ZONE_INTRUSION"
    SPILL_SLIP_HAZARD = "SPILL_SLIP_HAZARD"
    OBSTRUCTION_HAZARD = "OBSTRUCTION_HAZARD"
    PPE_NONCOMPLIANCE_HAZARD = "PPE_NONCOMPLIANCE_HAZARD"
    DOCK_EDGE_HAZARD = "DOCK_EDGE_HAZARD"
    PROCESS_DEVIATION_HAZARD = "PROCESS_DEVIATION_HAZARD"
    UNKNOWN_HAZARD = "UNKNOWN_HAZARD"

class HazardLifecycleState(str, Enum):
    CANDIDATE = "CANDIDATE"
    ACTIVE = "ACTIVE"
    CONFIRMED = "CONFIRMED"
    MITIGATED = "MITIGATED"
    DISMISSED = "DISMISSED"

@dataclass
class HazardRecord:
    hazard_id: str
    hazard_type: HazardType
    entity_ids: List[str]
    zone_id: str = "GLOBAL"
    severity: InteractionSeverity = InteractionSeverity.MODERATE
    imminence: InteractionImminence = InteractionImminence.MEDIUM
    confidence: float = 0.85
    evidence_quality: float = 0.85
    state: HazardLifecycleState = HazardLifecycleState.CANDIDATE
    provenance: Optional[ProvenanceRecord] = None
    description: str = "hazard_detected"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hazard_id": self.hazard_id,
            "hazard_type": self.hazard_type.value,
            "entities": self.entity_ids,
            "zone": self.zone_id,
            "severity": self.severity.value,
            "imminence": self.imminence.value,
            "confidence": round(self.confidence, 3),
            "evidence_quality": round(self.evidence_quality, 3),
            "state": self.state.value,
            "description": self.description,
            "provenance": self.provenance.to_dict() if self.provenance else None,
            "metadata": self.metadata
        }
