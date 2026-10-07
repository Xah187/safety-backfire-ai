#!/usr/bin/env python3
"""
scripts/v3_4/create_blind_manifest.py
Safety Backfire AI — Version V3.4 Blind Evaluation Split Tool.

Enforces facility-level blind holdouts for external facility safety benchmarking.
Guarantees:
  1. No frame-level or camera-level data leakage across partitions for the same facility.
  2. Ground-truth annotation files (detection_gt, trajectory_gt, intervention_event)
     are withheld and replaced by cryptographic hash commitments.
  3. Evaluation harness receives only unlabelled raw streams and camera surveys.
"""

import sys
import os
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Set, Optional

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))


class BlindSplitError(Exception):
    """Raised when a proposed evaluation split violates facility-level holdout rules."""
    pass


def compute_sha256(file_path: Path) -> str:
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def create_facility_blind_manifest(
    facilities_manifests: List[Path],
    held_out_facilities: List[str],
    output_manifest_path: Path,
    manifest_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Constructs a facility-level blind evaluation manifest.
    
    Args:
        facilities_manifests: List of paths to acquisition_manifest.json for ingested facilities.
        held_out_facilities: List of facility_ids designated for blind evaluation.
        output_manifest_path: Path to write the resulting blind evaluation manifest.
        manifest_id: Optional identifier string.
    """
    output_manifest_path = Path(output_manifest_path).resolve()
    held_out_set = set(held_out_facilities)

    facility_splits: Dict[str, str] = {}
    unlabelled_assets: List[Dict[str, Any]] = []
    withheld_gt_hashes: Dict[str, str] = {}

    all_facility_ids: Set[str] = set()

    for mf_path in facilities_manifests:
        mf_path = Path(mf_path).resolve()
        if not mf_path.is_file():
            raise FileNotFoundError(f"Acquisition manifest not found: {mf_path}")

        with open(mf_path, "r", encoding="utf-8") as f:
            m_data = json.load(f)

        fac_id = m_data.get("facility_id")
        if not fac_id:
            raise BlindSplitError(f"Manifest {mf_path} missing facility_id")

        if fac_id in all_facility_ids:
            raise BlindSplitError(f"Duplicate facility_id '{fac_id}' across manifests. Each facility must be partitioned as a single indivisible unit.")
        all_facility_ids.add(fac_id)

        # Assign split
        split = "BLIND_EVALUATION" if fac_id in held_out_set else "TRAIN_EXPLORATION"
        facility_splits[fac_id] = split

        base_dir = mf_path.parent
        sha_manifest = m_data.get("sha256_manifest", {})

        # Collect raw videos and surveys for held-out facilities
        if split == "BLIND_EVALUATION":
            raw_dir = base_dir / "raw"
            if not raw_dir.is_dir():
                raw_dir = base_dir

            video_files = list(raw_dir.glob("*.mp4")) + list(raw_dir.glob("*.mkv")) + list(raw_dir.glob("*.avi"))
            survey_file = base_dir / "metadata" / "camera_survey.json"
            if not survey_file.is_file():
                survey_file = base_dir / "camera_survey.json"

            survey_rel = str(survey_file.relative_to(base_dir)) if survey_file.is_file() else "UNKNOWN"

            for vf in sorted(video_files):
                cam_id = vf.stem
                vf_rel = str(vf.relative_to(base_dir))
                v_hash = sha_manifest.get(vf_rel, compute_sha256(vf) if vf.is_file() else "0"*64)

                unlabelled_assets.append({
                    "facility_id": fac_id,
                    "camera_id": cam_id,
                    "video_rel_path": vf_rel,
                    "camera_survey_rel_path": survey_rel,
                    "sha256": v_hash
                })

            # Commit withheld GT file hashes
            for gt_name in ["detection_gt.json", "trajectory_gt.json", "intervention_event.json", "risk_evidence.json"]:
                for candidate in [base_dir / "annotations" / gt_name, base_dir / gt_name]:
                    if candidate.is_file():
                        rel = str(candidate.relative_to(base_dir))
                        gt_hash = sha_manifest.get(rel, compute_sha256(candidate))
                        withheld_gt_hashes[f"{fac_id}::{gt_name}"] = gt_hash

    if not held_out_set.issubset(all_facility_ids):
        missing = held_out_set - all_facility_ids
        raise BlindSplitError(f"Held-out facility_id(s) {missing} not found among ingested manifests: {all_facility_ids}")

    if not unlabelled_assets:
        raise BlindSplitError("No assets available for blind evaluation. Ensure held-out facilities contain valid video streams.")

    if not manifest_id:
        manifest_id = f"BLIND_MANIFEST_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    blind_manifest = {
        "manifest_id": manifest_id,
        "creation_timestamp": datetime.now(timezone.utc).isoformat(),
        "milestone": "SAFETY_BACKFIRE_AI_V3.4",
        "split_policy": "FACILITY_LEVEL_HOLDOUT",
        "facility_splits": facility_splits,
        "held_out_facilities": sorted(list(held_out_set)),
        "unlabelled_evaluation_assets": unlabelled_assets,
        "withheld_ground_truth_hashes": withheld_gt_hashes,
        "access_lock_status": "LOCKED_UNTIL_EVALUATION_COMPLETION"
    }

    output_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_manifest_path, "w", encoding="utf-8") as f:
        json.dump(blind_manifest, f, indent=2)

    return blind_manifest


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Create Facility-Level Blind Evaluation Manifest")
    parser.add_argument("--manifests", nargs="+", required=True, help="List of paths to acquisition_manifest.json")
    parser.add_argument("--held-out", nargs="+", required=True, help="List of facility IDs for blind evaluation")
    parser.add_argument("--output", default="outputs/v3_4/manifests/blind_evaluation_manifest.json", help="Output blind manifest path")
    parser.add_argument("--id", help="Optional blind manifest ID")

    args = parser.parse_args()
    manifest_paths = [Path(p) for p in args.manifests]
    out_path = Path(args.output)

    try:
        res = create_facility_blind_manifest(manifest_paths, args.held_out, out_path, args.id)
        print(f"🟢 Successfully created blind evaluation manifest: {out_path}")
        print(f"   Held-out facilities: {res['held_out_facilities']}")
        print(f"   Unlabelled assets: {len(res['unlabelled_evaluation_assets'])}")
        print(f"   Withheld GT commitments: {len(res['withheld_ground_truth_hashes'])}")
    except BlindSplitError as e:
        print(f"🔴 BLIND SPLIT ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
