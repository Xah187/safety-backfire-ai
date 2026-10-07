"""
ground_truth.py
Safety Backfire AI - V3.2 Independent Human Ground Truth Schema and Loader
Enforces non-self-referential ground truth with multi-annotator confidence and visibility tracking.
"""

import sys
from pathlib import Path
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
import json

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

class VisibilityState(str, Enum):
    VISIBLE = "VISIBLE"
    OCCLUDED = "OCCLUDED"
    AMBIGUOUS = "AMBIGUOUS"
    NOT_VISIBLE = "NOT_VISIBLE"
    UNKNOWN = "UNKNOWN"

class AnnotationConfidence(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

@dataclass
class GroundTruthAnnotationV1:
    """
    Independent human-verified annotation for an entity in a single frame.
    """
    annotation_id: str
    video_id: str
    frame_index: int
    timestamp_sec: float
    entity_id: str
    entity_class: str # person, forklift, rack, pallet, load, conveyor, machine, dock, exit, barrier, etc.
    bbox_2d: Optional[List[float]] = None # [x1, y1, x2, y2]
    world_pos_ground_m: Optional[Tuple[float, float]] = None # (X_w, Y_w) physically surveyed/verified
    visibility: VisibilityState = VisibilityState.VISIBLE
    occlusion_percent: float = 0.0
    state: str = "stationary" # moving, stationary, reversing, fallen, leaning, unstable, blocked, damaged, occupied, etc.
    velocity_m_s: Optional[Tuple[float, float]] = None
    annotator_id: str = "HUMAN_EXPERT_01"
    annotation_confidence: AnnotationConfidence = AnnotationConfidence.HIGH
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "annotation_id": self.annotation_id,
            "video_id": self.video_id,
            "frame_index": self.frame_index,
            "timestamp_sec": round(self.timestamp_sec, 3),
            "entity_id": self.entity_id,
            "entity_class": self.entity_class,
            "bbox_2d": self.bbox_2d,
            "world_pos_ground_m": list(self.world_pos_ground_m) if self.world_pos_ground_m is not None else None,
            "visibility": self.visibility.value,
            "occlusion_percent": round(self.occlusion_percent, 2),
            "state": self.state,
            "velocity_m_s": list(self.velocity_m_s) if self.velocity_m_s is not None else None,
            "annotator_id": self.annotator_id,
            "annotation_confidence": self.annotation_confidence.value,
            "notes": self.notes
        }

@dataclass
class GroundTruthRelationEventV1:
    """
    Independent human-verified annotation for a pairwise relation, interaction, hazard, and safety event.
    """
    event_id: str
    video_id: str
    subject_id: str
    object_id: str
    start_frame: int
    end_frame: int
    start_time_sec: float
    end_time_sec: float
    relation_type: str # near, approaching, crossing, inside_zone, blocking, supporting, touching, impacting
    hazard_type: str # COLLISION_HAZARD, COLLAPSE_HAZARD, BLOCKED_EGRESS_HAZARD, etc.
    true_min_distance_m: float
    true_ttc_at_onset_sec: Optional[float] = None
    true_severity: str = "CRITICAL"
    annotator_ids: List[str] = field(default_factory=lambda: ["HUMAN_01", "HUMAN_02"])
    agreement_status: str = "FULL_CONSENSUS" # FULL_CONSENSUS, MINOR_DIVERGENCE, AMBIGUOUS_CASE
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "video_id": self.video_id,
            "subject_id": self.subject_id,
            "object_id": self.object_id,
            "frame_span": [self.start_frame, self.end_frame],
            "time_span_sec": [round(self.start_time_sec, 3), round(self.end_time_sec, 3)],
            "relation_type": self.relation_type,
            "hazard_type": self.hazard_type,
            "true_min_distance_m": round(self.true_min_distance_m, 2),
            "true_ttc_at_onset_sec": round(self.true_ttc_at_onset_sec, 2) if self.true_ttc_at_onset_sec is not None else "UNDEFINED",
            "true_severity": self.true_severity,
            "annotator_ids": self.annotator_ids,
            "agreement_status": self.agreement_status,
            "notes": self.notes
        }

def export_annotation_schema(output_path: Path):
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "GroundTruthAnnotationV1Schema",
        "description": "Independent multi-annotator ground truth schema for entities, states, relations, and hazards",
        "type": "object",
        "required": ["annotation_id", "video_id", "frame_index", "entity_id", "entity_class", "visibility", "state"],
        "properties": {
            "annotation_id": {"type": "string"},
            "video_id": {"type": "string"},
            "frame_index": {"type": "integer"},
            "timestamp_sec": {"type": "number"},
            "entity_id": {"type": "string"},
            "entity_class": {
                "type": "string",
                "enum": ["person", "forklift", "vehicle", "rack", "rack_upright", "beam", "pallet", "load", "conveyor", "machine", "dock", "exit", "barrier", "zone", "other_supported_entity"]
            },
            "visibility": {
                "type": "string",
                "enum": ["VISIBLE", "OCCLUDED", "AMBIGUOUS", "NOT_VISIBLE", "UNKNOWN"]
            },
            "annotation_confidence": {
                "type": "string",
                "enum": ["HIGH", "MEDIUM", "LOW"]
            }
        }
    }
    with open(output_path, "w") as f:
        json.dump(schema, f, indent=2)

if __name__ == "__main__":
    out_dir = WORKSPACE_ROOT / "safety_backfire_v3/outputs/v3_2"
    out_dir.mkdir(parents=True, exist_ok=True)
    export_annotation_schema(out_dir / "annotation_schema.json")
    print("Exported annotation_schema.json successfully.")
