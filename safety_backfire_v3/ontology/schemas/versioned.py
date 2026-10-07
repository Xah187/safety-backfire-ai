"""
V3.1 Safety Ontology — Versioned Canonical Schemas (Schema V1)

Provides explicit, strongly typed, and versioned JSON schemas for:
EntityV1, ObservationV1, RelationV1, InteractionV1, HazardV1, RiskDecisionV1,
InterventionV1, BackfireAssessmentV1, EventV1.
"""
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict

# Versioned Schema Definitions
SCHEMA_VERSION = "V1.0"

@dataclass
class EntityV1:
    schema_version: str = SCHEMA_VERSION
    entity_id: str = ""
    category: str = "UNKNOWN"
    subtype: str = "UNKNOWN"
    world_pos_m: Optional[List[float]] = None
    position_uncertainty_m: float = 0.20
    is_active: bool = True

@dataclass
class ObservationV1:
    schema_version: str = SCHEMA_VERSION
    frame_id: int = 0
    source_timestamp: float = 0.0
    detected_entities: List[str] = field(default_factory=list)
    confidence: float = 0.0
    odd_status: str = "VALID"

@dataclass
class RelationV1:
    schema_version: str = SCHEMA_VERSION
    subject_id: str = ""
    object_id: str = ""
    spatial_relation: str = "FAR"
    kinematic_relation: str = "UNKNOWN_KINEMATICS"
    distance_m: Optional[float] = None
    ttc_sec: Optional[float] = None
    confidence: float = 0.80

@dataclass
class InteractionV1:
    schema_version: str = SCHEMA_VERSION
    interaction_id: str = ""
    interaction_type: str = "BENIGN_INTERACTION"
    entity_a_id: str = ""
    entity_b_id: str = ""
    severity: str = "MODERATE"
    imminence: str = "MEDIUM"
    evidence_quality: float = 0.85

@dataclass
class HazardV1:
    schema_version: str = SCHEMA_VERSION
    hazard_id: str = ""
    hazard_type: str = "UNKNOWN_HAZARD"
    entity_ids: List[str] = field(default_factory=list)
    zone: str = "GLOBAL"
    severity: str = "MODERATE"
    imminence: str = "MEDIUM"
    state: str = "CANDIDATE"

@dataclass
class RiskDecisionV1:
    schema_version: str = SCHEMA_VERSION
    decision_id: str = ""
    hazard_id: str = ""
    event_id: str = ""
    risk_decision: str = "INSUFFICIENT_EVIDENCE"
    risk_score: float = 0.0
    hazard_category: str = "UNKNOWN_HAZARD"
    reason: str = ""

@dataclass
class InterventionV1:
    schema_version: str = SCHEMA_VERSION
    intervention_id: str = ""
    intervention_type: str = "UNKNOWN_INTERVENTION"
    zone: str = "GLOBAL"
    timestamp: float = 0.0
    intended_hazards: List[str] = field(default_factory=list)

@dataclass
class BackfireAssessmentV1:
    schema_version: str = SCHEMA_VERSION
    assessment_id: str = ""
    intervention_id: str = ""
    primary_category: str = "RISK_UNCHANGED"
    backfire_signal: str = "NEUTRAL"
    risk_delta_percent: float = 0.0
    new_hazards_introduced: List[str] = field(default_factory=list)

@dataclass
class EventV1:
    schema_version: str = SCHEMA_VERSION
    event_id: str = ""
    episode_id: str = ""
    pair_id: Optional[str] = None
    entity_ids: List[str] = field(default_factory=list)
    lifecycle_status: str = "ACTIVE"
    safety_state: str = "SAFE"
