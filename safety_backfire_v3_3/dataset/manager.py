"""
dataset/manager.py
V3.3 Dataset Strategy & Split Management Framework.
Enforces immutable metadata schemas, split boundaries, and blind set quarantine.
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

VALID_SPLITS = {
    "V3.3_DEV",
    "V3.3_CALIBRATION",
    "V3.3_VALIDATION",
    "V3.3_BLIND",
    "V3.3_EXTERNAL_STRESS"
}

VALID_SOURCE_TYPES = {"REAL", "SYNTHETIC", "REPLAY"}

VALID_ODD_TIERS = {
    "NOMINAL_ODD",
    "DEGRADED_ODD",
    "MIXED_ODD",
    "OUT_OF_ODD"
}

@dataclass
class StreamMetadata:
    dataset_id: str
    source_type: str
    camera_id: str
    camera_height_m: Optional[float]
    camera_pitch_deg: Optional[float]
    camera_roll_deg: Optional[float]
    floor_slope_deg: Optional[float]
    illumination_lux: Optional[float]
    fps: Optional[float]
    resolution: str
    warehouse_sector: str
    layout_id: str
    capture_date: str
    split: str
    odd_tier: str
    source_sha256: str
    annotation_status: str

    def validate(self):
        if self.split not in VALID_SPLITS:
            raise ValueError(f"Invalid split '{self.split}'. Must be one of {VALID_SPLITS}")
        if self.source_type not in VALID_SOURCE_TYPES:
            raise ValueError(f"Invalid source_type '{self.source_type}'. Must be one of {VALID_SOURCE_TYPES}")
        if self.odd_tier not in VALID_ODD_TIERS:
            raise ValueError(f"Invalid odd_tier '{self.odd_tier}'. Must be one of {VALID_ODD_TIERS}")
        if not self.dataset_id or not self.camera_id or not self.source_sha256:
            raise ValueError("dataset_id, camera_id, and source_sha256 must not be empty.")

class DatasetRegistry:
    def __init__(self, registry_file: Optional[Path] = None):
        self.streams: Dict[str, StreamMetadata] = {}
        self.blind_locked: bool = True
        self.registry_file = registry_file

    def register_stream(self, stream: StreamMetadata):
        stream.validate()
        if stream.dataset_id in self.streams:
            raise ValueError(f"Stream {stream.dataset_id} already registered.")
        self.streams[stream.dataset_id] = stream

    def get_split(self, split_name: str, allow_blind_access: bool = False) -> List[StreamMetadata]:
        if split_name not in VALID_SPLITS:
            raise ValueError(f"Unknown split: {split_name}")
        if split_name == "V3.3_BLIND" and self.blind_locked and not allow_blind_access:
            raise PermissionError(
                "BLIND SET ACCESS DENIED: V3.3_BLIND is quarantined. Calibration/tuning phase cannot access blind data."
            )
        return [s for s in self.streams.values() if s.split == split_name]

    def check_leakage(self) -> Dict[str, Any]:
        """Verify zero stream or hash overlap between calibration and validation/blind splits."""
        calib = {s.dataset_id: s.source_sha256 for s in self.streams.values() if s.split == "V3.3_CALIBRATION"}
        val_blind = {s.dataset_id: s.source_sha256 for s in self.streams.values() if s.split in ["V3.3_VALIDATION", "V3.3_BLIND"]}

        id_leakage = set(calib.keys()).intersection(set(val_blind.keys()))
        hash_leakage = set(calib.values()).intersection(set(val_blind.values()))

        return {
            "leakage_detected": len(id_leakage) > 0 or len(hash_leakage) > 0,
            "conflicting_dataset_ids": list(id_leakage),
            "conflicting_sha256_hashes": list(hash_leakage),
            "total_registered_streams": len(self.streams)
        }

    def save_registry(self, target_path: Path):
        data = {
            "registry_version": "V3.3_STREAM_REGISTRY",
            "streams": {k: asdict(v) for k, v in self.streams.items()}
        }
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load_registry(cls, source_path: Path) -> "DatasetRegistry":
        inst = cls(registry_file=source_path)
        with open(source_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for k, v in data.get("streams", {}).items():
            inst.register_stream(StreamMetadata(**v))
        return inst
