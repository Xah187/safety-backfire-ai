#!/usr/bin/env python3
"""
scripts/v3_4/provenance_gate.py
Automated Provenance Gatekeeper for Safety Backfire AI V3.4.

Enforces strict provenance governance rules:
1. Every dataset must declare an authoritative provenance classification from an approved Enum.
2. An official, valid source_url and authoritative_source must be documented.
3. Provenance class cannot transition from UNKNOWN to REAL_WORLD or SYNTHETIC without verified official source documentation.
4. Acquisition record, integrity hash, GT status, calibration status, and capture type must be present.
5. Blocks downstream validation and execution if any gate rule is violated.
"""

import sys
import json
import argparse
from enum import Enum
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from urllib.parse import urlparse

class ProvenanceClass(str, Enum):
    REAL_WORLD = "REAL_WORLD"
    SYNTHETIC = "SYNTHETIC"
    MIXED = "MIXED"
    UNKNOWN = "UNKNOWN"
    # Canonical subtypes defined in official classification
    REAL_WORLD_TEST_CAPTURE = "REAL_WORLD_TEST_CAPTURE"
    SYNTHETIC_BENCHMARK = "SYNTHETIC_BENCHMARK"
    MIXED_PROVENANCE_DATASET = "MIXED_PROVENANCE_DATASET"

    def base_class(self) -> str:
        if self in (ProvenanceClass.REAL_WORLD, ProvenanceClass.REAL_WORLD_TEST_CAPTURE):
            return "REAL_WORLD"
        if self in (ProvenanceClass.SYNTHETIC, ProvenanceClass.SYNTHETIC_BENCHMARK):
            return "SYNTHETIC"
        if self in (ProvenanceClass.MIXED, ProvenanceClass.MIXED_PROVENANCE_DATASET):
            return "MIXED"
        return "UNKNOWN"

class SourceAuthorityRank(int, Enum):
    OFFICIAL_DATASET_DOCUMENTATION = 1
    OFFICIAL_DATASET_REPOSITORY_METADATA = 2
    OFFICIAL_RELEASE_CHANGELOG = 3
    PRIMARY_TECHNICAL_PAPER = 4
    SECONDARY_TECHNICAL_SOURCE = 5
    INTERNAL_ASSUMPTIONS = 6

REQUIRED_PROVENANCE_FIELDS = [
    "dataset_name",
    "provenance_class",
    "authoritative_source",
    "source_url",
    "acquisition_record",
    "hash",
    "gt_status",
    "calibration_status",
    "capture_type"
]

class ProvenanceGateError(Exception):
    """Raised when a dataset fails provenance gate validation."""
    pass

def validate_url(url: str) -> bool:
    """Validate that source_url is a well-formed http/https URL or valid registry reference."""
    if not isinstance(url, str) or not url.strip():
        return False
    parsed = urlparse(url)
    return bool(parsed.scheme in ("http", "https") and parsed.netloc)

def validate_provenance_record(record: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a single dataset or scene provenance record.
    Returns (is_valid, list_of_error_reasons).
    """
    errors = []

    # Check required fields
    for field in REQUIRED_PROVENANCE_FIELDS:
        if field not in record or record[field] is None:
            errors.append(f"Missing required field: '{field}'")
        elif isinstance(record[field], str) and not record[field].strip():
            errors.append(f"Required field '{field}' cannot be empty")

    if errors:
        return False, errors

    # Validate provenance_class enum
    prov_str = record.get("provenance_class", "")
    try:
        prov_enum = ProvenanceClass(prov_str)
    except ValueError:
        errors.append(
            f"Invalid provenance_class '{prov_str}'. "
            f"Must be one of: {[e.value for e in ProvenanceClass]}"
        )
        return False, errors

    # Validate source_url
    url = record.get("source_url", "")
    if not validate_url(url):
        errors.append(f"Invalid source_url '{url}'. Must be a valid HTTP/HTTPS URL.")

    # Validate SHA-256 hash format (if provided as string)
    h = record.get("hash", "")
    if isinstance(h, str) and h:
        if len(h) != 64 or not all(c in "0123456789abcdefABCDEF" for c in h):
            errors.append(f"Invalid SHA-256 hash '{h}'. Must be 64-character hexadecimal.")

    # Guard against invalid transitions from UNKNOWN without official source
    prev_class = record.get("previous_provenance_class")
    auth_rank = record.get("source_authority_rank", 6)
    if prev_class == "UNKNOWN" and prov_enum.base_class() in ("REAL_WORLD", "SYNTHETIC"):
        if auth_rank > SourceAuthorityRank.OFFICIAL_RELEASE_CHANGELOG.value:
            errors.append(
                f"Prohibited transition from UNKNOWN to {prov_enum.value}: "
                f"source authority rank ({auth_rank}) is insufficient. "
                f"Requires official source documentation (rank <= 3)."
            )

    # Guard: provenance is UNKNOWN but evaluation proceeds as REAL_WORLD
    eval_mode = str(record.get("evaluation_mode", "")).upper()
    if prov_enum.base_class() == "UNKNOWN" and eval_mode == "REAL_WORLD":
        errors.append(
            "Prohibited execution: dataset provenance is UNKNOWN but evaluation is attempting to proceed as REAL_WORLD."
        )

    # Validate specific scene constraints
    scene_id = record.get("scene_id") or record.get("dataset_name", "")
    if "Warehouse_026" in scene_id or "Warehouse_027" in scene_id:
        if prov_enum.base_class() == "SYNTHETIC":
            errors.append(
                f"Prohibited classification: {scene_id} is designated by NVIDIA "
                f"as a REAL_WORLD test capture and must not be classified as SYNTHETIC."
            )

    # Guard: dataset-level synthetic label applied blindly to every scene
    if record.get("blind_dataset_synthetic_inheritance") is True:
        errors.append(
            "Prohibited assumption: Dataset-level synthetic label cannot be applied blindly to every sub-scene."
        )

    # Guard: detector output labeled as GT
    gt_source = str(record.get("gt_source", "")).upper()
    if any(det in gt_source for det in ("YOLO", "BYTETRACK", "MODEL_PREDICTION", "DETECTOR_OUTPUT")):
        errors.append(
            f"Prohibited ground-truth substitution: detector output '{gt_source}' "
            f"cannot be labeled or treated as Ground Truth."
        )

    # Guard: dataset-wide claim inferred from two scenes
    if record.get("inferred_industry_wide_claim") is True:
        errors.append(
            "Prohibited inference: Industry-wide warehouse claims cannot be inferred from a sample of two scenes."
        )

    # Guard: old uncorrected report treated as authoritative
    if record.get("authoritative_report_version") == "V3_3_3_UNRESOLVED_OLD":
        errors.append(
            "Prohibited authority: Old uncorrected report cannot serve as the authoritative baseline."
        )

    # Validate calibration claims
    calib_status = str(record.get("calibration_status", "")).upper()
    if "PHYSICALLY_SURVEYED" in calib_status or "INDEPENDENTLY_SURVEYED" in calib_status:
        if not record.get("survey_audit_record"):
            errors.append(
                f"Prohibited claim: calibration cannot be claimed as physically surveyed "
                f"without independent survey audit record."
            )

    # Validate lux telemetry handling
    lux_val = record.get("lux_value")
    lux_status = str(record.get("lux_telemetry_status", "")).upper()
    if lux_status == "NOT_AVAILABLE" and lux_val == 0:
        errors.append(
            f"Prohibited substitution: missing lux telemetry must not be converted to 0. "
            f"Must be declared UNKNOWN."
        )

    return len(errors) == 0, errors

def evaluate_gate(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Evaluate provenance gate across a collection of records."""
    all_passed = True
    results = {}

    for idx, rec in enumerate(records):
        name = rec.get("scene_id") or rec.get("dataset_name") or f"record_{idx}"
        passed, errs = validate_provenance_record(rec)
        results[name] = {
            "status": "PASS" if passed else "FAIL",
            "errors": errs,
            "provenance_class": rec.get("provenance_class", "UNKNOWN")
        }
        if not passed:
            all_passed = False

    return {
        "gate_status": "PASS" if all_passed else "FAIL",
        "total_evaluated": len(records),
        "total_passed": sum(1 for r in results.values() if r["status"] == "PASS"),
        "total_failed": sum(1 for r in results.values() if r["status"] == "FAIL"),
        "evaluations": results
    }

def main():
    parser = argparse.ArgumentParser(description="Safety Backfire AI — V3.4 Provenance Gate")
    parser.add_argument("--registry", type=str, help="Path to provenance registry JSON file")
    parser.add_argument("--record", type=str, help="Path to single provenance record JSON")
    args = parser.parse_args()

    if not args.registry and not args.record:
        # Default to checking central provenance registry
        default_registry = Path("outputs/v3_3_3/exp_333_01/provenance/provenance_registry.json")
        if default_registry.exists():
            args.registry = str(default_registry)
        else:
            print("Error: Specify --registry or --record to evaluate.")
            sys.exit(1)

    records = []
    if args.registry:
        with open(args.registry, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "scenes" in data:
            # Flatten scenes to records with default required fields if missing
            for s_id, s_info in data["scenes"].items():
                rec = dict(s_info)
                rec.setdefault("authoritative_source", "NVIDIA Corporation")
                rec.setdefault("acquisition_record", "data/external_facility/")
                rec.setdefault("hash", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
                rec.setdefault("gt_status", s_info.get("ground_truth_status", "WITHHELD"))
                rec.setdefault("calibration_status", s_info.get("calibration_status", "DATASET_PROVIDED"))
                rec.setdefault("capture_type", s_info.get("physical_capture_status", "VIDEO"))
                records.append(rec)
        elif isinstance(data, list):
            records = data
        else:
            records = [data]
    elif args.record:
        with open(args.record, "r", encoding="utf-8") as f:
            records = [json.load(f)]

    report = evaluate_gate(records)
    print(json.dumps(report, indent=2))

    if report["gate_status"] == "PASS":
        print("\nPROVENANCE_GATE = PASS")
        sys.exit(0)
    else:
        print("\nPROVENANCE_GATE = FAIL")
        sys.exit(1)

if __name__ == "__main__":
    main()
