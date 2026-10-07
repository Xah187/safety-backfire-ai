"""
V3.1 Safety Ontology — Base Entity Model & Hierarchy

Enforces:
1. Strict typing and inheritance for all warehouse entities.
2. Complete provenance tracing and 3D world positioning with uncertainty.
3. Explicit UNKNOWN_ENTITY fallback (never drop or invent classifications).
"""
import time
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
import numpy as np

from safety_backfire_v3.ontology.evidence.contracts import ProvenanceRecord, ODDStatus

class EntityCategory(str, Enum):
    PERSON = "PERSON"
    VEHICLE = "VEHICLE"
    STORAGE_STRUCTURE = "STORAGE_STRUCTURE"
    LOAD = "LOAD"
    MACHINE = "MACHINE"
    INFRASTRUCTURE = "INFRASTRUCTURE"
    ENVIRONMENTAL_HAZARD = "ENVIRONMENTAL_HAZARD"
    UNKNOWN = "UNKNOWN"

@dataclass
class EntityBase:
    """
    Abstract base entity contract across all warehouse perception and reasoning.
    """
    entity_id: str
    category: EntityCategory
    subtype: str = "UNKNOWN"
    track_id: Optional[int] = None
    bbox_2d: Optional[List[float]] = None # [x1, y1, x2, y2]
    world_pos_m: Optional[Tuple[float, float]] = None # (X, Y) on warehouse ground plane
    elevation_z_m: float = 0.0 # Height above ground plane
    velocity_m_s: Optional[Tuple[float, float]] = None # (vx, vy)
    speed_m_s: float = 0.0
    position_uncertainty_m: float = 0.20
    covariance_2d: Optional[np.ndarray] = None
    first_observed_ts: float = field(default_factory=time.time)
    last_observed_ts: float = field(default_factory=time.time)
    last_frame_id: int = 0
    odd_status: ODDStatus = ODDStatus.VALID
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "category": self.category.value,
            "subtype": self.subtype,
            "track_id": self.track_id,
            "bbox_2d": self.bbox_2d,
            "world_pos_m": list(self.world_pos_m) if self.world_pos_m is not None else None,
            "elevation_z_m": round(self.elevation_z_m, 3),
            "speed_m_s": round(self.speed_m_s, 2),
            "velocity_m_s": list(self.velocity_m_s) if self.velocity_m_s is not None else None,
            "position_uncertainty_m": round(self.position_uncertainty_m, 3),
            "last_frame_id": self.last_frame_id,
            "last_observed_ts": round(self.last_observed_ts, 4),
            "odd_status": self.odd_status.value,
            "is_active": self.is_active,
            "metadata": self.metadata
        }
