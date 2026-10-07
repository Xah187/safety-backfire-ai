"""
create_human_screening_timeline.py
Milestone V3.4-B REV2 — Full Scene Human Screening Infrastructure Generator

GOVERNANCE SPECIFICATION:
  - Generates visual screening timelines for all 11 streams (WH026 + WH027).
  - Two strictly decoupled output suites:
    1. SCREENING_BLIND: Neutral presentation (frame #, timestamp, camera ID only).
       Zero candidate markers, zero AI detection boxes, zero model risk scores.
    2. SCREENING_DEBUG: Includes AI candidate interval markers for audit/comparison.
  - Prohibits modification of raw source videos.
"""

import os
import sys
import json
import math
from pathlib import Path
import cv2
import numpy as np

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent

WH026_VIDEOS = WORKSPACE_ROOT / "data/external_facility/raw/Warehouse_026/MTMC_Tracking_2026/test/Warehouse_026/videos"
WH027_VIDEOS = WORKSPACE_ROOT / "data/external_facility_02/raw/Warehouse_027/MTMC_Tracking_2026/test/Warehouse_027/videos"

REGISTRY_PATH = WORKSPACE_ROOT / "outputs/v3_4/candidates/candidate_events_registry.json"
BASE_OUT_DIR = WORKSPACE_ROOT / "outputs/v3_4/human_screening"

BLIND_DIR = BASE_OUT_DIR / "SCREENING_BLIND"
DEBUG_DIR = BASE_OUT_DIR / "SCREENING_DEBUG"


def load_ai_candidates():
    if not REGISTRY_PATH.exists():
        return {}
    with open(REGISTRY_PATH) as f:
        data = json.load(f)
    by_cam = {}
    for c in data.get("candidates", []):
        key = (c["scene_id"], c["camera_id"])
        if key not in by_cam:
            by_cam[key] = []
        by_cam[key].append(c)
    return by_cam


def generate_stream_timeline(video_path, scene_name, cam_name, ai_cands):
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print(f"Error opening {video_path}")
        return
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    duration_s = total_frames / fps
    
    # Sample 1 frame every 2 seconds (30 panels across 60 seconds)
    sample_interval = int(round(fps * 2.0))
    sample_frame_indices = [i for i in range(0, total_frames, sample_interval)]
    if len(sample_frame_indices) > 30:
        sample_frame_indices = sample_frame_indices[:30]
        
    blind_panels = []
    debug_panels = []
    
    thumb_w, thumb_h = 320, 180
    
    for f_idx in sample_frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, f_idx)
        ret, frame = cap.read()
        if not ret:
            break
        
        resized = cv2.resize(frame, (thumb_w, thumb_h))
        time_s = f_idx / fps
        
        # 1. BLIND Panel
        b_panel = resized.copy()
        cv2.rectangle(b_panel, (0, 0), (thumb_w, 28), (20, 20, 20), -1)
        text_blind = f"{cam_name} | F{f_idx:04d} ({time_s:04.1f}s)"
        cv2.putText(b_panel, text_blind, (8, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
        blind_panels.append(b_panel)
        
        # 2. DEBUG Panel
        d_panel = resized.copy()
        # Check if f_idx falls within any AI candidate interval
        active_cands = [
            c for c in ai_cands 
            if int(round(c["start_time"] * fps)) <= f_idx <= int(round(c["end_time"] * fps))
        ]
        
        if active_cands:
            # Highlight with yellow/red banner
            cv2.rectangle(d_panel, (0, 0), (thumb_w, thumb_h), (0, 165, 255), 2)
            cv2.rectangle(d_panel, (0, 0), (thumb_w, 28), (0, 60, 180), -1)
            text_debug = f"AI CAND ({len(active_cands)}) | F{f_idx:04d} ({time_s:04.1f}s)"
            cv2.putText(d_panel, text_debug, (8, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
        else:
            cv2.rectangle(d_panel, (0, 0), (thumb_w, 28), (20, 20, 20), -1)
            text_debug = f"{cam_name} | F{f_idx:04d} ({time_s:04.1f}s)"
            cv2.putText(d_panel, text_debug, (8, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1, cv2.LINE_AA)
        debug_panels.append(d_panel)
        
    cap.release()
    
    # Assemble into grid (5 columns x 6 rows = 30 panels)
    cols = 5
    rows = math.ceil(len(blind_panels) / cols)
    
    blind_grid = np.zeros((rows * thumb_h, cols * thumb_w, 3), dtype=np.uint8)
    debug_grid = np.zeros((rows * thumb_h, cols * thumb_w, 3), dtype=np.uint8)
    
    for idx, (bp, dp) in enumerate(zip(blind_panels, debug_panels)):
        r = idx // cols
        c = idx % cols
        blind_grid[r * thumb_h:(r + 1) * thumb_h, c * thumb_w:(c + 1) * thumb_w] = bp
        debug_grid[r * thumb_h:(r + 1) * thumb_h, c * thumb_w:(c + 1) * thumb_w] = dp
        
    # Paths
    cam_blind_dir = BLIND_DIR / scene_name / cam_name
    cam_debug_dir = DEBUG_DIR / scene_name / cam_name
    cam_blind_dir.mkdir(parents=True, exist_ok=True)
    cam_debug_dir.mkdir(parents=True, exist_ok=True)
    
    cv2.imwrite(str(cam_blind_dir / "timeline_contact_sheet.jpg"), blind_grid)
    cv2.imwrite(str(cam_debug_dir / "timeline_contact_sheet_debug.jpg"), debug_grid)
    
    # Blind card
    blind_card = {
        "scene_id": scene_name,
        "camera_id": cam_name,
        "stream_duration_seconds": round(duration_s, 2),
        "total_frames": total_frames,
        "fps": fps,
        "protocol": "BLINDED_HUMAN_SCREENING",
        "instructions": (
            "Review this 60s stream independently. Identify any safety interventions, "
            "abrupt braking, worker evasions, or cross-corridor hazards. "
            "Record findings in human_event_screening.schema.json format without referencing model outputs."
        )
    }
    with open(cam_blind_dir / "stream_screening_card.json", "w") as f:
        json.dump(blind_card, f, indent=2)
        
    # Debug card
    debug_card = {
        "scene_id": scene_name,
        "camera_id": cam_name,
        "stream_duration_seconds": round(duration_s, 2),
        "total_frames": total_frames,
        "fps": fps,
        "protocol": "DEBUG_AUDIT_TIMELINE",
        "ai_candidate_count": len(ai_cands),
        "ai_candidates": [
            {
                "candidate_id": c["candidate_id"],
                "start_time": c["start_time"],
                "end_time": c["end_time"],
                "duration_seconds": c["duration_seconds"],
                "relevance_score": c["candidate_relevance_score"]
            }
            for c in ai_cands
        ]
    }
    with open(cam_debug_dir / "stream_debug_card.json", "w") as f:
        json.dump(debug_card, f, indent=2)


def main():
    print("=== Creating Full Scene Human Screening Infrastructure ===")
    ai_candidates = load_ai_candidates()
    
    # 1. Warehouse_026 (4 cameras)
    wh026_cams = [f"Camera_{i:04d}" for i in range(4)]
    for cam in wh026_cams:
        v_path = WH026_VIDEOS / f"{cam}.mp4"
        cands = ai_candidates.get(("Warehouse_026", cam), [])
        print(f"Processing Warehouse_026 {cam} ({len(cands)} AI candidates)...")
        generate_stream_timeline(v_path, "Warehouse_026", cam, cands)
        
    # 2. Warehouse_027 (7 cameras)
    wh027_cams = [f"Camera_{i:04d}" for i in range(7)]
    for cam in wh027_cams:
        v_path = WH027_VIDEOS / f"{cam}.mp4"
        cands = ai_candidates.get(("Warehouse_027", cam), [])
        print(f"Processing Warehouse_027 {cam} ({len(cands)} AI candidates)...")
        generate_stream_timeline(v_path, "Warehouse_027", cam, cands)
        
    print(f"Full Scene Screening Timelines successfully generated for all 11 streams.")
    print(f"  BLIND directory: {BLIND_DIR}")
    print(f"  DEBUG directory: {DEBUG_DIR}")

if __name__ == "__main__":
    main()
