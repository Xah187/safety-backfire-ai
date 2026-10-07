"""
V3.1 Safety Ontology — Interaction Taxonomy
"""
from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

from safety_backfire_v3.ontology.relations.types import RelationRecord
from safety_backfire_v3.ontology.evidence.contracts import ProvenanceRecord

class InteractionType(str, Enum):
    COLLISION_RISK = "COLLISION_RISK"
    IMPACT = "IMPACT"
    NEAR_COLLISION = "NEAR_COLLISION"
    BLOCKING = "BLOCKING"
    ENCROACHMENT = "ENCROACHMENT"
    FALL_EXPOSURE = "FALL_EXPOSURE"
    COLLAPSE_EXPOSURE = "COLLAPSE_EXPOSURE"
    ENTRAPMENT_EXPOSURE = "ENTRAPMENT_EXPOSURE"
    RESTRICTED_ZONE_INTRUSION = "RESTRICTED_ZONE_INTRUSION"
    UNSAFE_LOADING = "UNSAFE_LOADING"
    UNSAFE_UNLOADING = "UNSAFE_UNLOADING"
    BENIGN_INTERACTION = "BENIGN_INTERACTION"
    UNKNOWN_INTERACTION = "UNKNOWN_INTERACTION"

class InteractionSeverity(str, Enum):
    CATASTROPHIC = "CATASTROPHIC" # Fatal / amputation / major collapse
    CRITICAL = "CRITICAL"         # Severe injury / vehicle impact
    MODERATE = "MODERATE"         # Minor injury / near miss / load shift
    MINOR = "MINOR"               # Operational delay / warning zone
    NEGLIGIBLE = "NEGLIGIBLE"

class InteractionImminence(str, Enum):
    IMMINENT = "IMMINENT"   # TTC < 1.5s or distance <= 1.0m
    HIGH = "HIGH"           # TTC < 2.5s or distance <= 1.8m
    MEDIUM = "MEDIUM"       # Distance <= 3.0m
    LOW = "LOW"             # Distance > 3.0m but converging
    NONE = "NONE"

@dataclass
class InteractionRecord:
    interaction_id: str
    interaction_type: InteractionType
    entity_a_id: str
    entity_b_id: str
    relation: RelationRecord
    severity: InteractionSeverity = InteractionSeverity.MODERATE
    imminence: InteractionImminence = InteractionImminence.MEDIUM
    evidence_quality: float = 0.80
    provenance: Optional[ProvenanceRecord] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "interaction_id": self.interaction_id,
            "type": self.interaction_type.value,
            "entity_a_id": self.entity_a_id,
            "entity_b_id": self.entity_b_id,
            "severity": self.severity.value,
            "imminence": self.imminence.value,
            "evidence_quality": round(self.evidence_quality, 3),
            "relation": self.relation.to_dict(),
            "provenance": self.provenance.to_dict() if self.provenance else None
        }
