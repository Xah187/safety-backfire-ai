"""
metadata.py
Safety Backfire AI - V3.2 Video Metadata and Physical Provenance Contract
Enforces non-inferred physical parameters with explicit UNKNOWN defaults.
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field

class LineageStatus(str, Enum):
    KNOWN_DEVELOPMENT_DATA = "KNOWN_DEVELOPMENT_DATA"
    CALIBRATION_DATA = "CALIBRATION_DATA"
    VALIDATION_DATA = "VALIDATION_DATA"
    BLIND_TEST_DATA = "BLIND_TEST_DATA"
    UNKNOWN_LINEAGE = "UNKNOWN_LINEAGE"

class DatasetSplit(str, Enum):
    DEVELOPMENT = "DEVELOPMENT"
    CALIBRATION = "CALIBRATION"
    VALIDATION = "VALIDATION"
    BLIND_TEST = "BLIND_TEST"

@dataclass
class VideoMetadataV1:
    """
    Physical, optical, and environmental provenance metadata for warehouse video streams.
    Never infer measured physical metadata without explicitly labeling it as estimated.
    """
    video_id: str
    camera_id: str
    location_id: str
    source_type: str = "FIXED_OVERHEAD_SURVEILLANCE"
    capture_session_id: str = "SESSION_001"
    capture_date: str = "UNKNOWN"
    capture_duration_sec: float = 0.0
    resolution: Tuple[int, int] = (640, 360) # (width, height)
    fps: float = 30.0
    
    # Geometric and mount orientation parameters
    camera_height_m: Optional[float] = None
    camera_pitch_deg: Optional[float] = None
    camera_roll_deg: Optional[float] = None
    camera_yaw_deg: Optional[float] = None
    
    # Optical calibration
    lens_information: str = "UNKNOWN"
    intrinsics_matrix: Optional[List[List[float]]] = None # 3x3 K matrix
    distortion_coefficients: Optional[List[float]] = None # [k1, k2, p1, p2, k3]
    calibration_version: str = "UNKNOWN"
    
    # Environmental conditions
    floor_type: str = "CONCRETE_POLISHED"
    floor_slope_deg: float = 0.0
    lighting_condition: str = "INDOOR_HIGH_BAY_FLUORESCENT" # or DAYLIGHT, MIXED, LOW_LIGHT
    traffic_density: str = "MODERATE" # LOW, MODERATE, HIGH, CONGESTED
    
    # Operational interventions and constraints
    known_interventions: List[str] = field(default_factory=list)
    known_constraints: List[str] = field(default_factory=list)
    
    # Data partition governance
    dataset_split: DatasetSplit = DatasetSplit.VALIDATION
    lineage_status: LineageStatus = LineageStatus.UNKNOWN_LINEAGE
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "video_id": self.video_id,
            "camera_id": self.camera_id,
            "location_id": self.location_id,
            "source_type": self.source_type,
            "capture_session_id": self.capture_session_id,
            "capture_date": self.capture_date,
            "capture_duration_sec": round(self.capture_duration_sec, 2),
            "resolution": list(self.resolution),
            "fps": round(self.fps, 2),
            "camera_height_m": self.camera_height_m if self.camera_height_m is not None else "UNKNOWN",
            "camera_pitch_deg": self.camera_pitch_deg if self.camera_pitch_deg is not None else "UNKNOWN",
            "camera_roll_deg": self.camera_roll_deg if self.camera_roll_deg is not None else "UNKNOWN",
            "camera_yaw_deg": self.camera_yaw_deg if self.camera_yaw_deg is not None else "UNKNOWN",
            "lens_information": self.lens_information,
            "intrinsics_matrix": self.intrinsics_matrix if self.intrinsics_matrix is not None else "UNKNOWN",
            "distortion_coefficients": self.distortion_coefficients if self.distortion_coefficients is not None else "UNKNOWN",
            "calibration_version": self.calibration_version,
            "floor_type": self.floor_type,
            "floor_slope_deg": self.floor_slope_deg,
            "lighting_condition": self.lighting_condition,
            "traffic_density": self.traffic_density,
            "known_interventions": self.known_interventions,
            "known_constraints": self.known_constraints,
            "dataset_split": self.dataset_split.value,
            "lineage_status": self.lineage_status.value,
            "notes": self.notes
        }
