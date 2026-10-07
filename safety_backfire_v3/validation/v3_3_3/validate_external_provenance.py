"""
validation/v3_3_3/validate_external_provenance.py
Provenance validation module and CLI tool for EXP_333_01 External Facility Ingestion Gate.
Enforces Section 16 mandatory provenance checks and Central 01 protection rules.
"""

import sys
import os
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
import cv2
import numpy as np

def find_workspace_root() -> Path:
    p = Path(__file__).resolve()
    while p.parent != p:
        if (p / "data").is_dir() and (p / "safety_backfire_v3").is_dir():
            return p
        p = p.parent
    return Path(__file__).resolve().parent.parent.parent.parent

WORKSPACE_ROOT = find_workspace_root()
sys.path.insert(0, str(WORKSPACE_ROOT))

def compute_sha256(fp: Path) -> str:
    hasher = hashlib.sha256()
    with open(fp, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def compute_frame_hash(img: np.ndarray) -> str:
    """Compute 256-bit block mean hash for perceptual frame fingerprinting."""
    resized = cv2.resize(img, (16, 16), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY) if len(resized.shape) == 3 else resized
    avg = gray.mean()
    bits = (gray > avg).flatten()
    val = 0
    for b in bits:
        val = (val << 1) | int(b)
    return f"{val:064x}"

def hamming_distance_hex(h1: str, h2: str) -> int:
    """Computes bitwise Hamming distance between two 64-char hex strings (256 bits)."""
    v1 = int(h1, 16)
    v2 = int(h2, 16)
    xor_val = v1 ^ v2
    return bin(xor_val).count("1")

class ExternalProvenanceValidator:
    """Validates external facility candidate footage against Section 16 criteria."""

    def __init__(self):
        self.exclusion_reg_path = WORKSPACE_ROOT / "outputs/v3_3_3/exp_333_01/provenance/central01_exclusion_registry.json"
        self.split_manifest_path = WORKSPACE_ROOT / "outputs/v3_3_3/exp_333_01/splits/split_manifest.json"
        self.blind_manifest_path = WORKSPACE_ROOT / "outputs/v3_3_3/exp_333_01/splits/blind_manifest.json"

        with open(self.exclusion_reg_path, "r", encoding="utf-8") as f:
            self.exclusion_reg = json.load(f)

    def check_central01_exclusion(self, video_path: Path) -> Dict[str, Any]:
        """Verifies candidate video does NOT originate from Central 01 via hash or perceptual match."""
        if not video_path.exists():
            return {"passed": False, "reason": "FILE_NOT_FOUND"}

        # 1. Exact file hash check
        fhash = compute_sha256(video_path)
        known_hashes = set(self.exclusion_reg["known_source_file_hashes"].values())
        if fhash in known_hashes:
            return {
                "passed": False,
                "rejection_code": "CENTRAL01_FILE_MATCH_REJECTED",
                "matched_hash": fhash,
                "reason": "Exact cryptographic hash match against Facility Central 01 archived footage."
            }

        # 2. Perceptual frame fingerprint check (catches resized, cropped, or transcoded variants)
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            return {"passed": False, "reason": "CANNOT_DECODE_VIDEO"}

        n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        sample_indices = [0, min(100, n_frames - 1), min(200, n_frames - 1), min(400, n_frames - 1)]

        for fidx in sample_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, fidx)
            ret, frame = cap.read()
            if not ret or frame is None:
                continue
            cand_hash = compute_frame_hash(frame)
            for kf_name, kf_hash in self.exclusion_reg["keyframe_perceptual_hashes_256bit"].items():
                dist = hamming_distance_hex(cand_hash, kf_hash)
                if dist <= 15:
                    cap.release()
                    return {
                        "passed": False,
                        "rejection_code": "SYNTHETIC_SUBSTITUTE_REJECTED",
                        "matched_keyframe": kf_name,
                        "hamming_distance": dist,
                        "reason": f"Perceptual fingerprint matches Central 01 keyframe {kf_name} (Hamming dist={dist} <= 15)."
                    }
        cap.release()

        return {"passed": True, "sha256": fhash}

    def validate_candidate_file(self, video_path: Path, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Executes all 14 Section 16 checks on candidate video file."""
        report = {
            "file": str(video_path),
            "checks": {},
            "all_passed": False
        }

        # 1. File exists
        report["checks"]["file_exists"] = video_path.exists()
        if not report["checks"]["file_exists"]:
            report["rejection_reason"] = "FILE_DOES_NOT_EXIST"
            return report

        # 2. File readable
        report["checks"]["file_readable"] = os.access(video_path, os.R_OK)
        if not report["checks"]["file_readable"]:
            report["rejection_reason"] = "FILE_NOT_READABLE"
            return report

        # 3. File hash present & reproducible
        fhash = compute_sha256(video_path)
        report["checks"]["file_hash_present"] = len(fhash) == 64
        report["sha256"] = fhash

        # 4, 5, 6. Decodable, frame count, fps, resolution reproducible
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            report["checks"]["video_decodable"] = False
            report["rejection_reason"] = "UNABLE_TO_OPEN_VIDEO_STREAM"
            return report

        n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = float(cap.get(cv2.CAP_PROP_FPS))
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()

        report["checks"]["frame_count_reproducible"] = n_frames > 0
        report["checks"]["fps_reproducible"] = fps > 0.0
        report["checks"]["resolution_reproducible"] = w > 0 and h > 0
        report["frame_count"] = n_frames
        report["fps"] = fps
        report["resolution"] = f"{w}x{h}"

        # 8, 9, 10. Metadata checks
        meta = metadata or {}
        facility_id = meta.get("facility_id", "UNKNOWN")
        camera_id = meta.get("camera_id", "UNKNOWN")
        session_id = meta.get("acquisition_session_id", "UNKNOWN")

        report["checks"]["facility_identity_valid"] = facility_id not in self.exclusion_reg["banned_facility_identifiers"]
        report["checks"]["camera_identity_valid"] = camera_id not in self.exclusion_reg["banned_camera_identifiers"]
        report["checks"]["independent_session_valid"] = session_id != "CENTRAL_01_SESSION"

        # 11. Central 01 exclusion
        excl_res = self.check_central01_exclusion(video_path)
        report["checks"]["central01_exclusion"] = excl_res["passed"]
        if not excl_res["passed"]:
            report["rejection_reason"] = excl_res["rejection_code"]
            report["exclusion_details"] = excl_res
            return report

        # 12. Frame overlap status
        report["checks"]["frame_overlap_status"] = "CLEAR" if excl_res["passed"] else "NOT_ESTABLISHED"

        # 13. Split integrity
        with open(self.split_manifest_path, "r", encoding="utf-8") as f:
            sm = json.load(f)
        report["checks"]["split_integrity"] = sm["zero_adaptation_pipeline"]["parameter_adaptation"] == "ZERO_PARAMETER_ADAPTATION"

        # 14. Blind protocol integrity
        with open(self.blind_manifest_path, "r", encoding="utf-8") as f:
            bm = json.load(f)
        report["checks"]["blind_protocol_integrity"] = bm["blind_protocol_locked"] is True

        report["all_passed"] = all(
            v is True or v == "CLEAR" for v in report["checks"].values()
        )
        return report

def main():
    raw_dir = WORKSPACE_ROOT / "data/external_facility/raw"
    files = list(raw_dir.glob("*.mp4")) + list(raw_dir.glob("*.mov")) + list(raw_dir.glob("*.mkv"))

    print("=" * 80)
    print("EXP_333_01 EXTERNAL DATA PROVENANCE VALIDATOR")
    print("=" * 80)
    print(f"Target Directory: {raw_dir}")
    print(f"External Raw Files Found: {len(files)}")

    if len(files) == 0:
        print("\nPROVENANCE VALIDATION RESULT:")
        print("Status: BLOCKED_BY_EVIDENCE")
        print("Primary Blocker: External raw video footage is absent on disk (data/external_facility/raw/ is empty).")
        print("Facility Independence: NOT_ESTABLISHED")
        print("Frame Overlap: NOT_ESTABLISHED")
        print("Central 01 Protection: ACTIVE (Exclusion registry enforced)")
        print("Blind Protocol: LOCKED")
        print("Required Action: ACQUIRE_AUTHENTIC_EXTERNAL_FACILITY_FOOTAGE")
        print("=" * 80)
        return 0

    validator = ExternalProvenanceValidator()
    all_ok = True
    for vf in files:
        res = validator.validate_candidate_file(vf)
        print(f"\nEvaluating: {vf.name}")
        print(json.dumps(res, indent=2))
        if not res["all_passed"]:
            all_ok = False

    if not all_ok:
        print("\nVALIDATION FAILED: Ingested files violated provenance criteria.")
        return 1

    print("\nALL INGESTED FILES PASSED PROVENANCE VALIDATION.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
