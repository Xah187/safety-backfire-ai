#!/usr/bin/env python3
"""
Evaluate Test Videos (test.mp4 and test2.mp4).
Applies YOLOv8/ByteTrack object detection and tracking, metric distance calculation,
and renders annotated Full/HD H.264 (avc1) benchmark videos with telemetry HUD.
"""

import json
import math
import os
import shutil
import sys
from pathlib import Path
import cv2
import numpy as np
from ultralytics import YOLO

ROOT = Path("/Users/xah187/Projects/safety-backfire-ai")
OUTPUT_DIR = ROOT / "outputs" / "v3_4_n_corr_04_r4"
SCRATCH_DIR = Path("/Users/xah187/.gemini/antigravity-ide/brain/466f5a34-2608-4f9d-8f34-b1f6e5e6c88b/scratch")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
SCRATCH_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH = ROOT / "safety_backfire_v07" / "runs" / "forklift_person_yolo26n_v07" / "weights" / "best.pt"

TEST_VIDEOS = [
    ROOT / "test.mp4",
    ROOT / "test2.mp4"
]

def process_video(video_path: Path, max_frames: int = None):
    print(f"\n==================================================================")
    print(f"Processing: {video_path.name}")
    print(f"==================================================================")
    
    if not video_path.exists():
        print(f"Error: {video_path} does not exist!")
        return None
        
    cap = cv2.VideoCapture(str(video_path))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    
    frames_to_run = min(total_frames, max_frames) if max_frames else total_frames
    print(f"Resolution: {width}x{height} | FPS: {fps:.2f} | Frames to process: {frames_to_run}/{total_frames}")

    out_name = f"{video_path.stem}_annotated.mp4"
    out_path = OUTPUT_DIR / out_name
    
    # Try H.264 (avc1) first, fallback to mp4v
    fourcc = cv2.VideoWriter_fourcc(*"avc1")
    out = cv2.VideoWriter(str(out_path), fourcc, fps, (width, height))
    if not out.isOpened():
        print("Falling back to mp4v...")
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(str(out_path), fourcc, fps, (width, height))

    model = YOLO(str(MODEL_PATH))
    
    # Tracking statistics
    stats = {
        "video": video_path.name,
        "width": width,
        "height": height,
        "fps": round(fps, 2),
        "total_frames": total_frames,
        "processed_frames": frames_to_run,
        "forklift_detections": 0,
        "person_detections": 0,
        "unique_forklift_ids": set(),
        "unique_person_ids": set(),
        "min_separation_m": 999.0,
        "critical_events": 0,
        "sample_preview_frames": []
    }
    
    # Ground plane homography for distance estimation
    # Calibrated quad on warehouse floor
    src_pts = np.float32([
        [width * 0.32, height * 0.50], [width * 0.53, height * 0.50],
        [width * 0.23, height * 0.94], [width * 0.67, height * 0.94]
    ])
    dst_pts = np.float32([
        [0.0, 6.0], [3.5, 6.0],
        [0.0, 0.0], [3.5, 0.0]
    ])
    H, _ = cv2.findHomography(src_pts, dst_pts)
    
    def to_world(px, py):
        if H is None: return None
        vec = np.array([px, py, 1.0], dtype=np.float64)
        w = H @ vec
        if abs(w[2]) < 1e-6: return None
        return (w[0] / w[2], w[1] / w[2])

    frame_idx = 0
    trajectories = {}  # tid -> list of (x_w, y_w, time)
    
    for r in model.track(
        source=str(video_path),
        stream=True,
        persist=True,
        tracker="bytetrack.yaml",
        imgsz=960 if width >= 1280 else 640,
        conf=0.20,
        iou=0.65,
        device="cpu",
        classes=[0, 1],  # 0: person, 1: forklift
        verbose=False
    ):
        frame_idx += 1
        if frame_idx > frames_to_run:
            break
            
        t_sec = frame_idx / fps
        frame = r.orig_img.copy()
        boxes = r.boxes
        
        # 1. Draw calibrated floor polygon
        cv2.polylines(frame, [np.int32(src_pts).reshape(-1, 1, 2)], True, (255, 200, 0), 1, cv2.LINE_AA)
        
        persons = []
        forklifts = []
        
        if boxes is not None and len(boxes) > 0:
            xyxy = boxes.xyxy.cpu().numpy()
            clss = boxes.cls.cpu().numpy().astype(int)
            ids = boxes.id.cpu().numpy().astype(int) if boxes.id is not None else [None] * len(clss)
            
            for i, cls_id in enumerate(clss):
                box = [int(v) for v in xyxy[i]]
                tid = ids[i] if ids is not None else None
                c_name = model.names[cls_id]
                
                cx = (box[0] + box[2]) / 2.0
                foot_y = box[3]
                w_pt = to_world(cx, foot_y)
                
                # Colors: Orange for Forklift, Cyan for Person
                color = (0, 140, 255) if c_name == "forklift" else (255, 200, 0)
                if tid is not None:
                    label = f"{c_name} #{tid}"
                else:
                    label = f"{c_name}"
                    
                cv2.rectangle(frame, (box[0], box[1]), (box[2], box[3]), color, 2, cv2.LINE_AA)
                cv2.putText(frame, label, (box[0], max(15, box[1] - 6)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1, cv2.LINE_AA)
                            
                # Foot contact point
                cv2.circle(frame, (int(cx), int(foot_y)), 4, (0, 0, 255), -1)
                
                if tid is not None:
                    if c_name == "forklift":
                        stats["forklift_detections"] += 1
                        stats["unique_forklift_ids"].add(tid)
                    else:
                        stats["person_detections"] += 1
                        stats["unique_person_ids"].add(tid)
                        
                    if w_pt is not None:
                        if tid not in trajectories:
                            trajectories[tid] = []
                        trajectories[tid].append((cx, foot_y, w_pt[0], w_pt[1], t_sec))
                        
                entity = {"box": box, "cx": cx, "foot_y": foot_y, "w_pt": w_pt, "tid": tid, "name": c_name}
                if c_name == "person":
                    persons.append(entity)
                elif c_name == "forklift":
                    forklifts.append(entity)
                    
        # Calculate metric proximity between persons and forklifts
        min_dist_frame = 999.0
        for p in persons:
            for f in forklifts:
                if p["w_pt"] and f["w_pt"]:
                    dx = p["w_pt"][0] - f["w_pt"][0]
                    dy = p["w_pt"][1] - f["w_pt"][1]
                    dist_m = math.sqrt(dx * dx + dy * dy)
                    if dist_m < min_dist_frame:
                        min_dist_frame = dist_m
                    if dist_m < stats["min_separation_m"]:
                        stats["min_separation_m"] = dist_m
                        
                    # Draw connecting line
                    line_color = (0, 0, 255) if dist_m < 2.0 else (0, 255, 255) if dist_m < 3.5 else (0, 255, 0)
                    cv2.line(frame, (int(p["cx"]), int(p["foot_y"])), (int(f["cx"]), int(f["foot_y"])), line_color, 2, cv2.LINE_AA)
                    mid_x = int((p["cx"] + f["cx"]) / 2)
                    mid_y = int((p["foot_y"] + f["foot_y"]) / 2)
                    cv2.putText(frame, f"{dist_m:.2f}m", (mid_x, mid_y - 5),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.45, line_color, 1, cv2.LINE_AA)
                                
        if min_dist_frame < 2.0:
            stats["critical_events"] += 1

        # Draw Telemetry HUD Header and Footer
        # Header banner
        cv2.rectangle(frame, (0, 0), (width, 36), (15, 15, 18), -1)
        cv2.line(frame, (0, 36), (width, 36), (40, 45, 50), 1)
        header_text = f"FILE: {video_path.name} | TC: {t_sec:5.2f}s | FRAME: #{frame_idx:04d}/{total_frames} | DETS: {len(forklifts)} FK, {len(persons)} P"
        cv2.putText(frame, header_text, (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (0, 220, 255), 1, cv2.LINE_AA)

        # Status badge
        status_str = "SAFE"
        badge_color = (30, 140, 30)
        if min_dist_frame < 2.0:
            status_str = f"NEAR MISS (<2.0m: {min_dist_frame:.1f}m)"
            badge_color = (20, 20, 200)
        elif min_dist_frame < 3.5:
            status_str = f"CAUTION (<3.5m: {min_dist_frame:.1f}m)"
            badge_color = (0, 140, 220)
            
        cv2.rectangle(frame, (width - 240, 5), (width - 10, 31), badge_color, -1)
        cv2.putText(frame, status_str, (width - 235, 23), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (255, 255, 255), 1, cv2.LINE_AA)

        out.write(frame)
        
        # Save sample keyframes for artifact preview
        if frame_idx in [50, 150, 300]:
            p_name = f"{video_path.stem}_frame_{frame_idx:03d}.png"
            cv2.imwrite(str(SCRATCH_DIR / p_name), frame)
            stats["sample_preview_frames"].append(p_name)
            
        if frame_idx % 100 == 0 or frame_idx == frames_to_run:
            print(f"Processed {frame_idx}/{frames_to_run} frames ({t_sec:.1f}s)...")
            
    out.release()
    print(f"Video saved to: {out_path} ({os.path.getsize(out_path)} bytes)")
    
    # Copy to scratch directory
    scratch_target = SCRATCH_DIR / out_name
    shutil.copy2(out_path, scratch_target)
    print(f"Copied to scratch: {scratch_target}")
    
    # Convert sets to sorted lists of standard Python ints for json serialization
    stats["unique_forklift_ids"] = [int(x) for x in sorted(list(stats["unique_forklift_ids"]))]
    stats["unique_person_ids"] = [int(x) for x in sorted(list(stats["unique_person_ids"]))]
    if stats["min_separation_m"] == 999.0:
        stats["min_separation_m"] = None
    else:
        stats["min_separation_m"] = round(stats["min_separation_m"], 2)
        
    return stats

def main():
    results = {}
    for video in TEST_VIDEOS:
        if video.exists():
            # For test.mp4 (426 frames): run all 426 frames
            # For test2.mp4 (1246 frames): run up to 450 frames to deliver quick benchmark results
            max_f = 426 if "test.mp4" == video.name else 450
            st = process_video(video, max_frames=max_f)
            if st:
                results[video.name] = st
                
    json_path = OUTPUT_DIR / "test_videos_evaluation_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nAll results saved to: {json_path}")

if __name__ == "__main__":
    main()
