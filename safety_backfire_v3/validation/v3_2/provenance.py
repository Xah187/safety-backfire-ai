"""
provenance.py
Safety Backfire AI - V3.2 Dataset Manifest and Independence Auditor
Enforces strict partition isolation: Development != Calibration != Validation != Blind Test.
"""

import os
import hashlib
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from safety_backfire_v3.validation.v3_2.metadata import VideoMetadataV1, LineageStatus, DatasetSplit

@dataclass
class DatasetManifestV1:
    manifest_version: str = "V3.2_MANIFEST_1.0"
    created_at_utc: str = "2026-09-24T11:45:00Z"
    dataset_name: str = "Warehouse_RealWorld_Corpus_V3_2"
    videos: Dict[str, VideoMetadataV1] = field(default_factory=dict)
    file_hashes: Dict[str, str] = field(default_factory=dict)
    splits: Dict[str, List[str]] = field(default_factory=dict)

    def register_video(self, meta: VideoMetadataV1, filepath: Path):
        self.videos[meta.video_id] = meta
        if filepath.exists():
            h = hashlib.sha256(filepath.read_bytes()).hexdigest()
            self.file_hashes[meta.video_id] = h
        else:
            self.file_hashes[meta.video_id] = "FILE_NOT_FOUND"
        
        split_key = meta.dataset_split.value
        if split_key not in self.splits:
            self.splits[split_key] = []
        if meta.video_id not in self.splits[split_key]:
            self.splits[split_key].append(meta.video_id)

    def audit_independence(self) -> Dict[str, Any]:
        """
        Verifies zero overlap between splits.
        """
        all_ids = []
        overlaps = {}
        split_keys = list(self.splits.keys())
        
        for i in range(len(split_keys)):
            for j in range(i + 1, len(split_keys)):
                k1, k2 = split_keys[i], split_keys[j]
                common = set(self.splits[k1]).intersection(set(self.splits[k2]))
                if common:
                    overlaps[f"{k1}_vs_{k2}"] = list(common)

        is_independent = len(overlaps) == 0
        return {
            "is_independent": is_independent,
            "total_videos": len(self.videos),
            "split_distribution": {k: len(v) for k, v in self.splits.items()},
            "overlaps": overlaps,
            "policy_adherence": "STRICT_ISOLATION_ENFORCED" if is_independent else "DATA_LEAKAGE_DETECTED"
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "manifest_version": self.manifest_version,
            "created_at_utc": self.created_at_utc,
            "dataset_name": self.dataset_name,
            "total_videos": len(self.videos),
            "splits": self.splits,
            "independence_audit": self.audit_independence(),
            "videos": {vid: v.to_dict() for vid, v in self.videos.items()},
            "file_hashes": self.file_hashes
        }
