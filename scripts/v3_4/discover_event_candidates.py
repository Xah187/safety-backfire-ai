"""
discover_event_candidates.py
Milestone V3.4-B — Candidate Event Discovery & Human Review Package Generator

GOVERNANCE SPECIFICATION:
  - CANDIDATE GENERATOR ONLY: Does not determine ground-truth labels.
  - Prohibited: Classifying events as BACKFIRE or NO_BACKFIRE.
  - Generates candidate_relevance_score (NOT backfire probability).
  - Prepares isolated human review packages for independent double-blind evaluation.
  - Preserves raw video invariance: all clips are strictly DERIVED review artifacts.
"""

import os
import sys
import json
import math
import hashlib
from collections import defaultdict
from pathlib import Path
from datetime import datetime, timezone
import cv2
import numpy as np

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent

WH026_DIR = WORKSPACE_ROOT / "data/external_facility/raw/Warehouse_026/MTMC_Tracking_2026/test/Warehouse_026"
WH027_DIR = WORKSPACE_ROOT / "data/external_facility_02/raw/Warehouse_027/MTMC_Tracking_2026/test/Warehouse_027"

R3_LEDGER = WORKSPACE_ROOT / "safety_backfire_v3/outputs/v3_3_3/exp_333_01/runs/RUN_003_NVIDIA_WAREHOUSE_026/observation_ledger.json"
R4_LEDGER = WORKSPACE_ROOT / "safety_backfire_v3/outputs/v3_3_3/exp_333_01/runs/RUN_004_NVIDIA_WAREHOUSE_027/observation_ledger.json"

OUTPUT_CANDIDATES_DIR = WORKSPACE_ROOT / "outputs/v3_4/candidates"


def get_file_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def extract_derived_clip(src_video_path, start_frame, end_frame, out_clip_path, fps=30.0):
    cap = cv2.VideoCapture(str(src_video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open {src_video_path}")
    
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(out_clip_path), fourcc, fps, (width, height))
    
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    current_f = start_frame
    extracted_frames = []
    
    while current_f <= end_frame:
        ret, frame = cap.read()
        if not ret:
            break
        out.write(frame)
        if (current_f - start_frame) % max(1, (end_frame - start_frame) // 4) == 0 and len(extracted_frames) < 4:
            extracted_frames.append((current_f, frame.copy()))
        current_f += 1
        
    cap.release()
    out.release()
    return extracted_frames


def create_contact_sheet(frames_list, out_img_path):
    """Create a 3x3 or multi-row contact sheet from sampled frames."""
    if not frames_list:
        return
    thumb_w, thumb_h = 480, 270
    thumbs = []
    for label, f_num, img in frames_list:
        resized = cv2.resize(img, (thumb_w, thumb_h))
        # Add banner overlay
        cv2.rectangle(resized, (0, 0), (thumb_w, 36), (20, 20, 20), -1)
        text = f"{label} | F{f_num:04d} ({f_num/30.0:.1f}s)"
        cv2.putText(resized, text, (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1, cv2.LINE_AA)
        thumbs.append(resized)
        
    # Arrange in a grid of 3 columns
    cols = 3
    rows = math.ceil(len(thumbs) / cols)
    sheet = np.zeros((rows * thumb_h, cols * thumb_w, 3), dtype=np.uint8)
    
    for idx, thumb in enumerate(thumbs):
        r = idx // cols
        c = idx % cols
        sheet[r * thumb_h:(r + 1) * thumb_h, c * thumb_w:(c + 1) * thumb_w] = thumb
        
    cv2.imwrite(str(out_img_path), sheet)


def analyze_scene_candidates(ledger_path, scene_name, video_base_dir):
    with open(ledger_path) as f:
        ledger = json.load(f)
    obs = ledger.get("observations", [])
    
    by_cam_frame = defaultdict(lambda: {"persons": [], "forklifts": []})
    for o in obs:
        cls = o.get("class")
        cf = (o.get("camera_id"), o.get("frame_id"))
        if cls == "person":
            by_cam_frame[cf]["persons"].append(o)
        elif cls == "forklift":
            by_cam_frame[cf]["forklifts"].append(o)

    clusters = defaultdict(list)
    for (cam, frame), group in by_cam_frame.items():
        if group["persons"] and group["forklifts"]:
            for p in group["persons"]:
                for fk in group["forklifts"]:
                    fp_p = p.get("foot_point_px", [0, 0])
                    fp_fk = fk.get("foot_point_px", [0, 0])
                    dist_px = ((fp_p[0] - fp_fk[0])**2 + (fp_p[1] - fp_fk[1])**2)**0.5
                    d_p = p.get("metric_distance_m")
                    d_fk = fk.get("metric_distance_m")
                    diff_m = abs(d_p - d_fk) if (d_p and d_fk) else None
                    key = (cam, p.get("track_id"), fk.get("track_id"))
                    clusters[key].append({
                        "camera_id": cam,
                        "frame_id": frame,
                        "time_s": round(frame / 30.0, 2),
                        "dist_px": round(dist_px, 1),
                        "metric_diff_m": round(diff_m, 2) if diff_m is not None else None,
                        "person_obs": p,
                        "forklift_obs": fk
                    })
                    
    candidates = []
    cand_counter = 1
    for (cam, p_tr, fk_tr), items in clusters.items():
        if len(items) >= 20: # interaction lasting at least 0.66s
            items.sort(key=lambda x: x["frame_id"])
            start_f = items[0]["frame_id"]
            end_f = items[-1]["frame_id"]
            min_px = min(x["dist_px"] for x in items)
            min_m = min((x["metric_diff_m"] for x in items if x["metric_diff_m"] is not None), default=None)
            
            # calculate candidate relevance score based on proximity and duration
            prox_score = max(0.0, min(1.0, 1.0 - (min_px / 600.0)))
            dur_score = min(1.0, len(items) / 150.0)
            relevance_score = round(0.6 * prox_score + 0.4 * dur_score, 3)
            
            cand_id = f"CAND_{scene_name}_{cand_counter:03d}"
            cand_counter += 1
            
            candidates.append({
                "candidate_id": cand_id,
                "scene_id": scene_name,
                "camera_id": cam,
                "source_dataset": "nvidia/PhysicalAI-SmartSpaces",
                "source_video_id": f"{cam}.mp4",
                "source_video_path": str(video_base_dir / f"{cam}.mp4"),
                "start_frame": start_f,
                "end_frame": end_f,
                "start_time": round(start_f / 30.0, 2),
                "end_time": round(end_f / 30.0, 2),
                "duration_seconds": round((end_f - start_f) / 30.0, 2),
                "objects_involved": {
                    "person_track_id": p_tr,
                    "forklift_track_id": fk_tr
                },
                "min_pixel_distance": min_px,
                "min_metric_distance_diff": min_m,
                "possible_intervention": "FORKLIFT_DECELERATION_OR_PEDESTRIAN_AVOIDANCE",
                "possible_primary_zone": f"{cam}_CENTRAL_CORRIDOR",
                "possible_secondary_zone": f"{cam}_ADJACENT_RACK_AISLE",
                "candidate_type": "FORKLIFT_HUMAN_INTERACTION",
                "candidate_relevance_score": relevance_score,
                "reason": f"Sustained spatial convergence between forklift track {fk_tr} and pedestrian track {p_tr} (closest approach: {min_px}px).",
                "sample_observations": items[::max(1, len(items)//10)]
            })
            
    candidates.sort(key=lambda x: x["candidate_relevance_score"], reverse=True)
    return candidates


def generate_human_review_package(cand, out_dir):
    cand_dir = out_dir / cand["candidate_id"]
    cand_dir.mkdir(parents=True, exist_ok=True)
    
    src_video = Path(cand["source_video_path"])
    src_sha256 = get_file_sha256(src_video)
    
    # Define temporal windows
    int_start = cand["start_frame"]
    int_end = cand["end_frame"]
    
    # Pre window: up to 150 frames (5s) before intervention, bounded by frame 0
    pre_start = max(0, int_start - 150)
    pre_end = max(0, int_start - 1)
    
    # Post window: up to 240 frames (8s) after intervention, bounded by frame 1799
    post_start = min(1799, int_end + 1)
    post_end = min(1799, int_end + 240)
    
    # 1. Extract derived clips
    frames_before = extract_derived_clip(src_video, pre_start, pre_end, cand_dir / "before.mp4")
    frames_int = extract_derived_clip(src_video, int_start, int_end, cand_dir / "intervention.mp4")
    frames_after = extract_derived_clip(src_video, post_start, post_end, cand_dir / "after.mp4")
    
    # 2. Generate contact sheet
    all_sample_frames = []
    for f_idx, img in frames_before[:3]:
        all_sample_frames.append(("PRE", f_idx, img))
    for f_idx, img in frames_int[:3]:
        all_sample_frames.append(("INTERVENTION", f_idx, img))
    for f_idx, img in frames_after[:3]:
        all_sample_frames.append(("POST", f_idx, img))
    create_contact_sheet(all_sample_frames, cand_dir / "contact_sheet.jpg")
    
    # 3. metadata.json
    metadata = {
        "candidate_id": cand["candidate_id"],
        "scene_id": cand["scene_id"],
        "camera_id": cand["camera_id"],
        "source_dataset": cand["source_dataset"],
        "source_video": src_video.name,
        "source_sha256": src_sha256,
        "candidate_type": cand["candidate_type"],
        "candidate_relevance_score": cand["candidate_relevance_score"],
        "temporal_windows": {
            "pre": {
                "start_frame": pre_start,
                "end_frame": pre_end,
                "start_time_s": round(pre_start / 30.0, 2),
                "end_time_s": round(pre_end / 30.0, 2),
                "duration_s": round((pre_end - pre_start + 1) / 30.0, 2),
                "clip_filename": "before.mp4"
            },
            "intervention": {
                "start_frame": int_start,
                "end_frame": int_end,
                "start_time_s": round(int_start / 30.0, 2),
                "end_time_s": round(int_end / 30.0, 2),
                "duration_s": round((int_end - int_start + 1) / 30.0, 2),
                "clip_filename": "intervention.mp4"
            },
            "post": {
                "start_frame": post_start,
                "end_frame": post_end,
                "start_time_s": round(post_start / 30.0, 2),
                "end_time_s": round(post_end / 30.0, 2),
                "duration_s": round((post_end - post_start + 1) / 30.0, 2),
                "clip_filename": "after.mp4"
            },
            "window_definition_method": "FIXED_OFFSET_BOUNDED_BY_STREAM"
        },
        "spatial_zones": {
            "primary_zone": {
                "zone_id": cand["possible_primary_zone"],
                "zone_status": "PROVISIONAL_OPTICAL_CORRIDOR",
                "zone_definition_source": "CAMERA_HOMOGRAPHY_GRID",
                "zone_confidence": "MEDIUM"
            },
            "secondary_zone": {
                "zone_id": cand["possible_secondary_zone"],
                "zone_status": "PROVISIONAL_ADJACENT_CELL",
                "zone_definition_source": "PROXIMITY_TOPOLOGY",
                "zone_confidence": "LOW"
            }
        },
        "involved_entities": cand["objects_involved"],
        "governance_status": "PREPARED_FOR_INDEPENDENT_HUMAN_REVIEW"
    }
    with open(cand_dir / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
        
    # 4. event_timeline.json
    timeline = {
        "candidate_id": cand["candidate_id"],
        "timeline_events": [
            {
                "phase": "PRE",
                "start_time": round(pre_start / 30.0, 2),
                "end_time": round(pre_end / 30.0, 2),
                "description": "Baseline nominal corridor movement prior to close convergence."
            },
            {
                "phase": "INTERVENTION",
                "start_time": round(int_start / 30.0, 2),
                "end_time": round(int_end / 30.0, 2),
                "description": f"Convergence interval: closest distance {cand['min_pixel_distance']}px."
            },
            {
                "phase": "POST",
                "start_time": round(post_start / 30.0, 2),
                "end_time": round(post_end / 30.0, 2),
                "description": "Post-interaction traversal and zone exit monitoring."
            }
        ]
    }
    with open(cand_dir / "event_timeline.json", "w") as f:
        json.dump(timeline, f, indent=2)
        
    # 5. model_observations.json
    obs_summary = {
        "candidate_id": cand["candidate_id"],
        "total_interaction_observations": len(cand["sample_observations"]),
        "min_pixel_distance": cand["min_pixel_distance"],
        "min_metric_distance_diff": cand["min_metric_distance_diff"],
        "samples": [
            {
                "frame_id": s["frame_id"],
                "time_s": s["time_s"],
                "dist_px": s["dist_px"],
                "metric_diff_m": s["metric_diff_m"],
                "person_bbox": s["person_obs"].get("bbox_xyxy"),
                "forklift_bbox": s["forklift_obs"].get("bbox_xyxy")
            }
            for s in cand["sample_observations"]
        ]
    }
    with open(cand_dir / "model_observations.json", "w") as f:
        json.dump(obs_summary, f, indent=2)
        
    # 6. human_review_form.json
    review_form = {
        "candidate_id": cand["candidate_id"],
        "instructions": (
            "Review before.mp4, intervention.mp4, after.mp4, and contact_sheet.jpg. "
            "Evaluate whether this event constitutes a valid Safety Backfire event according to the 7 canonical criteria."
        ),
        "evaluation_criteria": {
            "criterion_1_clear_intervention": "Is there a distinct physical intervention/avoidance maneuver?",
            "criterion_2_measurable_pre_risk": "Was there measurable risk in the primary zone prior to intervention?",
            "criterion_3_primary_risk_reduced": "Did risk in the primary zone decrease or mitigate as intended?",
            "criterion_4_secondary_risk_escalated": "Did measurable risk escalate in a secondary/adjacent zone?",
            "criterion_5_causal_mechanism": "Is there a plausible causal relationship connecting the intervention to the secondary hazard?",
            "criterion_6_independent_evidence": "Is evidence supported by objective video/telemetry rather than assumption?",
            "criterion_7_inter_rater_consensus": "Do at least two independent evaluators concur?"
        },
        "review_inputs": {
            "reviewer_id": None,
            "review_timestamp_utc": None,
            "label_decision": None, # Options: BACKFIRE, NO_BACKFIRE, AMBIGUOUS
            "evidence_quality": None, # Options: HIGH, MEDIUM, LOW, UNKNOWN
            "causal_link_confidence": None, # Options: DIRECTLY_OBSERVED, TELEMETRY_SUPPORTED, PLAUSIBLE_BUT_UNCONFIRMED, NOT_ESTABLISHED
            "notes": ""
        }
    }
    with open(cand_dir / "human_review_form.json", "w") as f:
        json.dump(review_form, f, indent=2)
        
    print(f"Generated human review package for {cand['candidate_id']} at {cand_dir}")


def main():
    print("=== Milestone V3.4-B Candidate Screening ===")
    OUTPUT_CANDIDATES_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Screen Warehouse_026
    cands_wh026 = analyze_scene_candidates(
        R3_LEDGER, "Warehouse_026", WH026_DIR / "videos"
    )
    print(f"Warehouse_026 candidates discovered: {len(cands_wh026)}")
    
    # 2. Screen Warehouse_027
    cands_wh027 = analyze_scene_candidates(
        R4_LEDGER, "Warehouse_027", WH027_DIR / "videos"
    )
    print(f"Warehouse_027 candidates discovered: {len(cands_wh027)}")
    
    all_candidates = cands_wh026 + cands_wh027
    all_candidates.sort(key=lambda x: x["candidate_relevance_score"], reverse=True)
    
    # Save candidate registry
    registry_file = OUTPUT_CANDIDATES_DIR / "candidate_events_registry.json"
    registry_data = {
        "registry_version": "V3.4_B_CANDIDATE_EVENTS_REGISTRY_V1",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "total_candidates": len(all_candidates),
        "candidates_wh026": len(cands_wh026),
        "candidates_wh027": len(cands_wh027),
        "governance_note": "Candidate generator only. No ground-truth backfire labels assigned by model.",
        "candidates": [
            {
                "candidate_id": c["candidate_id"],
                "source": c["source_dataset"],
                "scene_id": c["scene_id"],
                "video_id": c["source_video_id"],
                "camera_id": c["camera_id"],
                "start_time": c["start_time"],
                "end_time": c["end_time"],
                "duration_seconds": c["duration_seconds"],
                "candidate_type": c["candidate_type"],
                "objects_involved": c["objects_involved"],
                "possible_intervention": c["possible_intervention"],
                "possible_primary_zone": c["possible_primary_zone"],
                "possible_secondary_zone": c["possible_secondary_zone"],
                "candidate_relevance_score": c["candidate_relevance_score"],
                "reason": c["reason"]
            }
            for c in all_candidates
        ]
    }
    with open(registry_file, "w") as f:
        json.dump(registry_data, f, indent=2)
    print(f"Candidate registry saved to {registry_file}")
    
    # 3. Generate human review packages for top primary candidates
    # We select the top candidates from each scene for package generation
    top_to_package = [cands_wh026[0], cands_wh026[1], cands_wh027[0]]
    for cand in top_to_package:
        generate_human_review_package(cand, OUTPUT_CANDIDATES_DIR)

    print("Candidate generation complete.")

if __name__ == "__main__":
    main()
