"""
setup_human_adjudication.py
Milestone V3.4-C — Human Adjudication Infrastructure & Review Packages Setup

GOVERNANCE SPECIFICATION:
  - Divides 51 union events into:
    * 38 ELIGIBLE events (window_valid == True)
    * 13 INELIGIBLE events (window_valid == False; status: INELIGIBLE_WINDOW)
  - Creates outputs/v3_4/adjudication/<event_id>/ for eligible events:
    * review_metadata.json
    * reviewer_1_form.json
    * reviewer_2_form.json
    * adjudication_form.json
    * before.mp4, intervention.mp4, after.mp4 (derived clips)
  - STRICT BLINDING: Zero AI relevance scores, zero YOLO boxes, zero ByteTrack IDs,
    zero Model H values, zero automated Backfire suggestions.
  - STRICT AGENT PROHIBITION: The Agent is forbidden from guessing or auto-populating
    BACKFIRE / NO_BACKFIRE / AMBIGUOUS. All decisions remain PENDING_HUMAN_REVIEW.
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone
import cv2

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent

UNION_REGISTRY_PATH = WORKSPACE_ROOT / "outputs/v3_4/candidates/union_events_registry.json"
BASE_ADJUDICATION_DIR = WORKSPACE_ROOT / "outputs/v3_4/adjudication"
BASE_GROUND_TRUTH_DIR = WORKSPACE_ROOT / "outputs/v3_4/ground_truth"

WH026_VIDEOS = WORKSPACE_ROOT / "data/external_facility/raw/Warehouse_026/MTMC_Tracking_2026/test/Warehouse_026/videos"
WH027_VIDEOS = WORKSPACE_ROOT / "data/external_facility_02/raw/Warehouse_027/MTMC_Tracking_2026/test/Warehouse_027/videos"


def get_file_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def extract_derived_clip(src_video_path, start_frame, end_frame, out_clip_path, fps=30.0):
    if end_frame < start_frame:
        return
    cap = cv2.VideoCapture(str(src_video_path))
    if not cap.isOpened():
        return
    
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*"avc1")
    out = cv2.VideoWriter(str(out_clip_path), fourcc, fps, (width, height))
    
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    current_f = start_frame
    
    while current_f <= end_frame:
        ret, frame = cap.read()
        if not ret:
            break
        out.write(frame)
        current_f += 1
        
    cap.release()
    out.release()


def setup_event_package(event, is_eligible):
    event_id = event["union_id"]
    event_dir = BASE_ADJUDICATION_DIR / event_id
    event_dir.mkdir(parents=True, exist_ok=True)
    
    scene = event["scene_id"]
    cam = event["camera_id"]
    v_base = WH026_VIDEOS if scene == "Warehouse_026" else WH027_VIDEOS
    src_video = v_base / f"{cam}.mp4"
    src_sha256 = get_file_sha256(src_video) if src_video.exists() else "SOURCE_FILE_NOT_FOUND"
    
    win = event.get("screening_windows", {})
    psf = win.get("pre", {}).get("start_frame", 0)
    pef = win.get("pre", {}).get("end_frame", 0)
    isf = win.get("intervention", {}).get("start_frame", 0)
    ief = win.get("intervention", {}).get("end_frame", 0)
    post_sf = win.get("post", {}).get("start_frame", 0)
    post_ef = win.get("post", {}).get("end_frame", 0)
    
    # 1. Video extraction only for eligible events
    if is_eligible and src_video.exists():
        extract_derived_clip(src_video, psf, pef, event_dir / "before.mp4")
        extract_derived_clip(src_video, isf, ief, event_dir / "intervention.mp4")
        extract_derived_clip(src_video, post_sf, post_ef, event_dir / "after.mp4")
        
    # Calculate package hash
    pkg_hash_input = f"{event_id}_{src_sha256}_{psf}_{ief}_{post_ef}"
    package_hash = hashlib.sha256(pkg_hash_input.encode("utf-8")).hexdigest()
    
    # 2. review_metadata.json (STRICTLY BLINDED: No AI scores or Backfire suggestions)
    review_metadata = {
        "event_id": event_id,
        "primary_candidate_id": event["primary_id"],
        "discovery_channel": event["discovery_source"],
        "facility_scene": scene,
        "camera_stream": cam,
        "source_video": src_video.name,
        "source_video_sha256": src_sha256,
        "package_hash": package_hash,
        "review_version": "V3.4_C_BLIND_ADJUDICATION_V1",
        "eligibility_status": "ELIGIBLE_FOR_ADJUDICATION" if is_eligible else "INELIGIBLE_WINDOW",
        "window_valid": is_eligible,
        "window_invalidation_reasons": event.get("window_invalidation_reasons", []),
        "temporal_window_bounds": {
            "pre": {
                "start_frame": psf,
                "end_frame": pef,
                "timestamp_start_s": round(psf / 30.0, 2),
                "timestamp_end_s": round(pef / 30.0, 2),
                "duration_s": round(max(0, pef - psf + 1) / 30.0, 2),
                "clip_filename": "before.mp4" if is_eligible else None
            },
            "intervention": {
                "start_frame": isf,
                "end_frame": ief,
                "timestamp_start_s": round(isf / 30.0, 2),
                "timestamp_end_s": round(ief / 30.0, 2),
                "duration_s": round(max(0, ief - isf + 1) / 30.0, 2),
                "clip_filename": "intervention.mp4" if is_eligible else None
            },
            "post": {
                "start_frame": post_sf,
                "end_frame": post_ef,
                "timestamp_start_s": round(post_sf / 30.0, 2),
                "timestamp_end_s": round(post_ef / 30.0, 2),
                "duration_s": round(max(0, post_ef - post_sf + 1) / 30.0, 2),
                "clip_filename": "after.mp4" if is_eligible else None
            }
        },
        "spatial_zones": {
            "primary_zone": {
                "zone_id": event["possible_primary_zone"],
                "zone_status": "DATASET_GEOMETRIC" if "Camera_0002" in event["possible_primary_zone"] else "PROVISIONAL"
            },
            "secondary_zone": {
                "zone_id": event["possible_secondary_zone"] if event["possible_secondary_zone"] != "UNKNOWN" else "UNKNOWN",
                "zone_status": "PROVISIONAL" if event["possible_secondary_zone"] != "UNKNOWN" else "UNKNOWN"
            }
        },
        "adjudication_readiness": "AWAITING_HUMAN_ASSESSORS" if is_eligible else "EXCLUDED_FROM_ADJUDICATION"
    }
    with open(event_dir / "review_metadata.json", "w") as f:
        json.dump(review_metadata, f, indent=2)
        
    # 3. reviewer_1_form.json
    reviewer_1_form = {
        "event_id": event_id,
        "reviewer_slot": "REVIEWER_1",
        "reviewer_id": None,
        "review_start_timestamp_utc": None,
        "review_completion_timestamp_utc": None,
        "status": "PENDING_HUMAN_REVIEW",
        "criteria_evaluations": {
            "intervention_visible": None,           # YES / NO / UNKNOWN
            "primary_risk_present": None,           # YES / NO / UNKNOWN
            "primary_risk_reduced": None,           # YES / NO / UNKNOWN
            "secondary_risk_changed": None,         # YES / NO / UNKNOWN
            "causal_mechanism_observed": None,      # YES / NO / UNKNOWN
            "independent_evidence_present": None,   # YES / NO / UNKNOWN
            "evidence_quality": None                # HIGH / MEDIUM / LOW / UNKNOWN
        },
        "causal_link_confidence": None,             # DIRECTLY_OBSERVED / TELEMETRY_SUPPORTED / PLAUSIBLE_BUT_UNCONFIRMED / NOT_ESTABLISHED
        "label_decision": None,                     # BACKFIRE / NO_BACKFIRE / AMBIGUOUS
        "reviewer_notes": "",
        "submission_signature": None
    }
    with open(event_dir / "reviewer_1_form.json", "w") as f:
        json.dump(reviewer_1_form, f, indent=2)
        
    # 4. reviewer_2_form.json (STRICTLY ISOLATED from Reviewer 1)
    reviewer_2_form = {
        "event_id": event_id,
        "reviewer_slot": "REVIEWER_2",
        "reviewer_id": None,
        "review_start_timestamp_utc": None,
        "review_completion_timestamp_utc": None,
        "status": "PENDING_HUMAN_REVIEW",
        "criteria_evaluations": {
            "intervention_visible": None,           # YES / NO / UNKNOWN
            "primary_risk_present": None,           # YES / NO / UNKNOWN
            "primary_risk_reduced": None,           # YES / NO / UNKNOWN
            "secondary_risk_changed": None,         # YES / NO / UNKNOWN
            "causal_mechanism_observed": None,      # YES / NO / UNKNOWN
            "independent_evidence_present": None,   # YES / NO / UNKNOWN
            "evidence_quality": None                # HIGH / MEDIUM / LOW / UNKNOWN
        },
        "causal_link_confidence": None,             # DIRECTLY_OBSERVED / TELEMETRY_SUPPORTED / PLAUSIBLE_BUT_UNCONFIRMED / NOT_ESTABLISHED
        "label_decision": None,                     # BACKFIRE / NO_BACKFIRE / AMBIGUOUS
        "reviewer_notes": "",
        "submission_signature": None
    }
    with open(event_dir / "reviewer_2_form.json", "w") as f:
        json.dump(reviewer_2_form, f, indent=2)
        
    # 5. adjudication_form.json
    adjudication_form = {
        "event_id": event_id,
        "adjudicator_id": None,
        "decision_timestamp_utc": None,
        "status": "PENDING_HUMAN_REVIEW",
        "reviewer_1_label": None,
        "reviewer_2_label": None,
        "disagreement": False,
        "disagreement_reason": "",
        "adjudicator_label": "PENDING_HUMAN_REVIEW", # Allowed final: BACKFIRE, NO_BACKFIRE, AMBIGUOUS
        "adjudicator_notes": "",
        "final_evidence_quality": None,              # HIGH / MEDIUM / LOW / UNKNOWN
        "final_causal_link": None                    # DIRECTLY_OBSERVED / TELEMETRY_SUPPORTED / PLAUSIBLE_BUT_UNCONFIRMED / NOT_ESTABLISHED
    }
    with open(event_dir / "adjudication_form.json", "w") as f:
        json.dump(adjudication_form, f, indent=2)


def main():
    print("=== Milestone V3.4-C Human Adjudication Infrastructure Setup ===")
    BASE_ADJUDICATION_DIR.mkdir(parents=True, exist_ok=True)
    BASE_GROUND_TRUTH_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(UNION_REGISTRY_PATH) as f:
        reg = json.load(f)
        
    union_records = reg.get("union_records", [])
    total_events = len(union_records)
    print(f"Loaded {total_events} events from union registry.")
    
    eligible_events = [e for e in union_records if e.get("window_valid", False)]
    ineligible_events = [e for e in union_records if not e.get("window_valid", False)]
    
    print(f"Eligible for Adjudication (WINDOW_VALID = TRUE): {len(eligible_events)}")
    print(f"Ineligible (WINDOW_VALID = FALSE; status: INELIGIBLE_WINDOW): {len(ineligible_events)}")
    
    # Setup packages for all 51 events (38 eligible + 13 ineligible cataloged with review_metadata)
    for idx, e in enumerate(union_records):
        is_elig = e.get("window_valid", False)
        setup_event_package(e, is_elig)
        if (idx + 1) % 10 == 0 or (idx + 1) == total_events:
            print(f"  Processed {idx + 1}/{total_events} packages...")
            
    # Initialize Ground Truth file container (Strictly empty of unadjudicated claims)
    gt_container = {
        "ground_truth_version": "V3.4_C_SAFETY_BACKFIRE_EVENT_GT_V1",
        "generation_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "governance_status": "PENDING_HUMAN_REVIEW",
        "epistemic_standard": "INDEPENDENT_HUMAN_ADJUDICATION_ONLY",
        "total_verified_gt_events": 0,
        "eligible_candidate_events_pool": len(eligible_events),
        "ineligible_events_pool": len(ineligible_events),
        "adjudicated_events": []
    }
    with open(BASE_GROUND_TRUTH_DIR / "safety_backfire_event_gt.json", "w") as f:
        json.dump(gt_container, f, indent=2)
        
    print(f"Human Adjudication setup complete at {BASE_ADJUDICATION_DIR}")
    print(f"Ground Truth container initialized at {BASE_GROUND_TRUTH_DIR / 'safety_backfire_event_gt.json'}")

if __name__ == "__main__":
    main()
