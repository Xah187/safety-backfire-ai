"""
V3.1 Safety Ontology — Evidence & Provenance Contracts

Enforces:
1. Strict separation of Direct Observation vs Inferred State.
2. Complete provenance tracing on every hazard, relation, and decision.
3. Multi-dimensional confidence decomposition (never collapse uncertainty into a single scalar).
4. ODD status tracking (VALID, DEGRADED, OUT_OF_DOMAIN, UNKNOWN).
"""
import time
from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

class EvidenceType(str, Enum):
    DIRECT_OBSERVATION = "DIRECT_OBSERVATION"
    MULTI_FRAME_OBSERVATION = "MULTI_FRAME_OBSERVATION"
    GEOMETRIC_INFERENCE = "GEOMETRIC_INFERENCE"
    KINEMATIC_INFERENCE = "KINEMATIC_INFERENCE"
    RELATIONAL_INFERENCE = "RELATIONAL_INFERENCE"
    COUNTERFACTUAL_INFERENCE = "COUNTERFACTUAL_INFERENCE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"

class ODDStatus(str, Enum):
    VALID = "VALID"
    DEGRADED = "DEGRADED"
    OUT_OF_DOMAIN = "OUT_OF_DOMAIN"
    UNKNOWN = "UNKNOWN"

@dataclass
class ConfidenceDecomposition:
    """
    Decomposes aggregate confidence into distinct sensory and reasoning stages.
    Enforces rule: Never hide uncertainty behind one scalar confidence.
    """
    detection_confidence: float = 0.0
    tracking_confidence: float = 0.0
    identity_confidence: float = 0.0
    geometry_confidence: float = 0.0
    pose_confidence: float = 0.0
    relation_confidence: float = 0.0
    kinematic_confidence: float = 0.0
    hazard_confidence: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        return {
            "detection": round(self.detection_confidence, 3),
            "tracking": round(self.tracking_confidence, 3),
            "identity": round(self.identity_confidence, 3),
            "geometry": round(self.geometry_confidence, 3),
            "pose": round(self.pose_confidence, 3),
            "relation": round(self.relation_confidence, 3),
            "kinematic": round(self.kinematic_confidence, 3),
            "hazard": round(self.hazard_confidence, 3)
        }

    @property
    def minimum_gate_confidence(self) -> float:
        """Returns the weakest link in the perceptual-reasoning pipeline."""
        non_zero = [c for c in [
            self.detection_confidence, self.tracking_confidence,
            self.geometry_confidence, self.hazard_confidence
        ] if c > 0.0]
        return min(non_zero) if non_zero else 0.0

@dataclass
class ProvenanceRecord:
    """
    Immutable structured provenance record required for all safety-critical claims.
    """
    source_frame_id: int
    source_timestamp: float
    capture_timestamp: float
    entity_ids: List[str]
    policy_version: str = "V3.1_CORE"
    decision_reason: str = "nominal"
    evidence_type: EvidenceType = EvidenceType.DIRECT_OBSERVATION
    odd_status: ODDStatus = ODDStatus.VALID
    confidence: ConfidenceDecomposition = field(default_factory=ConfidenceDecomposition)
    sensor_id: str = "CAM_MAIN_OVERHEAD"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_frame_id": self.source_frame_id,
            "source_timestamp": round(self.source_timestamp, 4),
            "capture_timestamp": round(self.capture_timestamp, 4),
            "entity_ids": self.entity_ids,
            "policy_version": self.policy_version,
            "decision_reason": self.decision_reason,
            "evidence_type": self.evidence_type.value,
            "odd_status": self.odd_status.value,
            "confidence": self.confidence.to_dict(),
            "sensor_id": self.sensor_id,
            "metadata": self.metadata
        }
