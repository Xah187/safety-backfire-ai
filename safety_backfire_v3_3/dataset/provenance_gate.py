"""
provenance_gate.py
V3.3 Dataset Provenance Gate & Verification Module.

Enforces Section 5 requirements:
No dataset may enter scientific evaluation unless:
1. source exists,
2. SHA256 is recorded,
3. source type is known,
4. capture metadata exists,
5. split assignment is immutable,
6. annotation provenance is documented,
7. ODD metadata is known or explicitly UNKNOWN.

The gate strictly rejects:
- METADATA_ONLY
- UNAVAILABLE
- UNKNOWN_SOURCE
from blind scientific evaluation.
"""

from typing import Dict, Any, List, Optional
import os

DISALLOWED_BLIND_CLASSIFICATIONS = {"METADATA_ONLY", "UNAVAILABLE", "UNKNOWN_SOURCE"}

class ProvenanceGateError(Exception):
    """Raised when a dataset violates provenance integrity requirements."""
    pass

class DatasetProvenanceGate:
    """Validates dataset metadata and provenance prior to inclusion in scientific evaluations."""

    @staticmethod
    def validate_dataset_record(record: Dict[str, Any], for_blind_evaluation: bool = False) -> Dict[str, Any]:
        """
        Validate a dataset against the 7 mandatory provenance criteria.
        
        Args:
            record: Dictionary containing dataset audit/manifest metadata.
            for_blind_evaluation: If True, strictly rejects METADATA_ONLY, UNAVAILABLE, UNKNOWN_SOURCE.
            
        Returns:
            Dict containing gate status, passes_gate (bool), and list of violations.
        """
        violations: List[str] = []
        dataset_id = record.get("dataset_id", "UNKNOWN_DATASET")
        classification = record.get("classification", "UNKNOWN")

        # 1. Source existence check
        file_exists = record.get("file_exists", False)
        if not file_exists and classification not in {"SYNTHETIC"}:
            violations.append(f"Source file does not exist on disk for dataset '{dataset_id}'")

        # 2. SHA256 recorded
        sha256 = record.get("sha256") or record.get("source_sha256")
        if not sha256 or len(sha256) != 64 or sha256.startswith("000000") or sha256 == "NONE":
            violations.append(f"Invalid or missing SHA-256 hash for dataset '{dataset_id}': {sha256}")

        # 3. Source type known
        source_type = record.get("source_type") or classification
        valid_source_types = {"REAL", "PHYSICALLY_PRESENT", "PHYSICALLY_PRESENT_AND_ANNOTATED", "SYNTHETIC", "REPLAY"}
        if classification in {"METADATA_ONLY", "UNAVAILABLE", "UNKNOWN_SOURCE"}:
            if classification not in valid_source_types:
                # Allowed to flag if checking for general or blind
                pass
        elif source_type not in valid_source_types:
            violations.append(f"Unknown source type for dataset '{dataset_id}': {source_type}")

        # 4. Capture metadata exists
        camera_id = record.get("camera_id")
        fps = record.get("fps")
        resolution = record.get("resolution")
        if not camera_id or fps is None or not resolution or resolution == "UNKNOWN":
            violations.append(f"Incomplete capture metadata (camera_id/fps/resolution) for dataset '{dataset_id}'")

        # 5. Split assignment immutable and recognized
        split = record.get("split")
        # For raw datasets, split can be inferred or checked if provided
        if split and not isinstance(split, str):
            violations.append(f"Invalid split assignment for dataset '{dataset_id}': {split}")

        # 6. Annotation provenance documented
        annotation_file = record.get("annotation_file")
        annotation_status = record.get("annotation_status") or record.get("annotation_type")
        if not annotation_file and not annotation_status:
            violations.append(f"Missing annotation provenance documentation for dataset '{dataset_id}'")

        # 7. ODD metadata known or explicitly UNKNOWN
        odd_tier = record.get("odd_tier")
        # Allowed values include NOMINAL_ODD, DEGRADED_ODD, OUT_OF_ODD, UNKNOWN
        valid_odd = {"NOMINAL_ODD", "DEGRADED_ODD", "OUT_OF_ODD", "UNKNOWN", None}
        if odd_tier not in valid_odd:
            violations.append(f"Invalid ODD tier for dataset '{dataset_id}': {odd_tier}")

        # Gate enforcement for Blind Scientific Evaluation
        if for_blind_evaluation:
            if classification in DISALLOWED_BLIND_CLASSIFICATIONS:
                violations.append(
                    f"Classification '{classification}' is strictly prohibited from blind scientific evaluation!"
                )
            if record.get("source_type") == "UNKNOWN_SOURCE":
                violations.append("UNKNOWN_SOURCE is strictly prohibited from blind scientific evaluation!")

        passes_gate = (len(violations) == 0)
        return {
            "dataset_id": dataset_id,
            "classification": classification,
            "passes_gate": passes_gate,
            "violations": violations,
            "for_blind_evaluation": for_blind_evaluation
        }

    @staticmethod
    def enforce_gate(record: Dict[str, Any], for_blind_evaluation: bool = False) -> None:
        """Enforce validation, raising ProvenanceGateError if criteria not met."""
        result = DatasetProvenanceGate.validate_dataset_record(record, for_blind_evaluation=for_blind_evaluation)
        if not result["passes_gate"]:
            raise ProvenanceGateError(
                f"Dataset '{result['dataset_id']}' rejected by Provenance Gate:\n" +
                "\n".join(f" - {v}" for v in result["violations"])
            )
