"""
V3.1 Safety Ontology — Multi-Dimensional Entity States

Enforces:
1. Every state dimension explicitly includes UNKNOWN rather than defaulting to safe.
2. Structural integrity is never inferred from appearance alone (defaults to UNKNOWN if unevidenced).
3. PPE visibility distinguishes NOT_VISIBLE from definitely absent.
"""
from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

class PostureState(str, Enum):
    STANDING = "STANDING"
    WALKING = "WALKING"
    RUNNING = "RUNNING"
    FALLEN = "FALLEN"
    CROUCHED = "CROUCHED"
    CLIMBING = "CLIMBING"
    REACHING = "REACHING"
    LIFTING = "LIFTING"
    WORKING_AT_HEIGHT = "WORKING_AT_HEIGHT"
    UNKNOWN = "UNKNOWN"

class MotionState(str, Enum):
    STOPPED = "STOPPED"
    MOVING = "MOVING"
    ACCELERATING = "ACCELERATING"
    DECELERATING = "DECELERATING"
    REVERSING = "REVERSING"
    TURNING = "TURNING"
    UNKNOWN = "UNKNOWN"

class StructuralState(str, Enum):
    STABLE = "STABLE"
    TILTED = "TILTED"
    LEANING = "LEANING"
    DAMAGED = "DAMAGED"
    DISPLACED = "DISPLACED"
    OVERHANGING = "OVERHANGING"
    PARTIALLY_FALLEN = "PARTIALLY_FALLEN"
    FALLEN = "FALLEN"
    UNSTABLE = "UNSTABLE"
    IMPACTED = "IMPACTED"
    UNKNOWN = "UNKNOWN"

class OperationalState(str, Enum):
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
    JAMMED = "JAMMED"
    GUARDED = "GUARDED"
    UNGUARDED = "UNGUARDED"
    OBSTRUCTED = "OBSTRUCTED"
    UNDER_MAINTENANCE = "UNDER_MAINTENANCE"
    UNKNOWN = "UNKNOWN"

class ZoneOccupancyState(str, Enum):
    CLEAR = "CLEAR"
    OCCUPIED = "OCCUPIED"
    BLOCKED = "BLOCKED"
    PARTIALLY_BLOCKED = "PARTIALLY_BLOCKED"
    RESTRICTED = "RESTRICTED"
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    UNKNOWN = "UNKNOWN"

class PPEObservationStatus(str, Enum):
    VISIBLE = "VISIBLE"
    NOT_VISIBLE = "NOT_VISIBLE"
    OCCLUDED = "OCCLUDED"
    UNKNOWN = "UNKNOWN"

@dataclass
class PPEProfile:
    hard_hat: PPEObservationStatus = PPEObservationStatus.UNKNOWN
    hi_vis_vest: PPEObservationStatus = PPEObservationStatus.UNKNOWN
    gloves: PPEObservationStatus = PPEObservationStatus.UNKNOWN
    eye_protection: PPEObservationStatus = PPEObservationStatus.UNKNOWN
    hearing_protection: PPEObservationStatus = PPEObservationStatus.UNKNOWN
    safety_shoes: PPEObservationStatus = PPEObservationStatus.UNKNOWN

    def to_dict(self) -> Dict[str, str]:
        return {
            "hard_hat": self.hard_hat.value,
            "hi_vis_vest": self.hi_vis_vest.value,
            "gloves": self.gloves.value,
            "eye_protection": self.eye_protection.value,
            "hearing_protection": self.hearing_protection.value,
            "safety_shoes": self.safety_shoes.value
        }
